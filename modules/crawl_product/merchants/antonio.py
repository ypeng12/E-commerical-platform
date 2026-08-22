from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _designer(self, data, item, **kwargs):
        json_data = json.loads(data.extract_first())
        item['tmp'] = json_data
        
        item['sku'] = json_data['sku']
        item['designer'] = json_data['brand']['name'].upper()
        item['description'] = json_data['description']
        item['color'] = ''

    def _images(self, images, item, **kwargs):
        images = images.extract()
        img_li = []
        for img in images:
            img = "https:" + img
            if img not in img_li:
                img_li.append(img.replace('large','product').split('?')[0])
        item['images'] = img_li
        item['cover'] = img_li[0]


    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []
        if item['category'] in ['a','b']:
            if not sizes:
                size_li.append('IT')
            else:
                size_li = sizes
        else:
            for size in sizes:
                size = size.replace('\n','').strip()
                size = re.sub(r'[\xbd]','.5', size)
                if size == 'I':
                    size = 'IT42'
                elif size == 'II':
                    size = 'IT44'
                elif size == 'III':
                    size = 'IT46'
                elif size == 'IV':
                    size = 'IT48'
                elif size == 'V':
                    size = 'IT50'
                elif size == 'UNI':
                    size = 'IT'
                if item['category'] == 's':
                    size = size.split('/')[0]
                elif item['category'] == 'c':
                    size = size.upper().replace('NUM','').split('/')[0]
                size_li.append(size)
            #     if item['category'] == 'c':
            #         size_str = ' '.join(size.split()[:2])
            #     elif item['category'] == 's':
            #         size_str = size.split()[0]
            #     size_li.append(size_str)
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        item['originlistprice'] = item['tmp']['offers']['price']
        item['originsaleprice'] = item['tmp']['offers']['price']

_parser = Parser()



class Config(MerchantConfig):
    name = 'antonio'
    merchant = 'Antonioli'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a[@class="last"]/text()',
            items = '//section[@class="products"]/article',
            designer = './/div[@class="brand-name"]',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"ProductForm__AddToCart")]/span', _parser.checkout)),
            ('name', '//div[@class="description-table"]//h2/text()'),    # TODO: path & function
            ('designer', ('//script[@type="application/ld+json"][contains(text(),"Product")]/text()',_parser.designer)),
            ('images', ('//img[@class="Image--lazyLoad"]/@data-src', _parser.images)),
            ('sizes', ('//div[@class="SizeSwatch__Item is-available-true"]/label/text()', _parser.sizes)), 
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//img[@itemprop="image"]/@src',
            ),
        size_info = dict(
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.antonioli.eu/en/US/men/section/accessories?page="
            ],
            b = [
                "https://www.antonioli.eu/en/US/men/section/bags?page=",
                "https://www.antonioli.eu/en/US/men/section/sale?utf8=%E2%9C%93&f%5Bcategories%5D%5B%5D=370&page="
            ],
            c = [
                "https://www.antonioli.eu/en/US/men/section/clothing?page=",
                "https://www.antonioli.eu/en/US/men/section/sale?f%5Bcategories%5D%5B%5D=478&page="
            ],
            s = [
                "https://www.antonioli.eu/en/US/men/section/shoes?page=",
                "https://www.antonioli.eu/en/US/men/section/sale?utf8=%E2%9C%93&f%5Bcategories%5D%5B%5D=479&page="
            ],
        ),
        f = dict(
            a = [
                "https://www.antonioli.eu/en/US/women/section/accessories?page="
            ],
            b = [
                "https://www.antonioli.eu/en/US/women/section/bags?page=",
                "https://www.antonioli.eu/en/US/women/section/sale?utf8=%E2%9C%93&f%5Bcategories%5D%5B%5D=480&page="
            ],
            c = [
                "https://www.antonioli.eu/en/US/women/section/clothing?page=",
                "https://www.antonioli.eu/en/US/women/section/sale?utf8=%E2%9C%93&f%5Bcategories%5D%5B%5D=478&page="
            ],
            s = [
                "https://www.antonioli.eu/en/US/women/section/shoes?page=",
                "https://www.antonioli.eu/en/US/women/section/sale?utf8=%E2%9C%93&f%5Bcategories%5D%5B%5D=479&page="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            thousand_sign = '.',
            country_url = '.eu/en-us/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        CN = dict(
            currency = 'CNY',
            thousand_sign = '.',
            currency_sign = '\xa5',
            country_url = '.eu/en-cn/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        JP = dict(
            currency = 'JPY',
            thousand_sign = '.',
            currency_sign = '\xa5',
            country_url = '.eu/en-jp/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        KR = dict(
            currency = 'KRW',
            thousand_sign = '.',
            currency_sign = '\u20a9',
            country_url = '.eu/en-kr/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            thousand_sign = '.',
            currency_sign = '\u20ac',
            country_url = '.eu/en-sg/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        HK = dict(
            currency = 'HKD',
            thousand_sign = '.',
            currency_sign = '$',
            country_url = '.eu/en-hk/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        GB = dict(
            currency = 'GBP',
            thousand_sign = '.',
            currency_sign = '\xa3',
            country_url = '.eu/en-gb/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        RU = dict(
            currency = 'RUB',
            thousand_sign = '.',
            currency_sign = '\u20bd',
            country_url = '.eu/en-ru/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            thousand_sign = '.',
            currency_sign = '$',
            country_url = '.eu/en-ca/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            thousand_sign = '.',
            currency_sign = '$',
            country_url = '.eu/en-au/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        DE = dict(
            currency = 'EUR',
            thousand_sign = '.',
            currency_sign = '\u20ac',
            country_url = '.eu/en-de/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            thousand_sign = '.',
            currency_sign = '\u20ac',
            country_url = '.eu/en-no/',
            # cookies = {
            #     'guest_token':'IncwTzc3M1ZJTmVhVmlpdXlGMGZVTnci--5b7d122e3eb0825398ee87ad5fbc5c777eb2e5bd'
            # },
        ),

        )

        


