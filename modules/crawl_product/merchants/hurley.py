from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from urllib.parse import urljoin
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "InStock" in checkout.extract_first():
            return False
        else:
            return True

    def _sku(self,res,item,**kwargs):
        data = json.loads(res.extract_first().split('var __st=')[1].rsplit(';',1)[0])
        item['sku'] = data['rid']

    def _description(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first().split('BISConfig.product = ')[1].split('_BISConfig.product')[0].rsplit(';',1)[0])
        item['tmp'] = json_data
        item['description'] = json_data['description'].split('<!-- split:Features -->')[0]

    def _images(self, res, item, **kwargs):
        json_data = item['tmp']
        images_li = []
        for image in json_data['images']:
            image = "https:" + image
            if image not in images_li and "sw.jpg" not in image:
                images_li.append(image)
        item['images'] = images_li
        item['cover'] = images_li[0]

    def _prices(self, res, item, **kwargs):
        saleprice = res.xpath('./span[@class="price"]/text()').extract_first()
        listprice = res.xpath('/span[@class="list_price"]/text()').extract_first()
        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _sizes(self,res,item,**kwargs):
        memo = ""
        if "final_sale" in item['tmp']['tags']:
            memo = ':f'
        size_li = []
        for size in item['tmp']['variants']:
            if size['available']:
                size_li.append(size['option2'] + memo)
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//meta[@property="og:image:secure_url"]/@content').extract()
        images_li = []
        for image in images:
            images_li.appen(image)
        return images_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

    def _page_num(self, data, **kwargs):
        return 1

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

    def _parse_item_url(self, response, **kwargs):
        json_data = response.xpath('//script[contains(text(),"window.ShopifyAnalytics = window.ShopifyAnalytics")]/text()').extract_first()
        datas = json.loads(json_data.split('var meta = ')[1].split('for (var attr in meta) ')[0].rsplit(';',1)[0])
        for prd in datas['products']:
            name = prd['variants'][0]['name'].split(' / ')[0]
            pid = name.lower().replace(' - ','-').replace(' ','-')
            # url = urljoin(response.url,pid)
            url = response.url.split('?')[0] + '/products/' + pid
            designer = prd['vendor']
            yield url, designer

_parser = Parser()

class Config(MerchantConfig):
    name = "hurley"
    merchant = "Hurley"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination"]/ul/li/a/text()', _parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            ),
        product=OrderedDict([
            ('checkout',('//span[@class="availability"]/text()',_parser.checkout)),
            ('sku', ('//script[contains(text(),"var __st=")]/text()', _parser.sku)),
            ('name', '//div[@id="ProductContainer"]//h1[@id="ProductTitle"]/text()'),
            ('color', '//span[@class="nosto_sku"]/span[@class="custom_fields"]/span[@class="Color"]/text()'),
            ('designer', '//span[@class="brand"]/text()'),
            ('description', ('//script[@id="back-in-stock-helper"]/text()', _parser.description)),
            ('images', ('//script[@id="back-in-stock-helper"]/text()', _parser.images)),
            ('price', ('//span[@class="nosto_sku"]', _parser.prices)),
            ('sizes', ('//div[@class="productView-option-size"]/div[@data-product-attribute="set-select"]', _parser.sizes)),
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
            size_info_path = '//div[@class="nosto_product"]/span[@class="description"]/ul/li/text()',
            ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.hurley.com/collections/womens-accessories?page={}',
            ],
            c = [
                'https://www.hurley.com/collections/mens-clothing?page={}',
                'https://www.hurley.com/collections/womens-swim?page={}',
            ]
        ),
        m = dict(
            a = [
                'https://www.hurley.com/collections/womens-accessories?page={}'
            ],
            c = [
                'https://www.hurley.com/collections/mens-boardshorts?page={}',
                'https://www.hurley.com/collections/mens-clothing?page={}',
            ],
        ),

    )

    countries = dict(
        US=dict(
            currency='USD',
        ),
    )