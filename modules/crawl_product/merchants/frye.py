from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract_first()
        if 'InStock' not in checkout:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        json_data = res.extract_first()
        datas = json.loads(json_data.split('var meta =')[1].split('for (var attr in meta)')[0].rsplit(';',1)[0])
        sku = datas['product']['variants'][0]['sku'].split('-')[0]
        color = datas['product']['variants'][0]['public_title'].split(' / ')[0].strip()
        if color == 'N':
            item['sku'] = ''
        else:
            item['sku'] = sku + '_' + color.upper()
            item['designer'] = datas['product']['vendor']

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first().strip()

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./span[@class="list_price"]/text()').extract_first()
        saleprice = prices.xpath('./span[@class="price"]/text()').extract_first()
        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _images(self, res, item, **kwargs):
        images_li = []
        images_data = res.extract()
        for img in images_data:
            img = "https:" + img
            if img not in images_li:
                images_li.append(img)

        item['images'] = images_li
        item['cover'] = images_li[0]

    def _sizes(self, res, item, **kwargs):
        size_li = []
        for size in res:
            if "instock" in size.xpath('./span[@class="availability"]').extract_first().lower():
                availsize = size.xpath('./span[@class="custom_fields"]/span[@class="Size"]/text()').extract_first()
                size_li.append(availsize)
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        images = response.xpath("//button[@class='product-gallery-nav__item']/img/@src").extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return images_li

    def _list_url(self, i, response_url, **kwargs):
        return response_url

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
    name = "frye"
    merchant = "Frye"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a[@class="last"]/text()',
            list_url = _parser.list_url,
            items = '//article',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//div[@class="nosto_product"]/span[@class="availability"]/text()',_parser.checkout)),
            ('sku', ('//script[contains(text(),"window.ShopifyAnalytics = window.ShopifyAnalytics")]/text()', _parser.sku)),
            ('name', '//div[@class="nosto_product"]/span[@class="name"]/text()'),
            ('color','//div[@class="nosto_product"]/span[@class="nosto_sku"]/span[@class="custom_fields"]/span[@class="Color"]/text()'),
            ('description',('//meta[@name="description"]/@content', _parser.description)),
            ('price', ('//div[@class="nosto_product"]', _parser.prices)),
            ('images', ('//div[@class="nosto_product"]/span[@class="alternate_image_url"]/text()', _parser.images)),
            ('sizes', ('//div[@class="nosto_product"]/span[@class="nosto_sku"]', _parser.sizes)),
        ]),
        image=dict(
            image_path = '//div[@class="nosto_product"]/span[@class="alternate_image_url"]/text()',
            replace = ("cdn.shopify.com/","https://cdn.shopify.com/"),
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
            ],
            c = [
            ],
            s = [
            ]
        ),
        m = dict(
            a = [
            ],
            c = [
            ],
            s = [
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )