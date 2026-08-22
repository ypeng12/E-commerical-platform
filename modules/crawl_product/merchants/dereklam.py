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

    def _sku(self, data, item, **kwargs):
        item['sku'] = item['url'].split('/')[-1].split('-')[-1].strip().upper()

    def _designer(self, data, item, **kwargs):
        item['designer'] = data.extract_first().strip().upper()
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            img = img.replace('_1000.jpg','_500.jpg')
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
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
        url = 'https://www.dereklam.com/us/api/products/' + item['sku']
        result = getwebcontent(url)
        obj = json.loads(result)
        sizes = obj['sizes']

        item['originsizes'] = []
        if len(sizes) != 0:

            for size in sizes:
                size = size['sizeDescription']
                if size !='':
                    item['originsizes'].append(size)

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//text()').extract()
        listPrice = prices.xpath('.//text()').extract()
        if len(listPrice) == 0:
            item['originsaleprice'] = salePrice[0].replace('\xa0','')
            item['originlistprice'] = salePrice[0].replace('\xa0','')
        else:
            item['originsaleprice'] = salePrice[0].replace('\xa0','')
            item['originlistprice'] = listPrice[0].replace('\xa0','')

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//button[@class="_3OeCK _3ot6x"]//img/@src').extract()
        images = []
        for img in img_li:
            img = img.replace('_1000.jpg','_500.jpg')
            if img not in images:
                images.append(img)
        return images


_parser = Parser()



class Config(MerchantConfig):
    name = 'dereklam'
    merchant = "Derek Lam"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            items = '//figure[contains(@data-test,"productDisplay-images")]',
            designer = './/span[@class="designer"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-test="productDetails-addToBagMain"]', _parser.checkout)),
            ('name', '//h1[@data-test="productDetails-title"]/text()'),
            ('designer', ('//meta[@property="product:brand"]/@content',_parser.designer)),
            ('images', ('//button[@class="_3OeCK _3ot6x"]//img/@src', _parser.images)),
            ('sku', ('//html', _parser.sku)),
            ('color','//span[@itemprop="color"]/text()'),
            ('description', ('//div[@itemprop="description"]//p/text()',_parser.description)), # TODO:
            ('prices', ('//p[@data-test="productDetails-price"]', _parser.prices)),
            ('sizes', ('//div[@class="product-option-cont"]//select[contains(@id,"selectedOption_3")]//@value', _parser.sizes)),
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
            size_info_path = '//div[@class="nj5Iz"]/div[1]//div[@class="_nk8D"]/div/p/text()',              
            ),
        )

    list_urls = dict(
        m = dict(
        ),
        f = dict(
            a = [
                'https://www.dereklam.com/us/sets/eyewear?i='
            ],
            s = [
                'https://www.dereklam.com/us/sets/footwear?i='
            ],
            c = [
                'https://www.dereklam.com/us/sets/10-crosby-ready-to-wear?i=',
                'https://www.dereklam.com/us/sets/10-crosby-essentials?i=',
                'https://www.dereklam.com/us/sets/denim?i=',
                "https://www.dereklam.com/us/sets/ready-to-wear?i=",
                "https://www.dereklam.com/us/sets/wardrobe?i=",

            ],
            e = [
                'https://www.dereklam.com/us/sets/10-crosby-fragranceq?i='
            ],

        params = dict(
            # TODO:
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/us/',
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = 'CNY',
            country_url = '/cn/',
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = 'JPY',
            country_url = '/jp/',
        ),
        KR = dict(
            currency = 'KRW',
            currency_sign = "KRW",
            country_url = '/kr/',
        ),
        SG = dict(
            currency = 'SGD',
            currency_sign = 'SGD',
            country_url = '/sg/',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            currency_sign = 'HKD',
            country_url = '/hk/', 
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = 'GBP',
            country_url = '/uk/',
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = 'RUB',
            country_url = '/ru/',
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CAD',
            country_url = '/ca/',
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'AUD',
            country_url = '/au/',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = 'EUR',
            country_url = '/de/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            country_url = '/no/',
        ),

        )
        


