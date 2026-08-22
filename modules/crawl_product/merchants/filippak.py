from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):


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
        sku = sku_data.extract_first().split('no.')[-1].upper()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.xpath('.//div[@class="ah ai aj ak"]//img/@src').extract() + images.xpath('.//div[@class="fe c7 ff"]//img/@src').extract()
        images = []
        for img in imgs:
            img = "https://www.filippa-k.com"+img
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
        if item['category'] in ['a','b'] or "tie" in item["name"].lower():
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
        try:
            color = color.extract()[-1].strip().upper()
        except:
            color = ""
        item['color'] = color
        item['designer'] = 'FILIPPA K'

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="in io ip iq"]//img/@src|//div[@class="kv b5 kw"]//img/@src').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
        



    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@id="content-container"]//ul//li[contains(@class,"bf")]/a/@href').extract())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'filippak'
    merchant = 'Filippa K'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(  
            items = '//div[@id="content-container"]//ul//li[contains(@class,"bf")]',
            designer = './/html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('images',('//html',_parser.images)), 
            ('sku',('//div[contains(@class,"bk")]/text()',_parser.sku)),
            ('name', '//h1/text()'),
            ('color',('//section//div[contains(@class,"c")]/div[contains(@class,"bt")]/text()',_parser.color)),
            ('description', ('//div[@class="cc"]//text()|//div[@class="c2 dp"]//text()',_parser.description)),
            ('prices', ('//span[contains(@class,"c7 bu")]//text()|//span[contains(@class,"c9 bu")]//text()', _parser.prices)),
            ('sizes',('//ol/li/button/text()',_parser.sizes)),
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
                'https://www.filippa-k.com/en/man/accessories?count=999',

            ],
            b = [
                "https://www.filippa-k.com/en/man/accessories/bags-wallets?count=999"
            ],

            s = [
                "https://www.filippa-k.com/en/man/accessories/shoes?count=999"
            ],
            c = [
                'https://www.filippa-k.com/en/man/clothing?count=999'
            ],

        ),
        f = dict(
            a = [
                'https://www.filippa-k.com/en/woman/accessories/socks?count=999',
                "https://www.filippa-k.com/en/woman/accessories/scarves-hats?count=999",
                "https://www.filippa-k.com/en/woman/accessories/belts?count=999",
                "https://www.filippa-k.com/en/woman/accessories/gloves?count=999"

            ],
            b = [
                "https://www.filippa-k.com/en/woman/accessories/bags-wallets?count=999"
            ],
            s = [
                "https://www.filippa-k.com/en/woman/accessories/shoes?count=999"
            ],
            c = [
                'https://www.filippa-k.com/en/woman/clothing?count=999?count=999',
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
            currency_sign = 'US$',
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
        #   currency = 'GBP',
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
#      
        )

        


