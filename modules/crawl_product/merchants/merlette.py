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
        pages = (int(data.strip().split("of")[-1].strip().replace('"',"")))+1
        return pages

    def _sku(self, sku_data, item, **kwargs):
        json = sku_data.extract()
        print(json)
        skudata = None
        for j in json:
            if "sku" in j:
                skudata = j
                break
        item['sku'] =  skudata.split('"sku": "')[-1].split('"')[0]



    def _images(self, images, item, **kwargs):

        imgs = images.xpath('.//div[contains(@class,"product-image-group--'+item["color"].lower()+'")]/img/@src').extract()
        if not imgs:
            imgs =  images.xpath('.//div[contains(@id,"product-image-id")]//img/@src').extract()

        images = []
        cover = None
        for img in imgs:
            img = "http:"+img.replace("_1200x","_500x")

            if img not in images and [item['color'].lower() in img.lower()]:
                images.append(img)

            if not cover and "_main" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('//meta[@property="og:description"]/@content').extract() + description.xpath('//div[@id="accordion__details"]//text()').extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.xpath('.//option[@selected="selected"]')
        if sizes:
            size = sizes[0].xpath("./text()").extract_first().split(" - ")[0].split("/")[-1].strip()
            sku = sizes[0].xpath("./@data-sku").extract_first().replace(size,"")
            sizes = sizes1.xpath('.//option[contains(@data-sku,"'+sku+'")]/text()').extract()
        else:
            sizes = sizes1.xpath('.//option/text()').extract()
        item['originsizes'] = []
        for size in sizes:
            if "sold" not in size.lower():
                item['originsizes'].append(size.split(" - ")[0].split("/")[-1].strip().strip())

        item["sku"] = sku
        item["color"] = size.split(" / ")[0].upper()
        item["designer"] = "MERLETTE"

    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//span[@class="product-item__price--reg"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//meta[@property="og:price:amount"]/@content').extract()[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//meta[@property="og:price:amount"]/@content').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//meta[@property="og:price:amount"]/@content').extract()[0].strip()


        





_parser = Parser()



class Config(MerchantConfig):
    name = 'merlette'
    merchant = 'Merlette'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="pagination__text"]/text()', _parser.page_num),
            items = '//a[@class="product-item__link "]',
            designer = './div/span/@data-product-brand',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="AddToCart"]', _parser.checkout)),
            
            # ('sku',('//script[@type="application/ld+json"]//text()',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//meta[@itemprop="name"]/@content'),
            ('designer','//div[@class="productBrandLogo"]//@title'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//select[@id="ProductSelect"]',_parser.sizes)),
            ('images',('//html',_parser.images)), 
            ('prices', ('//html', _parser.prices)),
            

            ]),
        look = dict(
            ),
        swatch = dict(


            ),
        image = dict(
            ),
        size_info = dict(
         
            ),
        )

    list_urls = dict(
        m = dict(


        ),
        f = dict(

            c = [
                "https://merlettenyc.com/collections/frontpage?page=",
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

        CN = dict(
            currency = 'CNY',
            discurrency = "USD",
            

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = "USD",
        ),
        KR = dict(
            
            currency = 'KRW',
            discurrency = "USD",
        ),
        SG = dict(
            
            currency = 'SGD',
            discurrency = "USD",
        ),
        HK = dict(
           
            currency = 'HKD',
            discurrency = "USD",
        ),
        GB = dict(
           
            currency = 'GBP',
            discurrency = "USD",
        ),
        RU = dict(
           
            currency = 'RUB',
            discurrency = "USD",
        ),
        CA = dict(
            
            currency = 'CAD',
            discurrency = "USD",
        ),
        AU = dict(
           
            currency = 'AUD',
            discurrency = "USD",
        ),
        DE = dict(
           
            currency = 'EUR',
            discurrency = "USD",
        ),
        NO = dict(

            currency = 'NOK',
            discurrency = "USD",
        ),    
        )

        


