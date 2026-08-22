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
        item['color'] = ''
        item['designer'] = 'CARMEN SOL'
        variants = response.xpath('//script/text()').extract()
        script = ""
        for v in variants:
            # print v

            if 'window.hulkapps.product =' in v:
                script = v
                break
        script = script.split("window.hulkapps.product =")[-1].split("window.hulkapps.product_collection")[0].strip()
        obj = json.loads(script)
        # print obj
        variants = obj['variants']
        color_varients = set()
        for v in variants:
            color_varients.add(v['option1'])

        for v in color_varients:
            itm = deepcopy(item)
            sizes = []
            for v2 in variants:
                if v2['available'] != True:
                    continue
                if v == v2['option1']:
                    itm['originsaleprice'] = str(v2['price'])[:-2]
                    itm['originlistprice'] = str(v2['price'])[:-2]
                    itm['sku'] = v2['sku'][0:4]+v2['sku'][-2:]
                    itm['color']= v2['option1'].upper()
                    price = v2['price']
                    if v2['option2']:
                        if v2['option2'] not in sizes:
                            sizes.append(v2['option2'])
                    else:
                        sizes = ['IT']
                        v2['option2'] = ''
                    self.prices(price, itm, **kwargs)
                    itm['name'] = v2['name'].replace(v2['option2'],'').replace('/','').strip()


                    
                    itm['cover'] = v2["featured_image"]["src"]
                    itm['images'] = [itm['cover']]
                    imgCode = itm['cover'].split(".jpg")[0].split("x4000-")[-1].split("-")[0]
                    print(imgCode)
                    for images in obj["media"]:
                        # print v2['name'].lower().split('-')[0].split('with')[-1]  
                        img = images["src"]
                        if imgCode in img and img not in itm['images']:
                            itm['images'].append(img)
                        
                            
            itm['originsizes'] = ';'.join(sizes)
            self.sizes(sizes, itm, **kwargs)
            yield itm



    def _page_num(self, data, **kwargs):
        pages = 99
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url  + str(i)
        return url
    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            item['images'].append(img)
        item['cover'] = item['images'][0]


    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if desc.strip() != '':
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.strip().split("Additional Images")[0]


    def _sizes(self, sizes, item, **kwargs):
        if sizes == []:
            item['originsizes'] = ''
        else:
            item['originsizes'] = sizes
        





_parser = Parser()



class Config(MerchantConfig):
    name = 'carmen'
    merchant = 'Carmen Sol'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
        	
            ('name','//h1/text()'),

            ('description', ('//div[@class="ProductMeta__Description"]//text()',_parser.description)),

            

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
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        m = dict(

        ),
        f = dict(
            a = [
                "https://carmensol.com/collections/charms?p=",
                "https://carmensol.com/collections/hats?p=",
                "https://carmensol.com/products/carmen-sol-borchia-bracelet?p="
            ],
            b = [
                "https://carmensol.com/collections/bags?p=",
            ],
            s = [
            	"https://carmensol.com/collections/shoes?p=",
            ],
            c = [
                "https://carmensol.com/collections/swim?p=",
            ],



        params = dict(
            # TODO:

            ),
        ),

    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        RU = dict(
            discurrency = 'USD',
            currency = 'RUB',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        )

        


