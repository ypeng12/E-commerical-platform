from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first())
        item['sku'] = json_data['sku']
        item['tmp'] = json_data

    def _name(self, res, item, **kwargs):
        data = item['tmp']
        if ' - ' in data['name']:
            item['name'] = data['name'].split(' - ')[1]
        else:
            item['name'] = data['name']
        item['designer'] = data['brand']['name'].upper()
        item['description'] = data['description']
        item['color'] = ''

    def _images(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        image_li = []
        for image in json_data['images']:
            if "https:" not in image:
                image_li.append("https:" + image)
        item["images"] = image_li
        item['cover'] = 'https:' + json_data['featured_image']

    def _prices(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item["originsaleprice"] = str(json_data['price'])[:-2] + '.' + str(json_data['price'])[-2:]
        item["originlistprice"] = str(json_data['price_max'])[:-2] + '.' + str(json_data['price_max'])[-2:]

    def _sizes(self,res,item,**kwargs):
        item["originsizes"] = ['IT']

    def _parse_images(self, response, **kwargs):
        images = response.xpath("//button[@class='product-gallery-nav__item']/img/@src").extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return images_li

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

_parser = Parser()

class Config(MerchantConfig):
    name = "navyhaircare"
    merchant = "Navy Haircare"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//li[@class="pagination-number"]/a/text()',
            list_url = _parser.list_url,
            items = '//div[@class="grid-view-item"]/div',
            designer = './/a/img/@id',
            link = './/a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[@id="AddToCart"]/span',_parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('name', ('//html', _parser.name)),
            ('images', ('//script[contains(@id,"ProductJson")][@type="application/json"]/text()', _parser.images)),
            ('price', ('//script[contains(@id,"ProductJson")][@type="application/json"]/text()', _parser.prices)),
            ('sizes', ('//html', _parser.sizes)),
        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
        ),
    )

    list_urls = dict(
        f = dict(
            e = [
                'https://www.navyhaircare.com/collections/all?page={}'
            ],
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )