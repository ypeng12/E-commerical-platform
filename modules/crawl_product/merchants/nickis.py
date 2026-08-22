from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        data = json.loads(checkout.extract_first())
        item['tmp'] = data
        if checkout:
            return False
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = item['tmp']['articleNumber']
        item['name'] = item['tmp']['title']
        item['designer'] = item['tmp']['brand']['title']
        item['color'] = item['tmp']['colors'][0].upper()
        item['url'] = 'https://www.nickis.com/en/product/' + item['sku']
          
    def _images(self, images, item, **kwargs):
        images = []

        for img in item['tmp']['images']:
            image = img['medium']
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _color(self, data, item, **kwargs):
        try:
            title = data.extract()
            item['color'] = title[0].split(',')[-1].strip().upper()
        except:
            item['color'] =  item['name'].split(' ')[-1].upper()

    def _description(self, description, item, **kwargs):
        descs = item['tmp']['detailAttributes']
        desc_li = []
        for desc in descs:
            desc_li.append(desc['value'])
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        osizes = item['tmp']['variants']
        item['originsizes'] = []
        for osize in osizes:
            if not osize['stock']:
                continue
            item['originsizes'].append(osize['displaySize'].replace(',','.'))

        if item['category'] in ['a','b'] and not item['originsizes']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        saleprice = item['tmp']['localPrice']
        listprice = item['tmp']['localOldPrice']

        item['originsaleprice'] = str(saleprice)
        item['originlistprice'] = str(listprice) if listprice else str(saleprice)

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.body)
        images = []

        for img in data['images']:
            image = img['medium']
            images.append(image)
        return images


_parser = Parser()



class Config(MerchantConfig):
    name = 'nickis'
    merchant = 'NICKIS.com'

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = '//span[@class="current"]/text()',
            list_url = _parser.list_url,
            items = '//ul[@data-context]/li',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './/a[@class="thumb-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//p/text()', _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('images', ('//html', _parser.images)),
            ('description', ('//html',_parser.description)),
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
        )

    list_urls = dict(
        g = dict(
        ),
        b = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),

    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/us/en/',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/uk/en/',
            currency_sign = '\xa3',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/de/de/',
            currency_sign = '\u20ac',
        )

        )
        


