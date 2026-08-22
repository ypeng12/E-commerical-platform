from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        json_datas = json.loads(checkout.extract_first().split('var dataLayerV2Json = ')[1].split('var dataLayer =')[0].rsplit(';',1)[0])
        item['tmp'] = json_datas
        if json_datas['ecommerce']['detail']['availability']:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = data.split('of ')[-1].strip()
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        data = item['tmp']['ecommerce']['detail']['products'][0]
        item['sku'] = data['id'] + '_' + data['colorId']

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first().split(' - ')[0].upper()
        item['designer'] = item['tmp']['page']['brand'].upper()
        item['description'] = item['tmp']['ecommerce']['detail']['products'][0]['description']
        item['color'] = ''
          
    def _images(self, images, item, **kwargs):
        datas = item['tmp']['ecommerce']['detail']['products'][0]['photos']
        images = []
        for img in datas.values():
            if img not in images and item['sku'] in img:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, orisizes, item, **kwargs):
        size_li = []
        for osize in item['tmp']['ecommerce']['detail']['products'][0]['sizeAvailability'].split(','):
            if osize:
                size_li.append(osize)

        item['originsizes'] = size_li

        if item['category'] in ['a','b','e'] and not item['originsizes']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        data =  item['tmp']['ecommerce']['detail']['products'][0]
        listprice = str(data['salePrice'])
        saleprice = str(data['originalPrice'])
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _parse_images(self, response, **kwargs):
        json_datas = response.xpath('//script[contains(text(),"dataLayerV2Json")]/text()').extract_first()
        datas = json.loads(json_datas.split('var dataLayerV2Json = ')[1].split('var dataLayer =')[0].rsplit(';',1)[0])
        img_li = []
        images = datas['ecommerce']['detail']['products'][0]['photos']
        for img in images.values():
            img_li.append(img)
        return img_li

_parser = Parser()


class Config(MerchantConfig):
    name = 'mango'
    merchant = "Mango"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pages"]/div/span/text()',_parser.page_num),
            items = '//ol[@class="products list items product-items"]/li/div',
            designer = './/p[@class="brand"]/a/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[contains(text(),"dataLayerV2Json")]/text()', _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('name', ('//meta[@property="og:title"]/@content', _parser.name)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        checknum = dict(
            ),
        )

    list_urls = dict(
        m = dict(
        ),
        f = dict(
            a = [
                '',
            ],
            b = [
                '',
            ],
            c = [
                '',
            ],
            s = [
            ],
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = 'shop.mango.com/us/'
        ),
        GB = dict(
            country_url = 'shop.mango.com/gb/'
        )

        )
        


