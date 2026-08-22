from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
from urllib.parse import urljoin
from lxml import etree
import json
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        json_url = item['url'].split('/product/')[1].split('?')[0]
        url = 'https://admin-api.seezona.com/api/site/v2/products/{}?currency=USD'.format(json_url)
        resp = requests.get(url)
        response = json.loads(resp.text)
        item['tmp'] = response
        return False

    def _name(self,res,item,**kwargs):
        item['name'] = item['tmp']['Data']['Product']['Name']
        item['designer'] = item['tmp']['Data']['Product']['BrandName']
        item['sku'] =  item['tmp']['Data']['Product']['Id'].upper()
        item['color'] = item['tmp']['Data']['Product']['Colors'][0]['Color'] if item['tmp']['Data']['Product']['Colors'] else ' '
        description = item['tmp']['Data']['Product']['Description'].strip()
        item['description'] = '\n'.join(re.findall(r"<li>([\s\S+?])</li>",description))

    def _prices(self, res, item, **kwargs):
        originsaleprice = item['tmp']['Data']['Product']['Price']
        originlistprice = item['tmp']['Data']['Product']['PriceLabel']
        item['originsaleprice'] = originsaleprice
        item['originlistprice'] = originlistprice

    def _sizes(self,res,item,**kwargs):
        sizes_li = []
        if kwargs['category'] == 'h' or kwargs['category'] == 'a':
            sizes_li = ['IT']
        else:
            for size in item['tmp']['Data']['Product']['Sizes']:
                sizes_li.append(size['Size'])
        item["originsizes"] = sizes_li
        images = item['tmp']['Data']['Product']['Images']
        image_li = []
        for image in images:
            image_li.append(image['ImageUrl'])
        item['images'] = image_li
        item['cover'] = item['images'][0]

    # def _parse_multi_items(self,response,item,**kwargs):
    #     color_dict = item['tmp']['Data']['Product']['Colors'][0]['Color']
    #     for color_data in color_dict:
    #         sku = color_data['productMasterId']
    #         item_color = deepcopy(item)
            
    #         self.sizes(osize, item_color, **kwargs)
    #         yield item_color

    def _parse_num(self,pages,**kwargs):
        # pages = pages/24+1
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('&sz=1', '&sz=%s'%i)
        return url

    def _parse_item_url(self,response,**kwargs):
        item_data = response.xpath('//json-adapter/@product-search').extract_first()
        item_data = json.loads(item_data)
        for url_items in item_data['products']:
            yield url_items['url'],'designer'

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.body)
        imgs = data['Data']['Product']['Images']
        images = []

        for img in imgs:
            image = img['ImageUrl'].split('?')[0] + '?width=684&height=900&fit=pad&auto=format&q=90'
            images.append(image)

        return images

_parser = Parser()

class Config(MerchantConfig):
    name = "seezona"
    merchant = "Seezona"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
        ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('name', ('//html', _parser.name)),
            ('prices', ('//json-adapter/@product', _parser.prices)),
            ('sizes',('//html',_parser.sizes))
        ]),
        image = dict(
            method = _parser.parse_images,
        ),
        look = dict(
        ),
        swatch = dict(
        ),        
    )

    # parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
               "https://www.seezona.com/shopping/accessories?page="
                ],
            b = [
                "https://www.seezona.com/shopping/bags?page=",
                ],
            c = [
                "https://www.seezona.com/shopping/clothing?page=",
                "https://www.seezona.com/shopping/activewear?page=",
                "https://www.seezona.com/shopping/beachwear?page="
            ],
            s = [
                "https://www.seezona.com/shopping/shoes?page="
            ],
        ),
    )

    countries = dict(
        US = dict(
            language = 'EN',
        )
    )
