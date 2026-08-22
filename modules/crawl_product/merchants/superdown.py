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
        page = int(data.split("of")[-1].split("item")[0])/96 +1
        print(page)
        return page

    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = item["url"].split("?")[0].split("/")[-1].upper()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:

            if img not in images:
                images.append(img)
            if not cover and "_V1" in img.lower():
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
        item["designer"] = item["designer"].upper()
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
    

    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//*[@id="onePriceRetailPrice"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//*[@id="twoPricePrice"]/text()').extract()[0].strip()
        except:
            item['originlistprice'] = prices.xpath('.//*[@id="onePriceRetailPrice"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//*[@id="onePriceRetailPrice"]/text()').extract()[0].strip()


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//li[@class="image-carousel__item"]/img/@src').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[contains(@class,"js-plp-item-count")]/text()').extract_first().lower().split("of")[-1].split("item")[0])
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'superdown'
    merchant = 'SuperDown'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[contains(@class,"js-plp-item-count")]/text()',_parser.page_num),
            items = '//li[@class="gc u-center u-margin-b--lg"]',
            designer = './p[contains(@class="product-brand")]/text()',
            link = './/a[@class="products-grid__images"]/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//div[@id="addToBagBtn"]', _parser.checkout)),
            ('images',('//li[@class="image-carousel__item"]/img/@src',_parser.images)), 
            ('sku',('//div/@data-master-id',_parser.sku)),
            ('color','//span[@class="pdp__spec--color"]/text()'),
            ('name', '//h1[@id="product-name"]/text()'),
            ('designer','//a[@class="pdp__brand"]/text()'),
            ('description', ('//ul[@class="pdp-details__list"]//text()',_parser.description)),
            ('sizes',('//*[@class="pdp__size-options--item"]/input/@value',_parser.sizes)),
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
            a = [
                "https://www.superdown.com/shop/cat/hats-hair-accessories-accessories/002f3e?pageNum=",
                "https://www.superdown.com/shop/cat/jewelry-accessories/cc994e?pageNum="
            ],
            b = [
                "https://www.superdown.com/shop/cat/bags-accessories/350364/?pageNum="
            ],

            c = [
                "https://www.superdown.com/shop/cat/clothing/3699fc?pageNum=",
                "https://www.superdown.com/shop/cat/dresses/a8e981?pageNum=",
            ],
            s = [
                "https://www.superdown.com/shop/cat/shoes/3f40a9?pageNum=",
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

        


