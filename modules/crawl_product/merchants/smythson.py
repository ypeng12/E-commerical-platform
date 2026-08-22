from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first() != 'true':
            return True
        else:
            return False


    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "http:" + img
            if img not in images:
                images.append(img)
            if not cover and "_w.jpg" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        item
          


    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = sku_data.extract_first().split(":")[-1].strip()

        

    def _sizes(self, sizes_data, item, **kwargs):
        

        if item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

        item["designer"] = "SYMTHSON"
    def _prices(self, prices, item, **kwargs):
        #nothing on sale right now, so cant see what how to get sale price, will have to check latter when they have sale.
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="b-product_attributes-regular_price"]/span[@itemprop="price"]/@content').extract_first()
            item['originsaleprice'] = prices.xpath('.//span[@class="b-product_attributes-sales_price"]/span[@itemprop="price"]/@content').extract_first()
        except:

            item['originsaleprice'] =prices.xpath('.//span[@class="b-product_attributes-sales_price"]/span[@itemprop="price"]/@content').extract_first()
            item['originlistprice'] =prices.xpath('.//span[@class="b-product_attributes-sales_price"]/span[@itemprop="price"]/@content').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="b-images-item"]//picture//img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "http:" + img
            if img not in images:
                images.append(img)

        return images
        

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="b-sort-result_count_copy"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('products',''))
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'smythson'
    merchant = 'Smythson'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//div[@class="product"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './div/div/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@class="js-availability"]/@data-ready-to-order', _parser.checkout)),
            ('name','//h1/text()'),
            ('images',('//div[@class="b-images-item"]//picture//img/@src',_parser.images)),
            ('color','//span[@class="colorName"]/text()'), 
            ('sku',('//div[@class="b-product_attributes-id"]/text()',_parser.sku)),
            ('description', ('//div[@id="tabDetails"]/div//text()',_parser.description)),
            ('sizes',('//div[@class="product-price"]//script/text()',_parser.sizes)),
            ('prices', ('//div[@class="b-product_attributes-price"]', _parser.prices)),
            

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
                "https://www.smythson.com/us/men/accessories?start=0&sz=9999",
                "https://www.smythson.com/us/men/scarves?start=0&sz=9999",
            ],
            b = [
                "https://www.smythson.com/us/men/bags?start=0&sz=9999"
            ],
        ),
        f = dict(
            a = [
                "https://www.smythson.com/us/women/accessories?start=0&sz=9999",
                "https://www.smythson.com/us/women/scarves?start=0&sz=9999"
            ],
            b = [
            	"https://www.smythson.com/us/women/bags?start=0&sz=9999"

            ],




        params = dict(
            # TODO:

            ),
        ),

    )


    countries = dict(
         US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            currency_sign =  '$',
            country_url = "/us/",
            
        ),

        JP = dict(
            
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = "/jpy/en/",
        ),


        CN = dict(
            currency = 'CNY',
            country_url = "/int/",
            discurrency = "GBP"
        ),
        KR = dict(
            currency = 'KRW', 
            country_url = "/int/",
            discurrency = "GBP"
        ),
        SG = dict(
            currency = 'SGD',
            country_url = "/int/",
            discurrency = "GBP"
        ),
        HK = dict(
            currency = 'HKD',
            country_url = "/int/",
            discurrency = "GBP"

        ),

        RU = dict(
            currency = 'RUB',
            country_url = "/int/",
            discurrency = "GBP"
        ),
        CA = dict(
            currency = 'CAD',
            country_url = "/int/",
            discurrency = "GBP"
            
        ),
        AU = dict(
            currency = 'AUD',
            country_url = "/int/",
            discurrency = "GBP"
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = "/uk/",
        ),

        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = "/eur/",
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = "EUR",
            currency_sign = '\u20ac',
            country_url = "/eur/",

        ), 
        )

        


