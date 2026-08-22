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



    def _sku(self, sku_data, item, **kwargs):
        
        skus =sku_data.extract()
        for sku in skus:
            if '"sku":' in sku:
                sku = sku.split('"sku":')[-1].split('",')[0].split('"')[-1][:-2]
                break
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.xpath('.//div/@data-thumb').extract()
        images = []
        cover = None
        for img in imgs:
            img = img.replace("_small_cropped.jpg",".jpg")
            if "http" not in img:
                img = "https:" + img

            if img not in images:
                images.append(img)
            if not cover and "_main" in img.lower():
            	cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('//div[@class="product-tech__text-wrap"]//p/text()').extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()

        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//span[contains(@id,"ProductPrice")]//text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//p[@class="product__price discount_price"]/text()').extract()[0].strip()
        except:

            item['originsaleprice'] = prices.xpath('.//span[contains(@id,"ProductPrice")]//text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//span[contains(@id,"ProductPrice")]//text()').extract()[0].strip()
        item["color"] = prices.xpath('//select[@data-index="option1"]/option[@selected="selected"]/text()').extract()[0].strip().upper()
        item["name"] =  item["name"] + " " + item["color"]
        item["designer"] = "VESSI"

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div/@data-thumb').extract()
        images = []
        for img in imgs:
            img = img.replace("_small_cropped.jpg",".jpg")
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images
        



    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@data-product-type="Shoes"]//div[@class="grid__meta"]/a/@href').extract())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'vessi'
    merchant = 'Vessi Footwear'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = '//span[@class="of-text"]/span/text()',
            items = '//div[@data-product-type="Shoes"]',
            designer = './/div[@class="product-item-designer"]//text()',
            link = './/div[@class="grid__meta"]/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[contains(@id,"AddToCart-product")]', _parser.checkout)),
            ('images',('//html',_parser.images)), 
            ('sku',('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('name', '//h1[@class="product__title"]/text()'),
            ('designer','//span[@class="product-info-designer"]/text()'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//select[@data-index="option2"]/option/text()',_parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            

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
            s = [
                "https://vessifootwear.com/collections/men?p="
            ],

        ),
        f = dict(
            s = [
                "https://vessifootwear.com/collections/women?p="
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
            area = 'EU',
            currency = 'USD',
            cookies= {'cart_currency':'USD',}

        ),
        CN = dict(
            currency = 'CNY',
            duscurrency = "USD"
        ),
        JP = dict(
            currency = 'JPY',
            duscurrency = "USD"
        ),
        KR = dict(

            currency = 'KRW',
            duscurrency = "USD",
            
        ),
        SG = dict(
            currency = 'SGD',
            duscurrency = "USD",
        ),
        HK = dict(
            currency = 'HKD',
            duscurrency = "USD",
        ),
        GB = dict(
            currency = 'GBP',
            duscurrency = "USD",
        ),
        RU = dict(
            currency = 'RUB',
            duscurrency = "USD",
        ),

        AU = dict(
            currency = 'AUD',
            duscurrency = "USD"
            
        ),
        DE = dict(
            currency = 'EUR',
            duscurrency = "USD",
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            duscurrency = "USD",
        ),    
        )

        


