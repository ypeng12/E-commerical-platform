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
            if not cover and "_main" in img.lower():
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
        
        item['sku'] = sku_data.extract_first().strip()

        

    def _sizes(self, sizes_data, item, **kwargs):
        

        if item['category'] in ['a','e']:
            item['originsizes'] = ['IT']

        item["designer"] = "CHARLOTTE TILBURY"
    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = prices.xpath('.//del[@class="DisplayPrice__rrp"]/text()').extract_first()
            item['originsaleprice'] = prices.xpath('.//*[@class="DisplayPrice__price"]/text()').extract_first()
        except:

            item['originsaleprice'] =prices.xpath('.//*[@class="DisplayPrice__price"]/text()').extract_first()

            item['originlistprice'] =prices.xpath('.//*[@class="DisplayPrice__price"]/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="ProductImage ThumbnailsRail__image"]//img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "http:" + img
            if img not in images:
                images.append(img)

        return images
        



    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//a[@class="Anchor ProductCard__link"]/@href').extract())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'charlotte'
    merchant = 'Charlotte Tilbury'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//a[@class="Anchor ProductCard__link"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './@href',
            ),
        product = OrderedDict([
        	
            ('name','//h1[@itemprop="name"]/text()'),
            ('images',('//div[@class="ProductImage ThumbnailsRail__image"]//img/@src',_parser.images)), 
            ('sku',('//div[@class="SellBlock__info"]//@data-bv-product-id',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('description', ('//div[@class="AccordionItem__content"][1]//text()',_parser.description)),
            ('sizes',('//div[@class="product-price"]//script/text()',_parser.sizes)),
            ('prices', ('//p[@class="SellBlock__price"]', _parser.prices)),
            

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

        ),
        f = dict(

            e = [
            	"https://www.charlottetilbury.com/us/products/skin-care?p=",
                "https://www.charlottetilbury.com/us/products/makeup?p="

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
            country_url = "/jp/",
        ),


        CN = dict(
            currency = 'CNY',
            country_url = "/cn/",
            currency_sign = 'CN\xa5',
        ),
        KR = dict(
            currency = 'KRW', 
            country_url = "/kr/",   
            currency_sign = "\u20A9"
        ),
        SG = dict(
            currency = 'SGD',
            country_url = "/sg/",
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = "/hk/",

        ),

        RU = dict(
            currency = 'RUB',
            currency_sign = 'RUB',
            country_url = "/ru/",
        ),
        CA = dict(
            currency = 'CAD',
            country_url = "/ca/",
            
        ),
        AU = dict(
            currency = 'AUD',
            country_url = "/au/",
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
            country_url = "/ie/",
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = "EUR",
            currency_sign = '\u20ac',
            country_url = "/ie/",

        ), 
        )

        


