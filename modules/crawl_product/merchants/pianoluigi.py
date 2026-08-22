from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.utils import *
from utils.cfg import *
from utils.ladystyle import blog_parser
import requests
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        variants = json_data['offers']
        for data in variants:
            if "InStock" in  data['availability']:
                return False

        return True

    def _sku(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        item['name'] = json_data['name']
        item['sku'] = json_data['mpn']
        item['designer'] = json_data['brand']['name']
        item['description'] = json_data['description']
        item['color'] = json_data['model'][0]['color']

    def _images(self, data, item, **kwargs):
        obj = item['tmp']
        item['images'] = [obj['image'].replace('450x450.jpg','1200x1200.jpg')]
        item['cover'] = item['images'][0]

    def _prices(self, data, item, **kwargs):
        obj = item['tmp']
        item['originlistprice'] = str(obj['offers']['highPrice'])
        item['originsaleprice'] = str(obj['offers']['lowPrice'])

    def _sizes(self, data, item, **kwargs):
        sizes_li = []
        for variant in item['tmp']['model']:
            if "InStock" in variant['offers']['availability']:
                sizes_li.append(variant['additionalProperty'][0]['value'])

        item['originsizes'] = sizes_li

    def _parse_images(self, response, **kwargs):
        images = []
        images.append(response.xpath('.//meta[@property="og:image"]/@content').extract_first())

        return images

    def _page_num(self, data, **kwargs):
        page_num = 20
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

_parser = Parser()


class Config(MerchantConfig):
    name = 'pianoluigi'
    merchant = 'Piano Luigi'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="ml-auto"]/text()',
            list_url = _parser.list_url,
            items = '//div[contains(@class,"product-collection")][@data-qv-check-change]/form/div',
            designer = './/div[contains(@class,"product-collection__more-info")]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[@type="application/ld+json"][contains(text(),"priceValidUntil")]/text()', _parser.checkout)),
            ('sku', ('//script[@data-desc="seo-product"]/text()', _parser.sku)),
            ('images', ('///html', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//meta[@property="og:description"]/@content',
            ),
        designer = dict(
            ),
        blog = dict(
        )
    )

    list_urls = dict(
        f = dict(
            'https://pianoluigi.com/collections/womens?q=pg_:{}&view=28'
        ),
        m = dict(
            'https://pianoluigi.com/collections/mens?q=pg_:{}&view=28'
        ),
    )

    countries = dict(
        US = dict(
            language = 'EN',
            currency = 'USD',
            ),
        GB = dict(
            currency = 'USD',
            discurrency = 'USD'
            ),
        DE = dict(
            currency = 'USD',
            discurrency = 'USD'
            )
        )

