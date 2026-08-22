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
        if 'Error Code' in checkout.extract_first():
            return False
        if item['category'] in ['c','s']:
            checkout = checkout.xpath('.//div[@class="form-group"]/select/option[@data-availability>0]').extract()
        elif item['category'] in ['a','b']:
            checkout = checkout.xpath('.//button[@data-label-add-to-cart="Add to Shopping Bag"]').extract()
        if not checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first().strip()
        item['designer'] = 'FENDI'

    def _images(self, images_data, item, **kwargs):
        imgs = images_data.extract()
        
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images
        
    def _description(self, description, item, **kwargs):
        description = description.xpath('.//*[@itemprop="description"]/text()').extract() + description.xpath('.//div[@id="more-details"]//ul/li//text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.extract()
        item['originsizes'] = []
        if sizes:
            for size in sizes:
                if 'only' not in size:
                    item['originsizes'].append(size.strip().replace(',','.').strip())
        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        item['originlistprice'] = str(prices.extract_first().strip())
        item['originsaleprice'] = str(prices.extract_first().strip())

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            info_li = info.xpath('.//text()').extract()
            info_str = ''.join(info_li)
            if info_str.strip() and info_str.strip() not in fits and ('length' in info_str.lower() or 'height' in info_str.lower() or 'depth' in info_str.lower()):
                fits.append(info_str.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _page_num(self, data, **kwargs):
        num_data = data.split('(')[-1].split(')')[0].strip()
        pages = int(num_data)/60 +1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)
        url = urljoin(response_url, '?q=:relevance&page=%s'%num)
        return url
        
_parser = Parser()



class Config(MerchantConfig):
    name = 'fendi'
    merchant = 'FENDI'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//button[@id="dropdown-sub-category"]//text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"product-card")]',
            designer = './/meta[@itemprop="brand"]/text()',
            link = './/meta[@itemprop="url"]/@content',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//span[@itemprop="productID"]/text()',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('images', ('//div[@class="main-product"]/div/img/@src', _parser.images)),
            ('color','//meta[@itemprop="color"]/@content'),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//div[@class="form-group"]/select/option[@data-availability>0]/text()', _parser.sizes)),
            ('prices', ('//span[@class="price "]//text()', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="main-product"]/div/img/@src'
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="more-details"]/ul/li',
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.fendi.com/us/man/wallets-and-small-accessories',
                'https://www.fendi.com/us/man/belts',
                'https://www.fendi.com/us/man/bag-accessories',
                'https://www.fendi.com/us/man/sunglasses',
                'https://www.fendi.com/us/timepieces/categories/men-watches',
                'https://www.fendi.com/us/man/fashion-jewelry',
                'https://www.fendi.com/us/man/textile-accessories'
            ],
            b = [
                'https://www.fendi.com/us/man/bags'
            ],
            c = [
                'https://www.fendi.com/us/man/ready-to-wear'
            ],
            s = [
                'https://www.fendi.com/us/man/shoes'
            ],

        ),
        f = dict(
            a = [
                'https://www.fendi.com/us/woman/belts',
                'https://www.fendi.com/us/woman/bag-accessories',
                'https://www.fendi.com/us/woman/sunglasses',
                'https://www.fendi.com/us/timepieces/categories/women-watches',
                'https://www.fendi.com/us/woman/fashion-jewelry',
                'https://www.fendi.com/us/woman/textile-accessories',
            ],
            b = [
                'https://www.fendi.com/us/woman/bags'
            ],
            c = [
                'https://www.fendi.com/us/woman/ready-to-wear',
            ],
            s = [
                'https://www.fendi.com/us/woman/shoes'
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
            country_url = '.com/us/',
        ),
        # Works Differently then US site
        # CN = dict(
        #     currency = 'CNY',
        #     language = 'ZH',
        #     country_url = '.cn/',
        #     translate = [
        #         ('bags','bag'),
        #     ]
        # ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            country_url = '.com/gb/',
            currency_sign = '\xa3',
        ),
        HK = dict(
            area = 'HK',
            currency = 'HKD',
            country_url = '.com/hk-en/',
            currency_sign = 'HK$'
        ),
        JP = dict(
            area = 'JP',
            currency = 'JPY',
            country_url = '.com/jp-en/',
            currency_sign = '\xa5',
        ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            country_url = '.com/ca/',
            currency_sign = 'C$',
        ),
        AU = dict(
            area = 'AU',
            currency = 'AUD',
            country_url = '.com/au/',
            currency_sign = 'AUD',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            country_url = '.com/de-en/',
            thousand_sign = '.',
            currency_sign = '\u20ac',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            thousand_sign = '.',
            country_url = '.com/no/',
            currency_sign = '\u20ac',
        ),
#      
        )

        


