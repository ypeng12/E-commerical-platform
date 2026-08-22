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
        page = int(data.strip())/12+1
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?p=' + str(i)
        
        return url

    def _color(self, data, item, **kwargs):
        item['color'] = data.extract_first().upper() if data.extract_first() else ''

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        item['sku']=sku_data
        

    def _images(self, images, item, **kwargs):
        images_list = images
        img_li = []
        for img in images_list:
            img_li.append(img['full'])
            if  img['isMain']:
                item['cover'] = img['full']
        item['images'] = img_li

    def _description(self, description, item, **kwargs):
        description =  description.xpath('.//div[contains(@class,"description_prod")]//text()').extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc or 'CDATA' in desc or desc=='':
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, orisizes, item, **kwargs):
        originsizes = []
        for orisize in orisizes:
            originsizes.append(orisize.strip())
        size_li = []

        if item['category'] in ['a','b']:
            if not originsizes:
                size_li.append('IT')
            else:
                size_li = originsizes

        elif item['category'] in ['s','c']:
            size_li = originsizes
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('//span[@id="product-price-%s"]/span/text()'%item['sku']).extract_first()
        listPrice = prices.xpath('//span[@id="old-price-%s"]/span/text()'%item['sku']).extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice
        

    def _parse_multi_items(self, response, item, **kwargs):
        item['designer'] = 'PAUL & SHARK'
        for script in response.xpath('//script/text()').extract():
             if 'data-role=swatch-options' in script:
                json_dict = json.loads(script)
                break
        sizeColor_json = json_dict['[data-role=swatch-options]']['Magento_Swatches/js/configurable-customer-data']['swatchOptions']
        colors = sizeColor_json['attributes']['93']['options']
        sizes = sizeColor_json['attributes']['227']['options']

        for color in colors:

            colorSizeCodes = color['products']
            if not colorSizeCodes:
                continue

            itm = deepcopy(item)
           
            itm['color'] = color['label'].upper()

            colorSizeCodes = color['products']

            osizes = []
            for size in sizes:
                for code in colorSizeCodes:
                    if code in size['products']:
                        osizes.append(size['label'])
            self.sizes(osizes, itm, **kwargs)

            images = sizeColor_json['images'][colorSizeCodes[0]]

            self.images(images,itm)
            itm['sku'] = response.xpath('//input[@name="item"]/@value').extract_first()+'_'+itm['color']

            yield itm

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="toolbar-number"][last()]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'paul'
    merchant = 'Paul & Shark'
    url_split = False
    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="toolbar-number"][last()]/text()',_parser.page_num),
            list_url = _parser.list_url,
            # parse_item_url = _parser.parse_item_url,
            items = '//ol[contains(@class,"products list items product-items")]/li',
            designer = '//html',
            link = './/a[contains(@class,"product-photo")]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="product-addtocart-button"]', _parser.checkout)),
            ('sku', ('//input[@name="item"]/@value',_parser.sku)),
            ('name', '//span[@class="base"]/text()'),   
            ('description', ('//html',_parser.description)), 
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(


            ),
        image = dict(
            
            ),
        size_info = dict(
         
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(

            # a = [
            #     "https://www.rimowa.com/us/en/limited-edition/?start=0&sz=12&format=page-element",
            # ],
            # b = [
            #     "https://www.rimowa.com/us/en/all-luggage/?start=0&sz=12&format=page-element"
            # ],
        ),
        m = dict(
            a = [
                "https://www.paulandshark.com/us_en/accessories.html",
            ],
            c = [
            	"https://www.paulandshark.com/us_en/always-collection.html",
            ],
            s = [
                "https://www.paulandshark.com/us_en/shoes.html",
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
# apparently shipping to us only
        # JP = dict(
        #     area = 'EU',
        #     currency = 'JPY',
        #     currency_sign = u'\xa5',
        #     country_url = "/jp/en/",
        # ),

        # GB = dict(
        #     area = 'EU',
        #     currency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = "/gb/en/",
        # ),

        # DE = dict(
        #     area = 'EU',
        #     currency = 'EUR',
        #     currency_sign = u'\u20ac',
        #     country_url = "/de/en/",
        # ),
        # NO = dict(
        #     area = 'EU',
        #     currency = 'NOK',
            
        #     currency_sign = u'kr',
        #     country_url = "/no/en/",

        # ), 
        )

        


