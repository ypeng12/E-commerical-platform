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
        page_num = data.split('of ')[-1].strip().split('total')[0].strip()
        return int(page_num)/24+1

    def _sku(self, data, item, **kwargs):
        scripts_data = data.extract()
        for script in scripts_data:
            if "productDetails = JSON.parse('" in script:
                script_str = script
                break
        script_str = script_str.split("productDetails = JSON.parse('")[-1].split("');")[0]
        json_dict = json.loads(script_str)
        item['color'] = json_dict['color'].strip().upper()
        item['designer'] = json_dict['brand'].strip().upper()
        item['sku'] = json_dict['sku'].strip().upper()
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip().replace('  ','')
            if desc.strip() == '' or desc.strip() == ' ':
                continue

            desc_li.append(desc.strip())

        description = '\n'.join(desc_li)

        item['description'] = description.strip()

    def _sizes(self, sizes_data, item, **kwargs):

        scripts_data = sizes_data.extract()
        for script in scripts_data:
            if 'spConfig' in script:
                script_str = script
                break
        script_str = script_str.split('Product.Config(')[-1].split('/**')[0].split(');')[0]
        json_dict = json.loads(script_str)
        item['tmp'] = json_dict
        try:
            products = json_dict['attributes']['136']['options']
        except:
            try:
                products = json_dict['attributes']['216']['options']
            except:
                try:
                    products = json_dict['attributes']['252']['options']
                except:
                    products = []
        size_li = []
        for product in products:
            size = product['label']
            if  'stock 'in size.lower():
                continue
            size_li.append(size)

        item['originsizes'] = size_li

        if item['category'] in ['a','b'] and size_li == []:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):

        item['originsaleprice'] = item['tmp']['basePrice']
        item['originlistprice'] = item['tmp']['oldPrice']


   

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//img[@class="etalage_thumb_image"]/@src').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        return images
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="pager"]//p[@class="amount"]//text()[last()]').extract_first().lower().split('of ')[-1].replace('item(s)','').replace('items','').strip().split('total')[0].strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'blueberry'
    merchant = "Blueberry Brands"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pager"]/p[@class="amount"]/text()',_parser.page_num),
            items = '//div[@class="item-area"]',
            designer = './/div[@class="product-impression-data hide"]/text()',
            link = './/h2[@class="product-name"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//p[@class="availability in-stock"]', _parser.checkout)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('images', ('//img[@class="etalage_thumb_image"]/@src', _parser.images)),
            ('sku', ('//script/text()', _parser.sku)),
            ('description', ('//div[@id="tab_description_tabbed_contents"]//div[@class="std"]//ul/li//text()',_parser.description)), # TODO:
            ('sizes', ('//script/text()', _parser.sizes)),
            ('prices', ('//div[@class="pdp_price"]', _parser.prices))
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
        f = dict(
            a = [
                'https://www.blueberrybrands.co.uk/eyeglasses.html?gender=631%2C633&p=',
                "https://www.blueberrybrands.co.uk/clothing-accessories/accessories.html?gender=631%2C633&p="
            ],
            c = [
                'https://www.blueberrybrands.co.uk/clothing-accessories/clothing.html?gender=631%2C633&p=',
            ],

            s = [
                'https://www.blueberrybrands.co.uk/footwear/women.html?p=',
            ],
            e = [
                "https://www.blueberrybrands.co.uk/perfumes/women.html?p=",
            ]
        ),
        m = dict(
            a = [
                'https://www.blueberrybrands.co.uk/eyeglasses.html?gender=632&p=',
                "https://www.blueberrybrands.co.uk/clothing-accessories/accessories.html?gender=631%2C632&p="
            ],
            c = [
                'https://www.blueberrybrands.co.uk/clothing-accessories/clothing.html?gender=631%2C632&p=',
            ],
            s = [
                'https://www.blueberrybrands.co.uk/footwear/men.html?p='
            ],
            e = [
                "https://www.blueberrybrands.co.uk/perfumes/men.html"
            ],


        params = dict(
            page = 1,
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            cookies = {
                'currency':'USD',
            },
            ),

        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        GB = dict(
            currency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },  
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),

        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            },
        ),
        )
        


