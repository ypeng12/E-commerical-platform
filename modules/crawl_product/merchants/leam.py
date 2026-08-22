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

    def _page_num(self, url, **kwargs):
        page_num = 30
        return int(page_num)
  

    def _sku(self, sku_data, item, **kwargs):

        sku = sku_data.extract_first()
       	obj = json.loads(sku)
       	item["sku"] = obj["sku"]
       	item["color"] = obj["color"]
        
        


    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        # print images
        images = []
        cover = None
        for img in imgs:
            img = img.split("?")[0]
            if "http" not in img:
                img = "http:" + img
            if img not in images:
                images.append(img)
            if not cover and "-1" in img.lower():
            	cover = img

        item['images'] = images
        # item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes_data, item, **kwargs):

        scripts_data = sizes_data.extract()
        for script in scripts_data:
            if 'spConfig' in script:
                script_str = script
                break
        script_str = script_str.split('Product.Config(')[-1].split('/**')[0].split(');')[0]
        json_dict = json.loads(script_str)
        item['tmp'] = json_dict
        try:
            products = json_dict['attributes']['169']['options']
        except:
            products = []
        size_li = []
        for product in products:
            size = product['label']
            size_li.append(size)

        item['originsizes'] = size_li

        if item['category'] in ['a','b'] and size_li == []:
            item['originsizes'] = ['IT']

        item["sku"] = item['tmp']["productId"]
    def _prices(self, prices, item, **kwargs):
        # prices  = item['tmp']

        try:
            item['originlistprice'] = prices.xpath('.//p[@class="old-price"]//span[@class="price"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//p[@class="special-price"]//span[@class="price"]/text()').extract()[0].strip()
        except:
            try:
                item['originsaleprice'] = prices.xpath('.//span[@class="regular-price"]/span[@class="price"]/text()').extract()[0].strip()
                item['originlistprice'] = prices.xpath('.//span[@class="regular-price"]/span[@class="price"]/text()').extract()[0].strip()
            except:
                item['originsaleprice'] = "0"
                item['originlistprice'] = "0"
                item["error"] = "AVAILABLE ONLY IN BOUTIQUE"

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product_photo"]/a/img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "http:" + img
            if img not in images:
                images.append(img)

        return images
        





_parser = Parser()



class Config(MerchantConfig):
    name = 'leam'
    merchant = 'Leam'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html', _parser.page_num),
            items = '//div[@class="item-inner"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './/div[@class="item-title"]/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@onclick="productAddToCartForm.submit(this)"]', _parser.checkout)),
            ('name','//div[@class="product-name"]//h2/text()'),
            ('images',('//div[@class="product_photo"]/a/img/@src',_parser.images)), 
            ('designer','//div[@class="product-name"]//h1/text()'),
            ('description', ('//div[@class="product-description"]//text()',_parser.description)),
            ('sizes',('//div[@class="product-price"]//script/text()',_parser.sizes)),
            ('prices', ('//div[@class="price-box"]', _parser.prices)),
            ('sku',('//script[@type="application/ld+json"]/text()',_parser.sku)),
            

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



        ),
        f = dict(
            a = [
                "https://www.leam.com/en/women/accessories.html?p=",
            ],
            b = [
            	"https://www.leam.com/en/women/bags.html?p="
            ],

            c = [

                "https://www.leam.com/en_en/women/clothing.html?p=",

            ],
            s = [
            	"https://www.leam.com/en/women/shoes.html?p=",
            ],





        params = dict(
            # TODO:

            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
         US = dict(
            language = 'EN', 
            area = 'EU',
            currency = 'USD',
            discurrency = 'EUR',
            currency_sign =  '\u20ac',
            
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ), 
        )

        


