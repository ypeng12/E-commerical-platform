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
        if checkout:
            return False
        else:
            return True

    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _name(self, data, item, **kwargs):
        data = json.loads(data.extract_first().replace('\n',''))
        item['tmp'] = data
        item['name'] = data['name']
        item['designer'] = data['brand']['name']
        item['description'] = data['description'].split('Description---')[-1].split('---')[0].strip()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []

        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img

            images.append(img)

        item['cover'] = images[0]
        item['images'] = images
        item['designer'] = "CARB TREE"
    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.extract()
        item['originsizes'] = []
        size_li = []
        for size in sizes:
            size = size.strip().split("-")[0].strip().replace('"','')
            
            size_li.append(size)

        item['originsizes'] = size_li if size_li else ['One Size']

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[@class="actual-price font--accent money"]/text()').extract_first()
        listprice = prices.xpath('.//span[@class="actual-price font--accent money"]/text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="pdp__img-slider"]//div[@class="image--root"]/noscript/img/@src').extract()
        images = []

        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            images.append(img)

        return images


_parser = Parser()



class Config(MerchantConfig):
    name = 'crabtree'
    merchant = 'Crabtree & Evelyn'

    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = '//div[@id="bc-sf-filter-products"]/div',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add"]', _parser.checkout)),
            ('sku', '//option/@data-sku'),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('description','//meta[@name="description"]/@content'),
            ('images', ('//div[@class="pdp__img-slider"]//div[@class="image--root"]/noscript/img/@src', _parser.images)),
            ('sizes', ('//select[@id="variant-listbox"]/option[@selected="selected"]/text()', _parser.sizes)),
            ('prices', ('//p[@class="price--container"]', _parser.prices))
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
        f = dict(
            e = [
                'https://www.crabtree-evelyn.com/collections/bodycare',
                'https://www.crabtree-evelyn.com/collections/hand-care',
                'https://www.crabtree-evelyn.com/collections/skincare',
                'https://www.crabtree-evelyn.com/collections/fragrance',
                'https://www.crabtree-evelyn.com/collections/lifestyle'
            ],

        params = dict(
            page = 1,
            ),
        ),

    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),

        )
        


