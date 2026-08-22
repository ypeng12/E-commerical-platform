from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _parse_multi_items(self, response, item, **kwargs):
        item["designer"] = "ANINE BING"
        obj = json.loads(response.body)
        obj = obj['product']

        colors = []
        item['url'] = item['url'].replace('.json','')
        item['name'] = obj['title']
        if ' - ' in item['name']:
            item['color'] = obj['title'].split('-')[-1]
        else:
            item['color'] = ''

        item['description'] = obj['body_html'].replace('<meta charset="utf-8">',' ').replace('<span style="font-weight: 400;">','').replace('<span>',' ').replace('</span>',' ').replace('</li>',' ').replace('</li>',' ').replace('<br>',' ').replace('</br>',' ').replace('<p>',' ').replace('</p>',' ').strip().replace('<p dir="ltr">',' ').replace('    ',' ').replace('  ',' ').strip().replace('<b>','').replace('</b>','').replace('<p style="padding-left: 30px;">','')
        imgs = obj['images']
        item['images'] = []
        for img in imgs:
            item['images'].append(img['src'])
        item['cover'] = item['images'][0]
        sizes = []
        first = True
        for v in obj['variants']:
            
            if v['inventory_quantity'] !=0:
                sizes.append(v['title'])

            if first:
                item['sku'] = v['sku'].replace('-'+v['title'],'')
                self.prices(v['price'], item, **kwargs)
                first = False




            
        self.sizes(sizes, item, **kwargs)

        yield item




    def _sizes(self, sizes, item, **kwargs):

        item['originsizes'] = []
        for orisize in sizes:
            item['originsizes'].append(orisize.strip())
        if item['category'] in ['a','b']:
            if not item['originsizes']:
                item['originsizes'] = ['IT']


        

    def _prices(self, prices, item, **kwargs):
        salePrice = ''

        regularPrice = prices
        item['originlistprice'] = regularPrice.strip()
        item['originsaleprice'] = regularPrice.strip()



    def _parse_item_url(self, response, **kwargs):
        obj = json.loads(response.body)
        products = obj['products']
        for quote in products:
            href = '/products/'+quote['handle']+'.json'
            url =  urljoin(response.url, href)
            yield url,'ANINE BING'



    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.body)
        number = len(obj['products'])
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'aninebing'
    merchant = 'Anine Bing'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,

            ),
        product = OrderedDict([
            # ('checkout',('//*[@id="add-to-bag-mob"]', _parser.checkout)),
            # ('sku',('//html', _parser.sku)),
            # ('name', '//h1[@class="col-12 product-description lg-first"]/text()'),
            # ('color','//span[@class="product_color"]/text()'),
            # ('description', ('//p[@class="description-content"]/text()',_parser.description)),
            # ('images', ('//div[@class="carousel-item "]/img/@data-src', _parser.images)),
            # ('sizes', ('//html', _parser.sizes)),
            # ('prices', ('//div[contains(@class,"product-price")]/text()', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            # method = _parser.parse_images,
            ),
        size_info = dict(
            # method = _parser.parse_size_info,
            # size_info_path = '//h3[contains(text(),"DETAILS & FIT")]/../../div[@class="accordion-body"]/div/p/text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
                "https://www.aninebing.com/collections/fine-jewelry/products.json??p=",
                "https://www.aninebing.com/collections/all-accessories/products.json?p=",
                "https://www.aninebing.com/collections/sunglasses/products.json?p=",

            ],
            b = [
                "https://www.aninebing.com/collections/bags/products.json?p=",
            ],
            c = [
                "https://www.aninebing.com/collections/all-clothing/products.json?p=",
            ],
            s = [
                "https://www.aninebing.com/collections/shoes/products.json?p=",
            ],

        ),
        m = dict(
            e = [
            ],
            c = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '/www.',
            ),
        GB = dict(
            currency = 'GBP',
            country_url = '/eu.',
            discurrency = 'EUR'
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/eu.',
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
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            country_url = '/eu.',
            discurrency = 'EUR',
        )

        )

        