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
        add_to_bag = checkout.extract_first()
        if "Add to bag" in add_to_bag:
            return False
        else:
            return True

    def _sku(self, sku_data, item, **kwargs):
        json_data = json.loads(sku_data.extract_first())
        item['tmp'] = json_data
        item['sku'] = json_data['id']

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['title'].split(' - ')[0].upper()

    def _designer(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['designer'] = json_data['brand']['name'].upper()
        item['color'] = json_data['color']
        item['description'] = json_data['description']

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['images']
        cover = "https:" + item['tmp']['featured_image']
        images = []
        for img in imgs:
            img = "https:" + img['src']
            if img not in images:
                images.append(img)

        item['images'] = images
        item['cover'] = cover if cover else images[0]

    def _sizes(self, res, item, **kwargs):
        osizes = item['tmp']['variants']
        sizes = []
        for osize in osizes:
            if osize['available']:
                sizes.append(osize['option2'])
        item['originsizes'] = sizes

    def _prices(self, prices, item, **kwargs):
        listprice = str(item['tmp']['price'])[:-2]
        saleprice = str(item['tmp']['compare_at_price'])[:-2]

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        imgs_data = json.loads(response.xpath('//script[@neptune-product-data]/text()').extract_first())
        imgs = imgs_data['images']
        images = []
        for img in imgs:
            img = "https:" + img['src']
            if img not in images:
                images.append(img)

        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'motherdenim'
    merchant = 'Mother Denim'

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="product-tile"]/div/',
            designer = './a[@class="thumb-link"]/@title',
            link = './a[@class="thumb-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[contains(@class,"product-item__foote")]/button[contains(@class,"quick-add__button")]/span/text()', _parser.checkout)),
            ('sku',('//script[@neptune-product-data]/text()', _parser.sku)),
            ('name', ('//html', _parser.name)),
            ('designer', ('//script[@type="application/ld+json"][contains(text(),"brand")]/text()', _parser.designer)),
            ('images',('//html', _parser.images)), 
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//html', _parser.sizes)),
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
        )

    list_urls = dict(
        m = dict(
            c = [
                'https://www.motherdenim.com/collections/mens'
            ],
        ),
        f = dict(
            a = [
                'https://www.motherdenim.com/collections/scarves-hats?page={}'
            ],
            b = [
                'https://www.motherdenim.com/collections/bags-wallets?page={}'
            ],
            c = [
                'https://www.motherdenim.com/collections/all-collection?page={}',
                'https://www.motherdenim.com/collections/accessories-socks?page={}'
            ],
            s = [
                'https://www.motherdenim.com/collections/shoes?page={}'
            ],
        ),
    )


    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
        ),
        )

