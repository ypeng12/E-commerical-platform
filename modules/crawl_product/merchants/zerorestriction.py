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
        pages = int(20)
        return pages




    def _sku(self, sku_data, item, **kwargs):
        sku = item["url"].split("?variant=")[-1]
        item['sku'] =  sku +"_"+item["color"]



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
        
        description = description.xpath('//div[@itemprop="description"]//text()').extract()   
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        item["designer"] = "ZERO RESTRICTION"

    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//*[@id="ComparePrice-product-template"').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//*[@id="ProductPrice-product-template"]/text()').extract()[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//*[@id="ProductPrice-product-template"]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//*[@id="ProductPrice-product-template"]/text()').extract()[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="ProductPhoto"]/a/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "http:" + img
            if img not in images:
                images.append(img)

        return images
        





_parser = Parser()



class Config(MerchantConfig):
    name = 'zerorestriction'
    merchant = 'ZeroRestriction'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="lc_bld plp_counter"]/text()', _parser.page_num),
            items = '//div[@class="product-card__info"]',
            designer = './div/span/@data-product-brand',
            link = './/@data-variant-url',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="AddToCartForm-product-template"]', _parser.checkout)),
            ('images',('//div[@id="ProductPhoto"]/a/@href',_parser.images)), 
            ('color','//div[@class="panda-swatch  ps-selected"]/@data-value'),
            ('sku',('//div[@class="style-number"]//span[@class="screen-reader-digits"]/text()',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//select[@id="SingleOptionSelector-1"]/option/@value',_parser.sizes)),
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
        )

    list_urls = dict(
        f = dict(
            c = [
                "https://zerorestriction.com/collections/womens-jackets?page=",
                "https://zerorestriction.com/collections/womens-vests?page=",
                "https://zerorestriction.com/collections/wtech-layers?page=",
                "https://zerorestriction.com/collections/wbottoms?page=",
            ],

        ),
        m = dict(
            a= ["https://zerorestriction.com/collections/accessories?page="],

            c = [
                "https://zerorestriction.com/collections/mens-jackets?page=",
                "https://zerorestriction.com/collections/mens-vests?page=",
                "https://zerorestriction.com/collections/tech-layers?page=",
                "https://zerorestriction.com/collections/mbottoms?page=",
                
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
            area = 'US',
            currency = 'USD',
            country_url = ".com/"

        ),

# No other country info
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = "USD",
            
        # ),

        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = "USD",
        # ),



#       
   
        )

        


