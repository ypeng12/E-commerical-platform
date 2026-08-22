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
        num_data = data.strip().replace('\n','').replace('/','').lower().replace('results','').strip()
        count = int(num_data)
        page_num = count / 64 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*64
        url = response_url.split('?')[0] + '?start=%s&sz=64&loadmore=1'%num
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().upper()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            img = "https://www.brahmin.com/" + img
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
        item['originsizes'] = ["IT"]
        
    def _prices(self, prices, item, **kwargs):
        price = prices.extract_first()
        item['originlistprice'] = price
        item['originsaleprice'] = price
    def _color(self, color, item, **kwargs):
        color = color.extract_first().upper().strip().replace("\n",'')
        item['color'] = color
        item['designer'] = 'BRAHMIN'

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="pdpCarousel"]//div[@class="carousel-inner"]/div/img/@src').extract()
        images = []
        for img in imgs:
            img = "https://www.brahmin.com/" + img
            if img not in images:
                images.append(img)

        return images
        



    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="results"]/text()[2]').extract_first().strip().replace('\n','').replace('/','').lower().replace('results','').strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'brahmin'
    merchant = 'Brahmin'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="results"]/text()[2]',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-tile"]',
            designer = './/html',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="add-to-cart-holder"]', _parser.checkout)),
            ('images',('//div[@id="pdpCarousel"]//div[@class="carousel-inner"]/div/img/@src',_parser.images)), 
            ('sku',('//div[@class="product-detail product-wrapper"]/@data-pid',_parser.sku)),
            ('name', '//h1[@class="product-name"]/text()'),
            ('color',('//span[@id="selectedColor"]/text()',_parser.color)),
            ('description', ('//div[@class="productDescription"]//text()',_parser.description)),
            ('prices', ('//div[@class="price"]//span[@class="sales"]/span/@content', _parser.prices)),
            ('sizes',('//html',_parser.sizes)),
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
            b = [
                'https://www.brahmin.com/mens?start=0&sz=32&loadmore=1',

            ],

        ),
        f = dict(
            a = [
                'https://www.brahmin.com/accessories?start=0&sz=32&loadmore=1',
            ],
            b = [
                'https://www.brahmin.com/handbags?start=0&sz=32&loadmore=1',
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
            
            
            ),
# dont know there currency rates with which they are multiplying, different currency dont work without JS.
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = 'USD',
        #     # cur_rate = 1,   # TODO


        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = 'USD',
        #     # cur_rate = 1,   # TODO


        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     discurrency = 'USD',  
        #     # cur_rate = 1,   # TODO    

        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     discurrency = 'USD', 
        #     # cur_rate = 1,   # TODO    

        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     discurrency = 'USD',  
        #     # cur_rate = 1,   # TODO


        # ),
        # GB = dict(
        # 	currency = 'GBP',
        #     discurrency = 'USD',
        #     # cur_rate = 1,   # TODO

        # ),
        # RU = dict(
        #     currency = 'RUB',
        #     discurrency = 'USD',
        #     # cur_rate = 1,   # TODO

        # ),
        # CA = dict(
        #     currency = 'CAD',            
        #     discurrency = 'USD',
        #     # cur_rate = 1,   # TODO

        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     discurrency = 'USD',  
        #     # cur_rate = 1,   # TODO    

        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     discurrency = 'USD', 
        #     # cur_rate = 1,   # TODO           

        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     discurrency = 'USD',
        #     # cur_rate = 1,   # TODO
        # ),
#      
        )

        


