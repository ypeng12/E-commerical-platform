from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _checkout(self, res, item, **kwargs):
        checkout = json.loads(res.extract_first())
        if checkout['event_config']['product_add_to_cart']:
            return False
        else:
            return True

    def _sku(self,sku,item,**kwargs):
        json_data = json.loads(sku.extract_first())
        item['sku'] = json_data['id']
        item["name"] = json_data['type']
        item['designer'] = json_data['vendor']
        item['description'] = re.search(r'>(.*?)<',json_data['description'],re.S).group(1)
        item['tmp'] = json_data

    def _color(self, colors, item, **kwargs):
        item['color'] = item['tmp']['title'].split(item['tmp']['type'])[0].strip().upper()

    def _prices(self, prices, item, **kwargs):
        saleprice = item['tmp']['price']
        listprice = item['tmp']['price_max']
        item['originsaleprice'] = str(saleprice)[0:-2] + '.' + str(saleprice)[-2:]
        item['originlistprice'] = str(listprice)[0:-2] + '.' + str(listprice)[-2:]

    def _images(self, images, item, **kwargs):
        images = item['tmp']['images']
        images_li = []
        for image in images:
            if image not in images_li:
                images_li.append('https:' + image)
        item['images'] = images_li
        item["cover"] = "https:" + item['tmp']['featured_image']

    def _sizes(self, sizes, item, **kwargs):
        osizes = item['tmp']['variants']
        sizes = []
        for size in osizes:                
            if size['available']:
                try:
                    sizes.append(size['public_title'].split(' ')[0])
                except:
                    if not size['public_title'] and item['category'] in ['a','b']:
                        sizes.append('IT')

        item['originsizes'] = sizes

    def _parse_images(self,response,**kwargs):
        images = response.xpath('//div[contains(@class,"enlarge_pane_contain")]/div[@class="enlarge_pane"]//div[@class="enlarge_contain"]/img/@src').extract()
        images_li = []
        for image in images:
            if image not in images_li:
                images_li.append("https:" + image)
        return images_li

_parser = Parser()


class Config(MerchantConfig):
    name = "luca"
    merchant = "Luca Faloni"

    path = dict(
        base = dict(
        ),
        plist=dict(
            list_url = _parser.list_url,
            items='//div[@class="color-selector collection-selector"]//ul',
            designer='./a/@title',
            link='./a/@href',
        ),
        product=OrderedDict([
            ('checkout', (
            '//script[@id="elevar-gtm-suite-config"]/text()',
            _parser.checkout)),
            ('sku', ('//script[@id="ProductJson-product-template-thumbnail"]/text()',_parser.sku)),
            ('color', ('//html', _parser.color)),
            ('prices', ('//html', _parser.prices)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
        ]),
        image = dict(
            method = _parser.parse_images,
        ),
        look = dict(
        ),
        swatch = dict(
        ),        
    )

    list_urls = dict(
        m = dict(
            a = [
                "https://lucafaloni.com/collections/leather?p=",
            ],
            c = [
                "https://lucafaloni.com/collections/cotton?",
                "https://lucafaloni.com/collections/silk-cashmere-knitwear?",
                "https://lucafaloni.com/collections/cashmere?",
                "https://lucafaloni.com/collections/linen?"
            ],
            s = [
               
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US=dict(
            language = 'EN',
            currency = 'USD',
            cookies = {
            'cart_currency': 'USD'
            }
        ),
        GB=dict(
            currency = 'GBP',
            cookies = {
            'cart_currency': 'GBP'
            }
        ),
        EU=dict(
            currency = 'EUR',
            cookies = {
            'cart_currency': 'EUR'
            }
        ),
    )
