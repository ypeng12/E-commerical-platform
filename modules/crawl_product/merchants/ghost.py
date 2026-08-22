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
        json = sku_data.extract()
        for j in json:
            if "sku" in j:
                break
        item['sku'] =  j.split('"sku": "')[-1].split('"')[0]



    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = "http:"+img.split(" ")[0].replace("_180x","_900x")

            if img not in images:
                images.append(img)
            if not cover and "_main" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('//div[@class="product-header"]//p/text()').extract() + description.xpath('//div[@class="product-information folding-section"]//p/text()').extract() + description.xpath('//div[@class="product-ingredients folding-section"]//p/text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = ""
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        item["designer"] = "GHOST DEMOCRACY"

    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//span[@class="price"]//s/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//span[@data-product-price]/text()').extract()[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//span[@data-product-price]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//span[@data-product-price]/text()').extract()[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@data-slide]/@data-bgset').extract()
        images = []
        for img in imgs:
            img = "http:"+img.split(" ")[0].replace("_180x","_900x")
            if img not in images:
                images.append(img)

        return images
        

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@class="product-details-header"]//a/@href').extract())
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'ghost'
    merchant = 'Ghost Democracy'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = '//a[contains(@class,"responsivePaginationButton--last")]/text()',
            items = '//div[@class="product-details-header"]',
            designer = './div/span/@data-product-brand',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[contains(@class,"js-add-to-cart")]', _parser.checkout)),
            ('images',('//div[@data-slide]/@data-bgset',_parser.images)), 
            ('sku',('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//h1/span/text()'),
            ('designer','//div[@class="productBrandLogo"]//@title'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
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


        ),
        f = dict(

            e = [
                "https://www.ghostdemocracy.com/collections/all?p=",
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


        ),

# US ONLY
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = "USD",
            

        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = "USD",
        # ),
        # KR = dict(
            
        #     currency = 'KRW',
        #     discurrency = "USD",
        # ),
        # SG = dict(
            
        #     currency = 'SGD',
        #     discurrency = "USD",
        # ),
        # HK = dict(
           
        #     currency = 'HKD',
        #     discurrency = "USD",
        # ),
        # GB = dict(
           
        #     currency = 'GBP',
        #     discurrency = "USD",
        # ),
        # RU = dict(
           
        #     currency = 'RUB',
        #     discurrency = "USD",
        # ),
        # CA = dict(
            
        #     currency = 'CAD',
        #     discurrency = "USD",
        # ),
        # AU = dict(
           
        #     currency = 'AUD',
        #     discurrency = "USD",
        # ),
        # DE = dict(
           
        #     currency = 'EUR',
        #     discurrency = "USD",
        # ),
        # NO = dict(

        #     currency = 'NOK',
        #     discurrency = "USD",
        # ),    
        )

        


