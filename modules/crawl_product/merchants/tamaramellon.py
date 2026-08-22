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

    def _parse_item_url(self, response, **kwargs):
        list_url = 'https://l.tamaramellon.com/api/products/styles?collection=all'
        response = requests.get(list_url)
        data = json.loads(response.text)
        products = data['data']

        for product in products:
            url = product['colorways'][0]['url'] + '&variant=' + str(product['colorways'][0]['shopify_variant_id'])
            yield url,'TAMARA MELLON'

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract()[0].split('__st=')[-1][:-1].strip())
        pid = str(data['rid'])
        color = ''
        if 'color' in data['pageurl']:
            color = data['pageurl'].split('color=')[-1].split('&variant=')[0].upper()
        item['color'] = color.replace('%20',' ')
        item['sku'] = pid + '_' + item['color']

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        item['designer'] = 'TAMARA MELLON'
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, data, item, **kwargs):
        scripts = data.extract()
        for script in scripts:
            if 'liquidProductData' in script:
                break

        obj = json.loads(script.split('liquidProductData =')[-1].split('// get hex colors')[0].strip()[:-1])
        item['originsaleprice'] = str(obj['price'] / 100)
        item['originlistprice'] = str(obj['price'] / 100)
        self.prices(obj, item, **kwargs)

        datas = obj['variants']
        osizes = []
        for data in datas:
            if data['available'] and item['color'] == data['option1']:
                osizes.append(data['option2'])
        item['originsizes'] = osizes

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//meta[@name="twitter:image"]/@content').extract()
        return images
    def _parse_checknum(self, response, **kwargs):
        list_url = 'https://l.tamaramellon.com/api/products/styles?collection=all'
        response = requests.get(list_url)
        data = json.loads(response.text)
        products = data['data']
        number = len(products)
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = 'tamaramellon'
    merchant = 'Tamara Mellon'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            parse_item_url = _parser.parse_item_url
            ),
        product = OrderedDict([
            ('checkout', ('//a[@id="add-to-cart-btn"]', _parser.checkout)),
            ('sku', ('//script[@id="__st"]/text()',_parser.sku)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('images', ('//meta[@name="twitter:image"]/@content', _parser.images)),
            ('description', ('//meta[@property="og:description"]/@content',_parser.description)),
            ('sizes', ('//script', _parser.sizes)),
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
            method = _parser._parse_checknum,
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
            ],
            b = [
            ],
            c = [
            ],
            s = [
                'https://www.tamaramellon.com/collections/all',
            ],

        params = dict(
            page = 1,
            ),
        ),

    )


    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
        ),
        )
        


