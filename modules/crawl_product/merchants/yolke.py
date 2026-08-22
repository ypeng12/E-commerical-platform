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
    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract()[0].split('__st=')[-1][:-1].strip())
        item['sku'] = str(data['rid'])
          
    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                images.append(urljoin('https:', img))
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        item['designer'] = 'YOLKE'
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        if item['category'] in ['c','s']:
            sizes = sizes_data.xpath('./option[not(@disabled)]/text()').extract()
            for size in sizes:
                item['originsizes'].append(size.strip())

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        price = prices.xpath('./span[@class="money"]/text()').extract()
        item['originsaleprice'] = price[0] if price else ''
        item['originlistprice'] = price[0] if price else ''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//ul[@class="images"]/li/a/@href').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                images.append(urljoin('https:', img))
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'yolke'
    merchant = 'Yolke'

    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = '//ul[@class="products"]/li',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@value="Add to basket"]', _parser.checkout)),
            ('sku', ('//script[@id="__st"]/text()',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('images', ('//ul[@class="images"]/li/a/@href', _parser.images)),
            ('color','//div[@class="information"]//h3/text()'),
            ('description', ('//meta[@name="description"]/@content',_parser.description)),
            ('sizes', ('//div[@class="variants"]/select', _parser.sizes)),
            ('prices', ('//h2[@itemprop="price"]', _parser.prices))
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
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
                'https://www.yolke.co.uk/collections/accessories',
            ],
            b = [
            ],
            c = [
                'https://www.yolke.co.uk/collections/silk-pyjama-sets',
                'https://www.yolke.co.uk/collections/cotton-pyjama-sets',
                'https://www.yolke.co.uk/collections/day-wear',
                'https://www.yolke.co.uk/collections/dresses',
                'https://www.yolke.co.uk/collections/dressing-gowns',
            ],
            s = [
            ],

        params = dict(
            page = 1,
            ),
        ),

    )


    countries = dict(
        US = dict(
            currency = 'USD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        )
        


