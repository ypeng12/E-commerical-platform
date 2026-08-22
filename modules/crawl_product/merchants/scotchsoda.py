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

    def _page_num(self, data, **kwargs):
        num_data = data.split('of')[-1].split('product')[0].strip()
        count = int(num_data)
        page_num = count / 120 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*120
        url = urljoin(response_url.split('?')[0], '?sz=120&start=%s'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().split(':')[-1].upper()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('.//div[@class="product-short-description"]/text()').extract() + description.xpath('.//div[@class="product-specifications"]/ul/li/text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

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
                if size.strip() not in size_li:
                    size_li.append(size.strip())
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="price"]/span/@data-salesprice').extract_first()
        listPrice = prices.xpath('.//span[@class="price"]/span/@data-standardprice').extract_first()
        if not salePrice:
            salePrice =  prices.xpath('.//strong[@class="product__price"]/@content').extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else salePrice
        item['originsaleprice'] = item['originsaleprice'].strip()
        item['originlistprice'] = item['originlistprice'].strip() 

    def _color(self, color, item, **kwargs):
        color = color.extract_first().lower().replace('colour','').replace(':','').strip().upper().split(':')[-1]
        item['color'] = color
        item['designer'] = 'SCOTCH & SODA'

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//ul[@id="js-pdp-carousel"]/li/a/@href').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="search-results-nav__info"]/text()').extract_first().lower().split('of')[-1].split('product')[0].strip())
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'scotchsoda'
    merchant = 'Scotch & Soda'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="search-results-nav__info"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '///div[@class="product-trigger__media"]',
            designer = './/html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add-to-cart"]', _parser.checkout)),
            ('images',('//ul[@id="js-pdp-carousel"]/li/a/@href',_parser.images)), 
            ('sku',('//span[@class="article-number"]/text()',_parser.sku)),
            ('name', '//h1/text()'),
            ('color',('//span[@class="product-property__label-value mobile-hidden"]/text()',_parser.color)),
            ('description', ('//html',_parser.description)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//ul[@placeholder="Size"]/li/a/text()',_parser.sizes)),
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
                'https://www.scotch-soda.com/us/en/men/accessories',

            ],

            c = [
                'https://www.scotch-soda.com/us/en/men/all-clothing'
            ],
            s = [
                'https://www.scotch-soda.com/us/en/men/footwear'
            ],
            e = [
                "https://www.scotch-soda.com/us/en/men/fragrance"
            ],
        ),
        f = dict(
            a = [
                'https://www.scotch-soda.com/us/en/women/accessories',
            ],
            c = [
                'https://www.scotch-soda.com/us/en/women/all-clothing?start=0&sz=120',
            ],
            s = [
                'https://www.scotch-soda.com/us/en/women/footwear-2'
            ],
            e = [
                "https://www.scotch-soda.com/us/en/women/fragrance-2"
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
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = '/us/',
            cookies = {'country_data':'US~en'}
            
            ),

        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            country_url = '/cn/',
            cookies = {'country_data':'CN~en'}

        ),
        JP = dict(
            currency = 'JPY',
            thousand_sign = '.',
            discurrency = 'EUR',
            country_url = '/global/',
            cookies = {'country_data':'GG~en'}

        ),
        KR = dict(
            currency = 'KRW',
            thousand_sign = '.',
            discurrency = 'EUR',
            country_url = '/global/',
            cookies = {'country_data':'GG~en'}         

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            country_url = '/sg/',
            cookies = {'country_data':'SG~en'}      

        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            country_url = '/hk/',
            cookies = {'country_data':'HK~en'}      

        ),
        GB = dict(
        	area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/gb/',
            cookies = {'country_data':'GB~en'}

        ),
        RU = dict(
            currency = 'RUB',
            thousand_sign = '.',
            discurrency = 'EUR',
            country_url = '/global/',
            cookies = {'country_data':'GG~en'}

        ),
        CA = dict(
            currency = 'CAD',            
            currency_sign = 'C$',
            country_url = '/ca/',
            cookies = {'country_data':'CA~en'}

        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            thousand_sign = '.',
            country_url = '/global/',
            cookies = {'country_data':'GG~en'}        

        ),
        DE = dict(
            currency = 'EUR',
            thousand_sign = '.',
            currency_sign = '\u20ac',
            country_url = '/de/',
            cookies = {'country_data':'DE~en'}             

        ),
        NO = dict(
            currency = 'NOK',
            thousand_sign = '.',
            discurrency = 'EUR',
            country_url = '/no/',
            cookies = {'country_data':'NO~en'}
        ),
#      
        )

        


