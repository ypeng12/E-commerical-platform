from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):


    def _sku(self, data, item, **kwargs):
        item['sku'] = item["tmp"]["brandStyleId"]
        item['name'] = item["tmp"]["name"]
        item['designer'] = 'CHRISTOPHER KANE'
          
    def _images(self, images, item, **kwargs):
        script = images.extract_first().split("window.__PRELOADED_STATE__ = ")[-1].split("</script>")[0]
        obj = json.loads(script)
        product = obj["entities"]["products"]
        key=item["url"].split("-")[-1]        
        item["tmp"] = product[key]
        img_li = item["tmp"]["images"]

        images = []
        for img in img_li:
            img = img["url"].replace("_54","_800")
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images




    def _description(self, description, item, **kwargs):
        description =item["tmp"]["description"] + item["tmp"]["complementaryInformation"]
        desc_li = []
        for desc in description:
            desc = desc["value"].strip().replace("<p>","").replace("</p>"," ").replace("<li>","").replace("</li>","").replace("\t"," ").replace("</ul>","").replace("<ul>","").replace("\n"," ").strip()
            if not desc.strip():
                continue
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = item["tmp"]["sizes"]

        item['originsizes'] = []
        if len(sizes) != 0:
            for size in sizes:
                if not size["isOutOfStock"]:
                    size = size["scaleAbbreviation"]+size["name"]
                    if size not in item['originsizes']:
                        item['originsizes'].append(size.strip())
        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = str(item["tmp"]["price"]["includingTaxes"])
        item['originlistprice'] = str(item["tmp"]["price"]["includingTaxesWithoutDiscount"])

    def _parse_item_url(self, response, **kwargs):
        obj = json.loads(response.body)
        pages = int(obj['products']['totalPages'])
        if kwargs['country'].upper() == 'US':
            homeurl ='https://www.christopherkane.com/shopping/'
        elif kwargs['country'].upper() == 'GB':
            homeurl ='https://www.christopherkane.com/uk/shopping/'
        else:
            homeurl ='https://www.christopherkane.com/'+kwargs['country']+'/shopping/'
        for x in range(1, pages+1):
            url = response.url.replace('pageindex=1','pageindex='+str(x))
            result = getwebcontent(url)
            obj = json.loads(result)
            products = obj['products']['entries']
            for quote in products:
                href = quote['slug']
                url =  urljoin(homeurl, href)
                yield url,'CHRISTOPHER KANE'

    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.body)
        number = int(obj['products']['totalItems'])
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'christopherkane'
    merchant = 'Christopher Kane'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('name', '//h2[@itemprop="name"]//text()'),
            ('images', ('//script[contains(text(),"window.__PRELOADED_STATE__")]', _parser.images)),
            ('sku', ('//html', _parser.sku)),
            # ('color','//meta[@property="product:color"]/@content'),
            ('description', ('//html',_parser.description)), # TODO:
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
        ),
        f = dict(
            a = [
                'https://www.christopherkane.com/api/sets/accessories/?pageindex=',
            ],
            b = [
                'https://www.christopherkane.com/api/sets/womens-bags/?pageindex=',
            ],
            c = [
                'https://www.christopherkane.com/api/sets/womens-dresses/?pageindex=',
                'https://www.christopherkane.com/api/sets/womens-skirts-trousers/?pageindex=',
                'https://www.christopherkane.com/api/sets/womens-sweatshirts-knitwear/?pageindex=',
                'https://www.christopherkane.com/api/sets/womens-tops-shirts/?pageindex=',
                'https://www.christopherkane.com/api/sets/womens-coats-jackets/?pageindex=', 

            ],
            s = [
                'https://www.christopherkane.com/api/sets/womens-footwear/?pageindex=',
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
            currency = 'USD',
            country_url = '.com/',
        ),
        CN = dict(
            currency = 'CNY',
            country_url = '.com/cn/',
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '.com/jp/',
            
        ),
        KR = dict( 
            currency = 'KRW',
            country_url = '.com/kr/',
            
            
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '.com/hk/',
            
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '.com/sg/',
            
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '.com/uk/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '.com/ca/',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '.com/au/',
            
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '.com/de/',
        ),

        NO = dict(
            currency = 'NOK',
            discurrency ="USD",
            country_url = '.com/no/',
        ),


        )
        


