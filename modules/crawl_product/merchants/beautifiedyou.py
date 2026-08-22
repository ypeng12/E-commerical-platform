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
        data = json.loads(res.extract_first().split('analytics.track(\'Product Viewed\',')[1].rsplit(');',1)[0].strip())
        item['sku'] = data['sku']
        item['name'] = data['name']

    def _images(self, res, item, **kwargs):
        images = res.extract()
        images_li = []
        for image in images:
            if image not in images_li:
                images_li.append(image)
        item['images'] = images_li
        item['cover'] = images_li[0]

    def _prices(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first().split('var BCData = ')[1].rsplit(';',1)[0])
        item["originlistprice"] = json_data['product_attributes']['price']['without_tax']['formatted']
        item["originsaleprice"] = json_data['product_attributes']['price']['without_tax']['formatted']

    def _sizes(self,res,item,**kwargs):
        item["originsizes"] = ['IT']

    def _parse_images(self, response, **kwargs):
        images = json.loads(response.xpath('//div[@class="row"]/section/div[@class="pr_main"]/figure[@class="productView-image"]/a/img/@src').extract_first())
        images_li = []
        for image in images:
            if image not in images_li:
                images_li.append(image)

        return images_li

_parser = Parser()

class Config(MerchantConfig):
    name = "beautifiedyou"
    merchant = "BeautifiedYou"

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="prod-image"]',
            designer = './a/img/@title',
            link = './a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//input[@id="form-action-addToCart"]',_parser.checkout)),
            ('sku', ('//script[@type="text/javascript"][contains(text(),"analytics.track(\'Product Viewed")]/text()', _parser.sku)),
            ('designer', '//div[@class="productView-product"]/h2/a/span/text()'),
            ('color', ('//span[@class="form-option-text"]/text()')),
            ('description', '//div[@class="tabs-contents"]/div[@id="tab-description"]/p/text()'),
            ('images', ('//div[@class="row"]/section/div[@class="pr_main"]/figure[@class="productView-image"]/a/img/@src', _parser.images)),
            ('price', ('//script[contains(text(),"var BCData")]/text()', _parser.prices)),
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
                'https://www.beautifiedyou.com/beauty-blender/blender-care/'
            ],
        ),
        m = dict(
            e = [
                'https://www.beautifiedyou.com/jack-black-body-care/'
            ],
        ),

    )

    countries = dict(
        US=dict(
            currency='USD',
        ),
    )