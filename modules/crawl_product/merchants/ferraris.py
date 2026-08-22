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

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + "?page="+str((i))
        return url
    def _page_num(self, data, **kwargs):
        page = int(data.spit("of")[-1].split("item")[0])/32 +1
        return page

    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = sku_data.extract_first().strip()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
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

        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//span[@class="regular-price"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip()
        except:

            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip()

        


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="swiper-wrapper"]/div//img/@content').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
        

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="product_count"]/text()').extract_first().strip().split("of")[-1].split("item")[0])
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'ferraris'
    merchant = 'Ferraris Boutique'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="product_count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="pro_second_box pro_block_align_0"]',
            designer = './/div[contains(@class,"pro_list_manufacturer")]',
            link = './/a[@itemprop="url"]/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@data-button-action="add-to-cart"]', _parser.checkout)),
            ('images',('//div[@class="swiper-wrapper"]/div//img/@content',_parser.images)), 
            ('sku',('//span[@class="product-code"]/text()',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('designer','//meta[@itemprop="brand"]/@content'),
            ('description', ('//meta[@itemprop="description"]/@content',_parser.description)),
            ('sizes',('//li[@class="input-container "]/@title',_parser.sizes)),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
            

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
            a = [
                "https://www.ferrarisboutique.com/en/men-accessories/?SubmitCurrency=1&id_currency=3&page=2"
            ],
            b = [
                "https://www.ferrarisboutique.com/en/men-bags/?SubmitCurrency=1&id_currency=3&page=2"
            ],
            c = [
                "https://www.ferrarisboutique.com/en/men-clothing/?SubmitCurrency=1&id_currency=3&page=2"
            ],
            s = [
                "https://www.ferrarisboutique.com/en/men-shoes/?SubmitCurrency=1&id_currency=3&page=2"
            ],

        ),
        f = dict(
            a = [
                "https://www.ferrarisboutique.com/en/women-accessories/?SubmitCurrency=1&id_currency=3&page=2"
            ],
            b = [
                "https://www.ferrarisboutique.com/en/women-bags/?SubmitCurrency=1&id_currency=3&page=2"
            ],
            c = [
                "https://www.ferrarisboutique.com/en/women-clothing/?SubmitCurrency=1&id_currency=3&page=2"
            ],
            s = [
                "https://www.ferrarisboutique.com/en/women-shoes/?SubmitCurrency=1&id_currency=3&page=2"
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
            country_url = "?SubmitCurrency=1&id_currency=3"
        ),


        CN = dict(
            currency = 'CNY',
            discurrency = "USD",
            
            

        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            currency_sign = "\u00A5",
            country_url = "?SubmitCurrency=1&id_currency=5"
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            discurrency = "USD",

        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = "USD",

        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            discurrency = "USD",

        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = "\u00A3",
            country_url = "?SubmitCurrency=1&id_currency=2"

        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = "USD",

        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            discurrency = "USD",

        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            discurrency = "USD",

        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = "?SubmitCurrency=1&id_currency=1",
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            country_url = "?SubmitCurrency=1&id_currency=8",
            currency_sign = 'NOK',
        ),    
        )

        


