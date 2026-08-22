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
        instock = checkout.extract_first()

        if instock and instock == 'instock':
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        obj = json.loads(data.extract_first())
        for product in obj['products']:
            if obj["selectedProductId"] == product['id']:
                item['tmp'] = product
                break

        item['sku'] = item['tmp']['id']
        item['name'] = item['tmp']['title']
        item['designer'] = 'M. GEMI'
        item['color'] = item['tmp']['colorSwatch']
        item['description'] = item['tmp']['description']
          
    def _images(self, images, item, **kwargs):        
        img_li = item['tmp']['images']
        images = []
        cover = None
        for img in img_li:
            if '_NEW' not in img['src'].upper() or '.jpg' not in img['src']:
                continue
            image = img['src'].replace('_1x1','')
            if image not in images:
                if '_01_MAIN' in image:
                    cover = image
                images.append(image)
        images.sort()
        item['images'] = images
        item['cover'] = cover if cover else images[0]

    def _description(self, description, item, **kwargs):
        description =  item['tmp']['detailDesc']
        description.append(item['tmp']['newShortDescription'])
        desc_li = []

        for desc in description:
            if not desc:
                continue
            desc_li.append(desc)

        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = item['tmp']['variants']
        size_li = []

        for size in sizes:
            if size['available'] == True:
                size_li.append(size["size"])

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        item['originlistprice'] = item['tmp']['compare_at_price']
        item['originsaleprice'] = item['tmp']['price_money_formatted']

    def _parse_images(self, response, **kwargs):
        images = []
        obj = json.loads(response.xpath('//script[@class="pdp-data"]/text()').extract_first())
        for product in obj['products']:
            if product['id'] == kwargs['sku']:
                data = product
                break

        img_li = data['images']
        images = []

        for img in img_li:
            if '_NEW' not in img['src'].upper() or '.jpg' not in img['src']:
                continue
            image = img['src'].replace('_1x1','')
            if image in images:
                continue
            images.append(image)
        images.sort()

        return images

    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.body)
        number = (obj["productSetCount"])
        return number

    def _parse_item_url(self, response, **kwargs):
        ajax_dict = json.loads(response.body)
        prd_list = ajax_dict['productSets']
        for prd in prd_list:
            for variation in prd['colors']:
                yield ('https://mgemi.com/'+prd['colors'][variation]['canonicalPdpUrl']), 'M.GEMI'

_parser = Parser()


class Config(MerchantConfig):
    name = 'mgemi'
    merchant = "M.Gemi"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout',('//meta[@property="product:availability"]/@content', _parser.checkout)),
            ('sku', ('//script[@class="pdp-data"]/text()', _parser.sku)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
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
                "https://be.mgemi.com/api/shopify/collections/plp-productsets/87610196027/all/1/1000/"
            ],
            a = [
                "https://be.mgemi.com/api/shopify/collections/plp-productsets/87908450363/all/1/1000/"
            ],
        ),
        f = dict(
            s = [
                'https://be.mgemi.com/api/shopify/collections/plp-productsets/87600857147/all/1/1000/?p=',
            ],
            b = [
                'https://be.mgemi.com/api/shopify/collections/plp-productsets/90594639931/all/1/1000/?p='
            ],


        params = dict(
            ),
        ),

    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),

        )
        


