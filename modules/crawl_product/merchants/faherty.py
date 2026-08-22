# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        page_num = 20
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('/?')[0] + '?page={}'.format(str(i))
        return url

    def _checkout(self, checkout, item, **kwargs):
        available = checkout.extract_first()
        if available and available.strip() == 'Add to Bag':
            return False
        else:
            return True

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        item['name'] = json_data['name'].split(' - ')[0]
        item['designer'] = json_data['brand']['name'].upper()
        item['description'] = json_data['description']

    def _images(self, scripts, item, **kwargs):
        images = item['tmp']['offers']
        images_li = []
        for image in images:
            if image not in images_li:
                images_li.append(image['image'])

        if images:
            item['cover'] = images_li[0]
        item['images'] = images_li

    def _sizes(self, res, item, **kwargs):
        datas = json.loads(res.extract_first().split('KlarnaThemeGlobals.productVariants=')[-1].split(';window.KlarnaThemeGlobals.documentCopy')[0])
        sizes_li = []
        for data in datas:
            if data['available']:
                sizes_li.append(data['option2'])

        item['originsizes'] = sizes_li

    def _prices(self, res, item, **kwargs):
        datas = json.loads(res.extract_first().split('KlarnaThemeGlobals.productVariants=')[-1].split(';window.KlarnaThemeGlobals.documentCopy')[0])

        listprice = str(datas[0]['compare_at_price'] / 100) if datas[0]['compare_at_price'] else None
        saleprice = str(datas[0]['price'] / 100)
        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="application/ld+json"][contains(text(),"https://schema.org")]/text()').extract_first())
        images = data['offers']
        imgs = []
        for image in images:
            if image not in imgs:
                imgs.append(image['image'])

        return imgs


_parser = Parser()


class Config(MerchantConfig):
    name = 'faherty'
    merchant = "Faherty"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[contains(@class,"product-listing")]',
            designer = './/h3[@class="list-product-brand"]/text()',
            link = './/figure/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[contains(@class,"product-app__action-pane__atc-buttons")]/button/text()', _parser.checkout)),
            ('sku', '//div[@class="product-app"]/@data-product-id'),
            ('name', ('//script[@type="application/ld+json"][contains(text(),"https://schema.org")]/text()', _parser.name)),
            ('color', '//span[@class="Color"]/text()'),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//script[contains(text(),"window.KlarnaThemeGlobals")]/text()', _parser.sizes)),
            ('prices', ('//script[contains(text(),"window.KlarnaThemeGlobals")]/text()', _parser.prices))
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
                'https://fahertybrand.com/collections/mens-accessories',
            ],
            b = [
                'https://fahertybrand.com/collections/mens-bags-and-wallets',
            ],
            c = [
                'https://fahertybrand.com/collections/mens-shirt-guide',
                'https://fahertybrand.com/collections/mens-polos',
                'https://fahertybrand.com/collections/mens-shorts',
                'https://fahertybrand.com/collections/mens-tees-henleys',
                'https://fahertybrand.com/collections/mens-sweaters',
                'https://fahertybrand.com/collections/mens-pajamas-and-lounge',
            ],
            s = [
                'https://fahertybrand.com/collections/mens-shoes-socks'
            ],
        ),
        f = dict(
            a = [
                'https://fahertybrand.com/collections/mens-accessories',
            ],
            b = [
                'https://fahertybrand.com/collections/womens-bags'
            ],
            c = [
                'https://fahertybrand.com/collections/womens-dresses',
                'https://fahertybrand.com/collections/womens-shirts-tops',
                'https://fahertybrand.com/collections/womens-tees-and-tanks',
                'https://fahertybrand.com/collections/womens-shorts',
                'https://fahertybrand.com/collections/womens-swim',
                'https://fahertybrand.com/collections/womens-skirts',
                'https://fahertybrand.com/collections/womens-pant-guide'
            ],
            s = [
                "https://fahertybrand.com/collections/womens-shoes-socks",
            ],

        params = dict(
            page = 1,
            )
        )
    )


    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {
                'currency':'USD',
            }
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        HK = dict(
            currency = 'HKD',
            cookies = {
                'currency':'HKD',
            }
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        GB = dict(
            currency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        CA = dict(
            currency = 'CAD',
            cookies = {
                'currency':'CAD',
            }
        ),
        AU = dict(
            currency = 'AUD',
            cookies = {
                'currency':'AUD',
            }
        ),
        DE = dict(
            currency = 'EUR',
            cookies = {
                'currency':'EUR',
            }
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        )
        )
        


