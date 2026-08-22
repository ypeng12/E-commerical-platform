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
    def _page_num(self, data, **kwargs):
        page = 30
        return page

    def _list_url(self, i, response_url, **kwargs):
        
        url = response_url.split('?')[0] + '?page=%s'%(i)
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
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
        item["sku"] = item['description'].split("Product MPN:")[-1].split("\n")[0].strip()
        
          



        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1
        item['color'] = ""
        item['originsizes'] = []
        for size in sizes:


            if not size.xpath("./@disabled").extract():
                print(size.xpath("./text()").extract_first())
                size  = size.xpath("./text()").extract_first().split("-")[0].split("/")[-1].split(':')[0]
                item['color'] = size.split("/")[0]
                if size not in item['originsizes']:
                    item['originsizes'].append(size.strip().replace(" ",''))

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = prices.xpath('.//span[contains(@class,"Price--compareAt")]/span/text()').extract()[-1].replace('"','')
            item['originsaleprice'] = prices.xpath('.//span[contains(@class,"Price--highlight")]/span/text()').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//span[contains(@class,"ProductMeta__Price")]/span/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[contains(@class,"ProductMeta__Price")]/span/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"Product__SlideItem--image")]//noscript/img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images
        





_parser = Parser()



class Config(MerchantConfig):
    name = 'urban'
    merchant = 'Urban Excess'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="result-count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]|//div[@class="collection-matrix"]/div//div',
            designer = './/div[@class="item-title"]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@data-action="add-to-cart"]', _parser.checkout)),
            ('name','//h1/text()'),
            ('designer','//h2[contains(@class,"ProductMeta__Vendor")]/text()'),
            ('images',('//div[contains(@class,"Product__SlideItem--image")]//noscript/img/@src',_parser.images)),
            ('description', ('//div[@class="ProductMeta__Description"]//text()',_parser.description)),
            ('sizes',('//select[contains(@id,"product-select")]/option',_parser.sizes)),
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
        m = dict(
            a = [
                "https://us.urbanexcess.com/collections/all-accessories?page="

            ],

            c = [
                "https://us.urbanexcess.com/collections/all-apparel?page=",

            ],
            s = [
                "https://us.urbanexcess.com/collections/all-footwear?page=",

            ],

        ),
        f = dict(

            s = [
            
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
            country_url = 'us.urbanexcess.com/',
            ),

        # Different Cointrues have different web-structure
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # JP = dict(
        #     area = 'GB',
        #     currency = 'JPY',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # KR = dict(
        #     area = 'GB',
        #     currency = 'KRW',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # SG = dict(
        #     area = 'GB',
        #     currency = 'SGD',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',

        # ),
        # HK = dict(
        #     area = 'GB',
        #     currency = 'HKD',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # GB = dict(
        #     area = 'GB',
        #     currency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),

        # CA = dict(
        #     currency = 'CAD',
        #     discurrency = 'USD',

        # ),
        # # AU = dict(
        # #     area = 'GB',
        # #     currency = 'AUD',
        # #     discurrency = 'GBP',
        # #     currency_sign = u'\xa3',
        # #     country_url = '.co.uk/',
        # # ),
        # DE = dict(
        #     area = 'GB',
        #     currency = 'EUR',
        #     currency_sign = u'\u20ac',
        #     country_url = '.eu/en/',
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     discurrency = 'EUR',
        #     currency_sign = u'\u20ac',
        #     country_url = '.eu/en/',
        # ),
        )

        


