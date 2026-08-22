from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, scripts, item, **kwargs):
        scripts_data = scripts.extract()
        for script in scripts_data:
            if 'spConfig' in script:
                script_str = script
                break
        script_str = script_str.split('Product.Config(')[-1].split('/**')[0].split(');')[0]
        script_dict = json.loads(script_str)
        if len(script_dict['attributes']['139']['options']) == 0:
            sold_out = True
        else:
            sold_out = False
            item['tmp'] = script_dict
        return sold_out

    def _page_num(self, data, **kwargs):
        page = 10
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?p=' + str(i)
        
        return url

    def _color(self, data, item, **kwargs):
        try:
            item['color'] = item['tmp']['attributes']['92']['options'][0]['label']
        except:
            item['color'] = ''

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        item['sku']=sku_data




    def _images(self, images, item, **kwargs):
        images_list = images.extract()
        img_li = []
        for img in images_list:
            img_li.append(img)
        item['images'] = img_li
        item['cover'] = img_li[0]
    def _description(self, description, item, **kwargs):
        description =  description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc or 'CDATA' in desc or desc=='':
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        json_dict = item['tmp']
        products = json_dict['attributes']['139']['options']
        size_li = []
        for product in products:
            size = product['label']
            if  'stock 'in size.lower():
                continue
            size_li.append(size)

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = item['tmp']['basePrice']
        item['originlistprice'] = item['tmp']['oldPrice']



_parser = Parser()


class Config(MerchantConfig):
    name = 'temperley'
    merchant = 'Temperley London'
    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="product-image"]',
            designer = '//html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[@id="product-script"]', _parser.checkout)),
            ('sku', ('//meta[@itemprop="sku"]/@content',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),   
            ('designer', '//meta[@itemprop="brand"]/@content'),
            ('images', ('//div[@id="slider"]/div/img/@src', _parser.images)),
            ('description', ('//div[@class="std"]//text()',_parser.description)), # TODO:
            ('color',('///html', _parser.color)),
            ('sizes', ('//html', _parser.sizes)), 
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
        )

    list_urls = dict(
        f = dict(
            c = [
                "https://www.temperleylondon.com/us/all-products.html?limit=all&p=",

            ],


        ),
        m = dict(
            a = [
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
            country_url = '/us/'
            ),

        CN = dict(
            currency = 'CNY',
            country_url = '/row/',
            discurrency = 'GBP',
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '/row/',
            discurrency = 'GBP',
        ),
        KR = dict(
            currency = 'KRW',
            country_url = '/row/',
            discurrency = 'GBP',
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/row/',
            discurrency = 'GBP'
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '/row/',
            discurrency = 'GBP'
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/',
        ),
        RU = dict(
            currency = 'RUB',
            country_url = '/row/',
            discurrency = 'GBP'    
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = '/ca/',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '/row/',
            discurrency = 'GBP',
        ),

        DE = dict(
            currency = 'EUR',
            country_url = '/eu/',
        ),
        NO = dict(
            currency = 'NOK',
            country_url = '/row/',
            discurrency = 'GBP'
        ),
        )
