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

    def _parse_multi_items(self, response, item, **kwargs):
        urls = response.xpath('//div[@id="innav_popup_toggle"]//li[@class="attribute"]//li/a/@href').extract()
        urls.append(response.url)
        for quote in urls:
           
            href = quote
            result = getwebcontent(href) 
            html = etree.HTML(result)
            itm = deepcopy(item)
            obj = html.xpath('//head//script[@type="application/ld+json"]/text()')[0]
            obj = json.loads(obj)
            avalibility = obj["offers"]["availability"]
            
            if "OutOfStock" in avalibility:
                continue
            itm["name"] = obj["name"]
            dimentions = "Heigt: %s, Width: %s, Depth: %s, Weignt:%s" %(str(obj["height"]), str(obj["width"]), str(obj["depth"]), str(obj["weight"]))
            # try:
            #     dimentions = "\nHeigt: %s, Width: %s, Depth: %s, Weignt:%s\n" %str(obj["height"]) %str(obj["width"]) %str(obj["depth"]) %str(obj["weight"])
            # except:
            #     dimentions = ""

            
            itm["description"] = obj["description"]  + dimentions
            itm["sku"] = obj["sku"]
            itm["color"] =obj["color"]
            itm["images"] = obj["image"]
            itm["cover"] = itm["images"][0]
            price = obj["offers"]
            itm["designer"] = "RIMOVA"
            itm["url"] = obj["offers"]["url"]
            self.prices(price, itm, **kwargs)

            size = dimentions

            self.sizes(size, itm, **kwargs)
            
            yield itm

    def _page_num(self, data, **kwargs):
        pages = 30
        return pages

    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = response_url.split("?")[0] + '?start=%s&sz=12&format=page-element' %str(i*12)
        return url
  


          



        # item['cover'] = cover if cover else item['images'][0]
        


        

    def _sizes(self, sizes_data, item, **kwargs):
        if sizes_data != "":
            item['originsizes'] = [sizes_data]

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = str(prices["price"])
            item['originsaleprice'] = str(prices["price"])
        except:

            item['originsaleprice'] = "0"
            item['originlistprice'] = "0"
            item["error"] = "Please Check Price"

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
    name = 'rimowa'
    merchant = 'Rimowa'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html', _parser.page_num),
            list_url = _parser.list_url,
            items = '//a[@class="product-link"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './@href',
            ),
        product = OrderedDict([
        	
            # ('name','//div[@class="product-name"]//h2/text()'),
            # ('images',('//div[@class="product_photo"]/a/img/@src',_parser.images)), 
            # ('designer','//div[@class="product-name"]//h1/text()'),
            # ('description', ('//div[@class="product-description"]//text()',_parser.description)),
            # ('sizes',('//div[@class="product-price"]//script/text()',_parser.sizes)),
            # ('prices', ('//div[@class="price-box"]', _parser.prices)),
            # ('sku',('//script[@type="application/ld+json"]/text()',_parser.sku)),
            

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
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        m = dict(

            # a = [
            #     "https://www.rimowa.com/us/en/limited-edition/?start=0&sz=12&format=page-element",
            # ],
            # b = [
            #     "https://www.rimowa.com/us/en/all-luggage/?start=0&sz=12&format=page-element"
            # ],
        ),
        f = dict(
            a = [
                "https://www.rimowa.com/us/en/limited-edition/?start=0&sz=12&format=page-element",
            ],
            b = [
            	"https://www.rimowa.com/us/en/all-luggage/?start=0&sz=12&format=page-element"
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
            currency_sign =  '$',
            country_url = "/us/en/"
            
        ),

        JP = dict(
            area = 'EU',
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = "/jp/en/",
        ),

        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = "/gb/en/",
        ),

        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = "/de/en/",
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            
            currency_sign = 'kr',
            country_url = "/no/en/",

        ), 
        )

        


