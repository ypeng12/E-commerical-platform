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
        num_data = 30
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = i
        url = urljoin(response_url.split('?')[0], '?page=%s'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first()[:-6].upper()
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
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="nosto_sku"]//span[@class="list_price"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//p[@id="price-preview"]//del/div/text()').extract()[0]
        except:
            item['originlistprice'] = prices.xpath('.//div[@class="key-details"]//meta[@itemprop="price"]/@content').extract()[0]
            item['originsaleprice'] = prices.xpath('.//div[@class="key-details"]//meta[@itemprop="price"]/@content').extract()[0]
    def _color(self, color, item, **kwargs):
        item['name'] = item['name'].replace('\n','').replace('    ','').replace('  ',' ').strip()
        item['color'] = ''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="product-slider"]//a/@href').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)

        return images
        





_parser = Parser()



class Config(MerchantConfig):
    name = 'sportsedit'
    merchant = 'The Sports Edit'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="search-results-nav__info"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@id="products"]/div',
            designer = './/h3/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@id="addToCart"]', _parser.checkout)),
            ('images',('//div[@id="product-slider"]//a/@href',_parser.images)), 
            ('sku',('//span[@class="nosto_sku"]//span[@class="id"]/text()',_parser.sku)),
            ('name', '//span[@class="productname"]/text()'),
            ('designer','//span[@itemprop="brand"]/text()'),
            ('color',('//div[@class="color-option"]/text()',_parser.color)),
            ('description', ('//div[@id="new-product-tabs"]/div/div/div[1]//p/text()',_parser.description)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//select[@id="product-select"]/option[not(@disabled)]/text()',_parser.sizes)),
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
            c = [
                'https://www.thesportsedit.com/collections/mens-bottoms?page=1&currency=usd',
                "https://www.thesportsedit.com/collections/mens-sports-tops?page=1&currency=usd",
                "https://www.thesportsedit.com/collections/mens-gym-clothes?page=1&currency=usd",
                "https://www.thesportsedit.com/collections/mens-running-clothes?page=1&currency=usd",
                "https://www.thesportsedit.com/collections/mens-leisure?page=1&currency=usd"
            ],
            s = [
                "https://www.thesportsedit.com/collections/mens-trainers?page=1&currency=usd",
                ],
        ),
        f = dict(

            c = [
                'https://www.thesportsedit.com/collections/womens-gym-bottoms?page=1&currency=usd',
                "https://www.thesportsedit.com/collections/womens-sports-tops?page=1&currency=usd",
                "https://www.thesportsedit.com/collections/sports-bras-and-crops?page=1&currency=usd",
                "https://www.thesportsedit.com/collections/maternity-sportswear?page=1&currency=usd"
            ],
            s = [
                "https://www.thesportsedit.com/collections/womens-trainers?page=1&currency=usd",
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
            country_url = "&currency=usd"
            
            ),

        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            country_url = "&currency=gbp",

        ),
        JP = dict(
            currency = 'JPY',
            country_url = "&currency=jpy",

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            country_url = "&currency=gbp",


        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            country_url = "&currency=gbp",

        ),
        HK = dict(
            currency = 'HKD',
            country_url = "&currency=hkd",  

        ),
        GB = dict(
        	area = 'EU',
            currency = "GBP",
            country_url = "&currency=gbp",

        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            thousand_sign = ".", 
            country_url = "&currency=eur",

        ),
        CA = dict(
            currency = 'CAD',            
            
            country_url = "&currency=cad",

        ),
        AU = dict(
            currency = 'AUD',
            
            country_url = "&currency=aud",     

        ),
        DE = dict(
            currency = 'EUR',
            country_url = "&currency=eur",
            thousand_sign = '.',    

        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'eur',
            country_url = "&currency=eur",
            thousand_sign = '.',
        ),
#      
        )

        


