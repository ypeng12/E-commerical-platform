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
        num_data = 10
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = i
        url = urljoin(response_url.split('?')[0], '?page=%s'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first()[:-2].upper()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
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
        price = prices.extract_first()
        item['originlistprice'] = price
        item['originsaleprice'] = price

    def _color(self, color, item, **kwargs):
        item['name'] = item['name'].replace('\n','').replace('    ','').replace('  ',' ').strip()
        item['color'] = ''
        item['designer'] = 'ASCENO'

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@data-slider="main-image"]/div//noscript/img/@src').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)

        return images

_parser = Parser()



class Config(MerchantConfig):
    name = 'asceno'
    merchant = 'Asceno'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="search-results-nav__info"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-action="add-to-cart"]', _parser.checkout)),
            ('images',('//div[@data-slider="main-image"]/div//noscript/img/@src',_parser.images)), 
            ('sku',('//input[@name="id"]/@data-sku',_parser.sku)),
            ('name', '//h1[@class="ProductMeta__Title Playfair Heading u-h1"]/text()'),
            ('color',('//span[@class="product-property__label-value mobile-hidden"]/text()',_parser.color)),
            ('description', ('//div[@class="accordionItemContent"]//p//text()',_parser.description)),
            ('prices', ('//div[@class="Grid ProductList--grid"]//span[@class="money"]/@data-money', _parser.prices)),
            ('sizes',('//div[@id="group_size"]//span/label/text()',_parser.sizes)),
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
        f = dict(
            c = [
                'https://www.asceno.com/collections/sleepwear?page=1',
                "https://www.asceno.com/collections/view-all-ready-to-wear?page=1",
                "https://www.asceno.com/collections/swim-beach?page=1"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            discurrency = 'GBP'
            ),

        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP'
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP'
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP'      
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP'   
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP'   
        ),
        GB = dict(
        	area = 'EU',
            discurrency = 'GBP'
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP'
        ),
        CA = dict(
            currency = 'CAD',            
            discurrency = 'GBP'
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP'      
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP'         
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP'
        )
        )

        


