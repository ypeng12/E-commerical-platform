from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _parse_item_url(self, response, **kwargs):
        for script in response.xpath('//script/text()').extract():
            if 'window.CURRENT_PAGE =' in script:
                break       
        obj = json.loads(script.split('window.CURRENT_PAGE =')[-1].rsplit('};')[0]+'}')
        products = obj['products']['products']

        for product in products:
            url = 'https://www.na-kd.com' + product['url']
            designer = product['brandName']

            yield url, designer

    def _checkout(self, checkout, item, **kwargs):
        try:
            obj = json.loads(checkout.extract_first().split('window.CURRENT_PAGE =')[-1].rsplit('};')[0]+'}')
            if 'articleNumber' in obj:
                item['tmp'] = obj
                return False
            else:
                return True
        except:
            return True

    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = item['tmp']['articleNumber']
        item['designer'] = item['tmp']['brandName'].upper()
        item['color'] = item['tmp']['variation']['itemColorName']['$c']

    def _sizes(self, sizes_data, item, **kwargs):
        osizes = []
        for osize in item['tmp']['sizes']:
            if osize['stock'] != 'none':
                osizes.append(osize['sizeName'])
        item['originsizes'] = osizes
          
    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['imageUrls']
        item['images'] = []
        for img in imgs:
            image = 'https://www.na-kd.com' + img.split("?")[0]
            if image not in item['images']:
                item['images'].append(image)
        
        item['cover'] = item['images'][0]

    def _prices(self, prices, item, **kwargs):
        prices = item['tmp']['sizes'][0]['price']
        item['originlistprice'] = str(prices['original'])
        item['originsaleprice'] = str(prices['current'])

    def _parse_images(self, response, **kwargs):
        script = response.xpath('//script[contains(text(),"window.CURRENT_PAGE =")]/text()').extract_first()
        obj = json.loads(script.split('window.CURRENT_PAGE =')[-1].rsplit('};')[0]+'}')
        imgs = obj['imageUrls']
        images = []
        for img in imgs:
            image = 'https://www.na-kd.com' + img.split("?")[0]
            if image not in images:
                images.append(image)
        return images        
    def _parse_checknum(self, response, **kwargs):
        for script in response.xpath('//script/text()').extract():
            if 'window.CURRENT_PAGE =' in script:
                break       
        obj = json.loads(script.split('window.CURRENT_PAGE =')[-1].rsplit('};')[0]+'}')
        products = obj['products']['products']
        # print(obj)
        number = len(products)
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'Measurements' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.split("Measurements:")[-1])
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = 'nakd'
    merchant = "NA-KD"

    path = dict(
        base = dict(
            ),
        plist = dict(
            parse_item_url = _parser.parse_item_url,
            list_url = _parser.list_url,
            ),
        product = OrderedDict([
            ('checkout', ('//script[contains(text(),"window.CURRENT_PAGE =")]/text()', _parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('description', '//meta[@property="og:description"]/@content'),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            ('images', ('//html', _parser.images)),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(

        ),
        f = dict(
            a = [
                'https://www.na-kd.com/en/accessories?sortBy=popularity&count=1000&p_categories=c_1-32935_en-us',
            ],

            c = [
                'https://www.na-kd.com/en/jackets--coats?sortBy=popularity&count=1000&p_categories=c_1-32890_en-us',
                'https://www.na-kd.com/en/sweaters?sortBy=popularity&count=1000&p_categories=c_1-32884_en-us',
                'https://www.na-kd.com/en/tops?sortBy=popularity&count=1000&p_categories=c_1-32877_en-us',
                'https://www.na-kd.com/en/dresses?sortBy=popularity&count=1000&p_categories=c_1-32867_en-us',
                'https://www.na-kd.com/en/blazers?sortBy=popularity&count=1000&p_categories=c_1-32895_en-us',
                'https://www.na-kd.com/en/trousers?sortBy=popularity&count=1000&p_categories=c_1-32897_en-us',
                'https://www.na-kd.com/en/shirts--blouses?sortBy=popularity&count=1000&p_categories=c_1-90356_en-us',
                'https://www.na-kd.com/en/lingerie?sortBy=popularity&count=1000&p_categories=c_1-32922_en-us',
                'https://www.na-kd.com/en/swimwear?sortBy=popularity&count=1000&p_categories=c_1-32916_en-us',
                'https://www.na-kd.com/en/skirts?sortBy=popularity&count=1000&p_categories=c_1-32912_en-us',
                'https://www.na-kd.com/en/jumpsuits--playsuits?sortBy=popularity&count=1000&p_categories=c_1-32909_en-us',
                'https://www.na-kd.com/en/jeans?sortBy=popularity&count=1000&p_categories=c_1-151783_en-us',
                'https://www.na-kd.com/en/sports-clothing?sortBy=popularity&count=1000&p_categories=c_1-32988_en-us',
                'https://www.na-kd.com/en/shorts?sortBy=popularity&count=1000&p_categories=c_1-32908_en-us'
            ],
            s = [
                'https://www.na-kd.com/en/shoes?sortBy=popularity&count=1000&p_categories=c_1-32961_en-us',
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
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            cookies = {'CountryCode':'GBR'}
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        )

        


