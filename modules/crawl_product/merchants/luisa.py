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
        if checkout:
            return False
        else:
            return True

    def _sku(self, scripts, item, **kwargs):
        for script in scripts.extract():
            if 'window.__BODY_MODEL' in script:
                break
        data = json.loads(script.split('window.__BODY_MODEL__ =')[-1][:-1].strip())
        item['tmp'] = data
        item['sku'] = data['DynamicYieldInfo']['ItemCode'].upper()
        item['description'] = data['MetaSharing'][0]['Description']
        item['color'] = data['RequestedColorDescription']

        item['originlistprice'] = data['Detail']['PriceList']
        item['originsaleprice'] = data['Detail']['FinalPrice']
        self.prices(data, item, **kwargs)
        item['tmp'] = data

    def _designer(self,designer_data,item,**kwargs):
        item['designer'] = designer_data.extract_first().upper()

    def _images(self, images, item, **kwargs):
        for colorAvail in item['tmp']['Availability']:
            for ca in colorAvail['ColorAvailability']:
                if item['color'] == ca['Description']:
                    color_id = ca['Id']
                    break

        images = []
        imgs = item['tmp']['PhotosByColor'][color_id]
        for img in imgs:
            image = 'https://images.lvrcdn.com/Big' + img
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        osizes = item['tmp']['Availability']
        for colorAvail in item['tmp']['Availability']:
            for ca in colorAvail['ColorAvailability']:
                if item['color'] == ca['Description']:
                    size = colorAvail['Description'].replace('IT','').strip()
                    item['originsizes'].append(size)

        if 'sku' in kwargs and kwargs['sku'] != item['sku']:
            item['sku'] = kwargs['sku']
            item['originsizes'] = []
            if 'tmp' in item:
                item.pop('tmp')

    def _parse_images(self, response, **kwargs):
        images = []
        scripts = response.xpath('//script/text()').extract()

        for script in scripts:
            if 'window.__BODY_MODEL' in script:
                break
        data = json.loads(script.split('window.__BODY_MODEL__ =')[-1][:-1].strip())
        color = data['RequestedColorDescription']

        for colorAvail in data['Availability']:
            for ca in colorAvail['ColorAvailability']:
                if color == ca['Description']:
                    color_id = ca['Id']
                    break

        imgs = data['PhotosByColor'][color_id]
        for img in imgs:
            image = 'https://images.lvrcdn.com/Big' + img
            images.append(image)

        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'luisa'
    merchant = "LUISAVIAROMA"
    url_split = False
    merchant_headers = {
        'User-Agent': 'ModeSensLuisa022119',
        'x-lvr-partner-modesens': '47a09c17-0141-42e3-b1de-f0caea804d4c',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div/@data-totalpages',
            items = '//div[@id="div_lp_body"]/div/div',
            designer = './a//span[@itemprop="brand"]/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-id="ItemPage-AddToCartButton"]', _parser.checkout)),
            ('name', '//*[@data-id="ItemPage-Description"]/text()'),
            ('sku', ('//script/text()', _parser.sku)),
            # ('color','//span[contains(@class,"SelectRow__txtContainer")]/text()'),
            ('designer', ('//*[@data-id="ItemPage-Designer"]/text()',_parser.designer)),
            ('images', ('//html', _parser.images)),
            
            ('sizes', ('//html', _parser.sizes)),
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
                'https://www.luisaviaroma.com/en-us/shop/men/accessories?lvrid=_gm_i3&Page=',
                'https://www.luisaviaroma.com/en-us/shop/men/jewelry-watches?lvrid=_gm_i101&Page=',
            ],
            b = [
                'https://www.luisaviaroma.com/en-us/shop/men/bags?lvrid=_gm_i22&Page=',
            ],
            c = [
                'https://www.luisaviaroma.com/en-us/shop/men/clothing?lvrid=_gm_i1&Page=',
            ],
            s = [
                'https://www.luisaviaroma.com/en-us/shop/men/shoes?lvrid=_gm_i4&Page=',
            ],
        ),
        f = dict(
            a = [
                'https://www.luisaviaroma.com/en-us/shop/women/accessories?lvrid=_gw_i3&Page=',
                'https://www.luisaviaroma.com/en-us/shop/women/jewelry-watches?lvrid=_gw_i101&Page=',
            ],
            b = [
                'https://www.luisaviaroma.com/en-us/shop/women/bags?lvrid=_gw_i22&Page=',
            ],
            c = [
                'https://www.luisaviaroma.com/en-us/shop/women/clothing?lvrid=_gw_i1&Page=',
            ],
            s = [
                'https://www.luisaviaroma.com/en-us/shop/women/shoes?lvrid=_gw_i4&Page=',
            ],

        params = dict(
            page = 1,
            ),
        ),

    )

    countries = dict(
        US = dict(
            area = 'US',
            language = 'EN', 
            currency = 'USD',
            country_url = '/en-us/',
        ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            country_url = '/zh-cn/',
            currency_sign = '\xa5',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/en-gb/',
            currency_sign = '\xa3',
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '/en-hk/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/en-ca/',
            currency_sign = 'cad',
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '/en-jp/',
            currency_sign = '\xa5',
        ),
        KR = dict(
            currency = 'KRW',
            country_url = '/en-kr/',
            currency_sign = '\u20a9',
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/en-sg/',
            currency_sign = 'S$',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '/en-au/',
            currency_sign = 'aud',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/en-de/',
            currency_sign = '\u20ac',
        ),
        NO = dict(
            currency = 'NOK',
            country_url = '/en-no/',
            currency_sign = 'kr',
        ),
        RU = dict(
            currency = 'RUB',
            country_url = '/en-ru/',
            currency_sign = '\u0440\u0443\u0431',
        )
        )
        


