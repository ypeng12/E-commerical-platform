from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = 10
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        item['name'] = json_data['name'].upper()
        item['designer'] = json_data['manufacturer'].upper()
        item['color'] = json_data['color']
        item['description'] = json_data['description'] if json_data['description'] else json_data['manufacturer']

    def _images(self, images, item, **kwargs):
        item['images'] = item['tmp']['image']
        item['cover'] = item['images'][0] if item['images'] else ''

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())
        if not sizes:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        listprice = item['tmp']['offers']['highPrice']
        saleprice = item['tmp']['offers']['offers'][0]['price']
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        json_data = json.loads(response.xpath('//script[@type="application/ld+json"][contains(text(),"offers")]/text()').extract_first())
        images = json_data['image']
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="productsTotalCount"]/text()').extract_first())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'd2store'
    merchant = 'd2-store'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[@class="cnt"]',
            designer = './span[@class="marca"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
        	('checkout', ('//ul[@id="cart_lnk"]/li/a[@class="add_cart"]', _parser.checkout)),
            ('sku', '//meta[@property="product:retailer_item_id"]/@content'),
            ('name',('//script[@type="application/ld+json"][contains(text(),"offers")]/text()', _parser.name)),
            ('images',('//html',_parser.images)),
            ('sizes',('//div[@id="taglia_wrap"]/a/text()',_parser.sizes)),
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
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.d2-store.com/en/women/categories/accessories/belts/groups?={}',
                'https://www.d2-store.com/en/women/categories/accessories/gloves/groups?={}',
                'https://www.d2-store.com/en/women/categories/accessories/hats/groups?={}',
                'https://www.d2-store.com/en/women/categories/accessories/jewellery/groups?={}',
                'https://www.d2-store.com/en/women/categories/accessories/mixed/groups?={}',
                'https://www.d2-store.com/en/women/categories/accessories/scarves/groups?={}',
                'https://www.d2-store.com/en/women/categories/accessories/sunglasses/groups?={}'
            ],
            b = [
                'https://www.d2-store.com/en/women/categories/accessories/bags/groups?={}'
                'https://www.d2-store.com/en/women/categories/accessories/wallets/groups?={}'
            ],
            c = [
                'https://www.d2-store.com/en/women/categories/clothing/groups?s={}',
                'https://www.d2-store.com/en/women/categories/accessories/socks',
            ],
            s = [
                'https://www.d2-store.com/en/women/categories/shoes/groups?s={}'
            ]
        ),
        m = dict(
            a = [
                'https://www.d2-store.com/en/men/categories/accessories/belts/groups?={}',
                'https://www.d2-store.com/en/men/categories/accessories/gloves/groups?={}',
                'https://www.d2-store.com/en/men/categories/accessories/hats/groups?={}',
                'https://www.d2-store.com/en/men/categories/accessories/jewellery/groups?={}',
                'https://www.d2-store.com/en/men/categories/accessories/mixed/groups?={}',
                'https://www.d2-store.com/en/men/categories/accessories/scarves/groups?={}',
                'https://www.d2-store.com/en/men/categories/accessories/sunglasses/groups?={}'
            ],
            b = [
                'https://www.d2-store.com/en/men/categories/accessories/bags/groups?={}'
                'https://www.d2-store.com/en/men/categories/accessories/wallets/groups?={}'
            ],
            c = [
                'https://www.d2-store.com/en/men/categories/clothing/groups?s={}',
                'https://www.d2-store.com/en/men/categories/accessories/socks',
            ],
            s = [
                'https://www.d2-store.com/en/men/categories/shoes/groups?s={}'
            ]
        )
    )


    countries = dict(
         US = dict(
            language = 'EN',
            currency = 'USD'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = "USD"
        )
    )

        


