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
        if checkout:
            return False
        else:
            return True

    def _parse_item_url(self, response, **kwargs):
        obj = json.loads(response.body)
        products = obj
        
        for quote in products:
            url = (etree.HTML(quote['product_item']).xpath('//div//a/@href'))[0]
            yield url,'AMENDI'

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0]
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https://www.belstaff.com/" + img
            if img not in images:
                images.append(img)
            if not cover and "_LK.jpg" in img.lower():
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
        
          


    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = sku_data.extract()[0].strip()
        item["designer"] = 'AMENDI'
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = prices.xpath('.//div[@class="price"]/text()').extract()[-1].replace('"','')
            item['originsaleprice'] = prices.xpath('.//div[@class="price"]/text()').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//div[@class="price"]/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//div[@class="price"]/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="image-desktop"]//img/@data-src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https://" + img
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.body)
        number = len(obj)
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'amendi'
    merchant = 'AMENDI'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//div[@class="result-count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            items = '//div[@id="js-listing-holder"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@class="add-cart-btn"]', _parser.checkout)),
            ('name','//h1[@class="h1"]/text()'),
            ('designer','//meta[@property="product:brand"]/@content'),
            ('images',('//div[@class="image-desktop"]//img/@data-src',_parser.images)),
            ('color','//h2[@class="h3"]/text()'),
            ('sku',('//form/@data-sku',_parser.sku)),
            ('description', ('//div[@class="info"]/p/text()',_parser.description)),
            ('sizes',('//input[@class="size-input"]/@data-size',_parser.sizes)),
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


            c = [
                "https://www.amendi.com/wp-json/wp/v2/products?per_page=1000&category=mens&termid=130&lang=en&",

            ],


        ),
        f = dict(


            c = [
                "https://www.amendi.com/wp-json/wp/v2/products?per_page=1000&category=womens&termid=162&lang=en&"
            ],





        params = dict(
            # TODO:

            ),
        ),

    )


    countries = dict(



        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '.com/en_US/',
            ),

       
        )

        


