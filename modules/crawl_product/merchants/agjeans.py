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
        if "Add to cart" in add_to_bag:
            return False
        else:
            return True

    def _sku(self, sku_data, item, **kwargs):
        json_data = json.loads(sku_data.extract_first())
        item['tmp'] = json_data
        item['sku'] = json_data['sku']

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['name']
        item['designer'] = item['tmp']['brand']['name']
        item['description'] = item['tmp']['description']
        item['color'] = ''

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            if "http" not in img:
                img = "https:" + img

            if img not in images:
                images.append(img)
            if not cover and "_1" in img:
                cover = img
        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]

    def _sizes(self, res, item, **kwargs):
        osizes = res.extract()
        sizes = []
        for osize in osizes:
            if osize.strip():
                sizes.append(osize)
        item['originsizes'] = sizes

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./span[@class="price-standard"]/text()').extract_first().strip()
        saleprice = prices.xpath('./span[contains(@class,"price-sales")]/text()').extract_first().strip()
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice if saleprice else listprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('.//div[@class="product-main-images"]//div[@class="slick-data"]/a/img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'agjeans'
    merchant = 'AG Jeans'

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="product-tile"]/div/',
            designer = './a[@class="thumb-link"]/@title',
            link = './a[@class="thumb-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product-add-to-cart"]/form/fieldset/legend/text()', _parser.checkout)),
            ('sku',('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('images',('//div[@class="product-main-images"]//div[@class="slick-data"]/a/img/@src', _parser.images)), 
            ('name', ('//html', _parser.name)),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
            ('sizes',('//li[@class="attribute size"]/div[@class="value"]/ul/li[@class="variation-group-value"]/a/span/text()', _parser.sizes)),
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
            a = [
                'https://www.agjeans.com/men/accessories/hats',
                'https://www.agjeans.com/men/accessories/belts',
                'https://www.agjeans.com/men/accessories/sunglasses',
            ],
            b = [
                'https://www.agjeans.com/men/accessories/bags',
            ],
            c = [
                'https://www.agjeans.com/men/clothing/denim',
                'https://www.agjeans.com/men/clothing/pants',
                'https://www.agjeans.com/men/clothing/tees',
                'https://www.agjeans.com/men/clothing/polos',
                'https://www.agjeans.com/men/clothing/shirts',
                'https://www.agjeans.com/men/clothing/jackets',
                'https://www.agjeans.com/men/clothing/outerwear',
                'https://www.agjeans.com/men/clothing/sweatshirts',
                'https://www.agjeans.com/men/clothing/sweatpants'
            ]
        ),
        f = dict(
            a = [
                'https://www.agjeans.com/women/accessories/hats',
                'https://www.agjeans.com/women/accessories/belts',
                'https://www.agjeans.com/women/accessories/sunglasses',
            ],
            b = [
                'https://www.agjeans.com/women/accessories/bags',
            ],
            c = [
                'https://www.agjeans.com/women/clothing/denim',
                'https://www.agjeans.com/women/clothing/pants'
                'https://www.agjeans.com/women/clothing/jackets',
                'https://www.agjeans.com/women/clothing/outerwear',
                'https://www.agjeans.com/women/clothing/tees-and-tanks',
                'https://www.agjeans.com/women/clothing/tops-and-shirts',
                'https://www.agjeans.com/women/clothing/dresses-and-more',
                'https://www.agjeans.com/women/clothing/sweatshirts',
                'https://www.agjeans.com/women/clothing/sweatpants',
            ],
        ),
    )


    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
        ),
        )


