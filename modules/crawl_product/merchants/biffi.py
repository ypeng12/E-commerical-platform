from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        data = checkout.extract_first()
        if data:
            item['tmp'] = json.load(data)
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_json = data.extract_first()
        page_num = num_json.split('of')[1].strip()
        return _page_num//24

    def _list_url(self, i, response_url, **kwargs):
        return response_url.replace('?p=','?p={}'.format(i))

    def _sku(self,res,item,**kwargs):
        item['sku'] = item['tmp']['sku']
        item['designer'] = item['tmp']['brand'].upper()
        item['description'] = item['tmp']['description']
        item['name'] = item['tmp']['name'].upper()
        item['color'] = ''

    def _images(self, res, item, **kwargs):
        images_data = json.loads(res.extract_first())
        image_li = []
        for image_code in images_data['*']['Magento_Catalog/js/product/view/provider']['data']['items']:
            for image in images_data['*']['Magento_Catalog/js/product/view/provider']['data']['items'][image_code]['images']:
                if image['url'] not in image_li:
                    image_li.append(image['url'])
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./span[@class="normal-price"]//span[@class="price"]/text()').extract_first()
        saleprice = prices.xpath('.//span[@data-price-type="oldPrice"]/span/text()').extract_first()
        if saleprice is not None:
            item["originsaleprice"] = saleprice.strip()
        else:
            item["originsaleprice"] = listprice
        item["originlistprice"] = listprice

    def _sizes(self,res,item,**kwargs):
        size_data = json.loads(res.extract_first())
        size_li = []
        for size in  size_data['#product_addtocart_form']['configurable']['spConfig']['attributes']['208']['options']:
            if size['in_stock'] != 0:
                size_li.append(size['tmp_simple_value'])
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        images_data = json.loads(response.xpath('//script[contains(text(),"Magento_Catalog/js/product/view/provider")]/text()').extract_first())
        image_li = []
        for image_code in images_data['*']['Magento_Catalog/js/product/view/provider']['data']['items']:
            for image in images_data['*']['Magento_Catalog/js/product/view/provider']['data']['items'][image_code]['images']:
                if image['url'] not in image_li:
                    image_li.append(image['url'])
        return image_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "biffi"
    merchant = "Biffi Boutique"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="toolbar-amount"]',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product details product-item-details"]',
            designer = './/div[@class="brand"]/text()',
            link = './/div[@ class="slider-product-name"]/a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//script[@type="application/ld+json"]/text()',_parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('price', ('//div[@class="wrap-price"]/div[@data-role="priceBox"]', _parser.prices)),
            ('images', ('//script[contains(text(),"Magento_Catalog/js/product/view/provider")]/text()', _parser.images)),
            ('sizes', ('//script[@type="text/x-magento-init"][contains(text(),"#product_addtocart_form")]/text()', _parser.sizes)),
        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="care"]/div[@class="accordion-body"]/p/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.biffi.com/us_en/women/accessories?p='
            ],
            b = [
                'https://www.biffi.com/us_en/women/bags?p='
            ],
            c = [
                'https://www.biffi.com/us_en/women/clothing?p=',
            ],
            s = [
                'https://www.biffi.com/us_en/women/footwear?p='
            ]
        ),
        m = dict(
            a = [
                'https://www.biffi.com/us_en/men/accessories?p='
            ],
            b = [
                'https://www.biffi.com/us_en/men/bags?p='
            ],
            c = [
                'https://www.biffi.com/us_en/men/clothing?p=',
            ],
            s = [
                'https://www.biffi.com/us_en/men/footwear?p='
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )