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
        pages = int(data.split("items")[0].split["of"][-1].strip().replace(",",""))/30 + 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + '?start=%s&sz=32/' %i*30
        return url


    def _sku(self, sku_data, item, **kwargs):
        sku = item["url"].split("-")[-1].split('.html')[0].upper()
        item['sku'] =  sku



    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        # print images
        images = []
        cover = None
        for img in imgs:
            img = img.split("?")[0]

            if img not in images:
                images.append(img)
            if not cover and "_0" in img.lower():
                cover = img

        item['images'] = images
        # item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('//div[@class="b-product_long_description"]//text()').extract() 
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
        item["designer"] = "RUCOLINE"

    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//h4[contains(@class,"js-product_price-standard")]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//span[@class="b-product_price-sales"]/text()').extract()[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//h4[contains(@class,"js-product_price-standard")]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//h4[contains(@class,"js-product_price-standard")]/text()').extract()[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//img[@class="js-producttile_image b-product_image  js-zoomy"]/@src').extract()
        images = []
        for img in imgs:
            img = img.split("?")[0]
            if img not in images:
                images.append(img)

        return images
        



    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[contains(@class,"l-search_result-paging-controls-loaded")]//text()').extract_first().strip().lower().split("of")[-1].split("item")[0].strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'rucoline'
    merchant = 'Rucoline'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="l-search_result-paging-controls-loaded js-paging-controls-loaded"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//li[contains(@class,"b-swatches_color-item")]/a|.//a[contains(@class,"js-producttile_link")]',
            designer = './div/span/@data-product-brand',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@class="js-add_to_cart b-product_add_to_cart-submit "]', _parser.checkout)),
            ('images',('//img[@class="js-producttile_image b-product_image  js-zoomy"]/@src',_parser.images)), 
            ('color','//span[@class="js_color-description h-hidden"]/text()'),
            ('sku',('//div[@class="style-number"]//span[@class="screen-reader-digits"]/text()',_parser.sku)),
            ('name', '//span[@class="b-product_name"]/text()'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//li[@class="b-swatches_size-item emptyswatch"]/a/@title',_parser.sizes)),
            ('prices', ('//div[@class="b-product_container-price"]', _parser.prices)),
            

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
                "https://www.rucoline.com/en/men/shoes/?p=",
            ],

        ),
        f = dict(
            a = [
                "https://www.rucoline.com/en/women/accessories/small-leather-goods/?p="
            ],
            b = [
                "https://www.rucoline.com/en/women/accessories/bags/?p="
            ],
            s = [
                "https://www.rucoline.com/en/women/shoes/?p=",
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
            thousand_sign = ".",
            cookies = {'preferredCountry':'US'},
            

        ),


        CN = dict(
            area = "EU",
            currency = 'CNY',
            thousand_sign = '.',
            currency_sign = '\xa5',
            cookies = {'preferredCountry':'CN'},

        ),
        KR = dict(
            area = "EU",
            currency = 'KRW',
            discurrency = "EUR",
            cookies = {'preferredCountry':'KR'},
            currency_sign = '\u20ac',
            thousand_sign = ".",

        ),
        SG = dict(
            area = "EU",
            currency = 'SGD',
            discurrency = "EUR",
            cookies = {'preferredCountry':'SG'},
            currency_sign = '\u20ac',
            thousand_sign = ".",
        ),
        HK = dict(
            area = "EU",
            currency = 'HKD',
            cookies = {'preferredCountry':'HK'},
            currency_sign = 'HK$',
            thousand_sign = ".",
        ),
        GB = dict(
            area = "EU",
            currency = 'GBP',
            cookies = {'preferredCountry':'GB'},
            currency_sign = '\xa3',
            thousand_sign = ".",

            
        ),
        RU = dict(
            area = "EU",
            currency = 'RUB',
            discurrency = "EUR",
            cookies = {'preferredCountry':'RU'},
            currency_sign = '\u20ac',
            thousand_sign = ".",
        ),
        CA = dict(
            area = "EU",
            currency = 'CAD',
            discurrency = "EUR",
            cookies = {'preferredCountry':'CA'},
            currency_sign = '\u20ac',
            thousand_sign = ".",
        ),
        AU = dict(
            area = "EU",
            currency = 'AUD',
            discurrency = "EUR",
            cookies = {'preferredCountry':'AU'},
            currency_sign = '\u20ac',
            thousand_sign = ".",
        ),
        DE = dict(
            area = "EU",
            currency = 'EUR',
            cookies = {'preferredCountry':'DE'},
            currency_sign = '\u20ac',
            thousand_sign = ".",
        ),
        NO = dict(

            currency = 'NOK',
            area = "EU",
            cookies = {'preferredCountry':'NO'},
            currency_sign = '\u20ac',
            thousand_sign = ".",
        ),    
        )

        


