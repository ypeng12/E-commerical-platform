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

    def _page_num(self, script, **kwargs):          
        page_num = int(script.split('Results')[0].strip().replace(',',''))/96

        return int(page_num)

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        img_li = []
        for i in imgs:
            if 'http' not in i:
                i = 'https:'+i
            img_li.append(i)
        item['cover'] = img_li[0]

        item['images'] = img_li
        item['sku'] = item['url'].split('/')[-1].split('_')[0].strip().upper()
        
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

    def _sizes(self, data, item, **kwargs):

        if item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

        elif item['category'] in ['c','s']:
            sizes = data.extract()

            item['originsizes'] = sizes

        
    def _prices(self, prices, item, **kwargs):
        discounted_price = prices.xpath('.//div[contains(@class,"PriceWithSchema9__value--sale")]/span/text()').extract_first()
        full_price = prices.xpath('.//s[@class="PriceWithSchema9__wasPrice"]/text()').extract_first()
        price = prices.xpath('.//span[@class="PriceWithSchema9__value PriceWithSchema9__value--details"]/span/text()').extract_first()
        item['originsaleprice'] = discounted_price if discounted_price else price
        item['originlistprice'] = full_price if full_price else price
        if not item['originlistprice'] and not item['originsaleprice']:
            item['error'] = "listprice is missing"
            item['originlistprice'] = 0
            item['originsaleprice'] = 0

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="ViewportObserver1"]//noscript/img/@src').extract()
        images = []
        
        for i in imgs:
            if 'http' not in i:
                i = 'https:'+i
            if '_11_' in i:
                images.append(i)
        return images
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="ProductListingPage51__totalProducts"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        size_info = '\n'.join(infos)
        return size_info 
_parser = Parser()



class Config(MerchantConfig):
    name = 'outnet'
    merchant = 'THE OUTNET.COM'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="ProductListingPage51__totalProducts"]/text()',_parser.page_num),
            # list_url = _parser.list_url,
            # parse_item_url = _parser.parse_item_url,
            items = '//div[@itemprop="mainEntity"]/a',
            designer = './/span[@itemprop="brand"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"CTAButtons82__addToBag")]', _parser.checkout)),
            # ('sku', ('//a[@class="action towishlist tertiary"]/@data-post',_parser.sku)),
            ('name', '//p[@class="ProductInformation82__name"]/text()'),    # TODO: path & function
            ('designer', '//h1[@itemprop="brand"]/text()'),
            ("color" , '//span[@class="ProductDetailsColours82__colourName"]/text()'),
            ('images', ('//div[@class="ViewportObserver1"]//noscript/img/@src', _parser.images)),
            ('description', ('//div[@class="EditorialAccordion82__accordionContent"]//text()',_parser.description)), # TODO:
            ('sizes', ('//label[@class="GridSelect11__optionBox"]/text()', _parser.sizes)), 
            ('prices', ('//html', _parser.prices))
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
            size_info_path = '//div[@class="EditorialAccordion83__accordionContent EditorialAccordion83__accordionContent--size_and_fit"]//text()',

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
                "https://www.theoutnet.com/en-us/shop/accessories?pageNumber="
            ],
            b = [
                "https://www.theoutnet.com/en-us/shop/bags?pageNumber="
            ],
            c = [
                "https://www.theoutnet.com/en-us/shop/clothing?pageNumber="
            ],
            s = [
                "https://www.theoutnet.com/en-us/shop/shoes?pageNumber="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            # discurrency = 'AED',
            cur_rate = 1,   # TODO
            country_url = '.com/en-us/',
            ),
        # No longer availibele in china
        # CN = dict(
        #     area = 'CN',
        #     currency = 'CNY',
        #     # discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     country_url = '.cn/en-cn/',
        #     translate = [
        #     ('www.','store.'),

        #     ]
        # ),
        JP = dict(
            language = 'JA',
            area = 'EU',
            currency = 'JPY',
            # discurrency = 'USD',
            # currency_sign = u'\xa3',
            country_url = '.com/ja-jp/',
            translate = [
            ('/accessories?page=','/%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA%E3%83%BC?page='),
            ('/bags?page=','/%E3%83%90%E3%83%83%E3%82%B0?page='),
            ('/clothing?page=','/%E3%82%A2%E3%83%91%E3%83%AC%E3%83%AB?page='),
            ('/shoes?page=','/%E3%82%B7%E3%83%A5%E3%83%BC%E3%82%BA?page=')

            ]
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            discurrency = 'USD',
            currency_sign = u'US$',
            country_url = '.com/en-kr/',
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = 'USD',
            currency_sign = u'US$',
            country_url = '.com/en-sg/',
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            # discurrency = 'USD',
            currency_sign = u'HK$',
            country_url = '.com/en-hk/', 
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',

            currency_sign = u'\xa3',
            country_url = '.com/en-gb/',
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            # discurrency = 'USD',
            currency_sign = u'RUB',
            thousand_sign = '\xa0',
            country_url = '.com/en-ru/',
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            discurrency = 'USD',
            country_url = '.com/en-ca/',
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            # discurrency = 'USD',
            # currency_sign = u'\xa3',
            country_url = '.com/en-au/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            # discurrency = 'EUR',
            currency_sign = u'\u20ac',
            thousand_sign = '.',
            country_url = '.com/en-de/',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = u'\u20ac',
            thousand_sign = '.',
            country_url = '.com/en-no/',
        ),

        )

        


