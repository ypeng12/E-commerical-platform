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

    def _sku(self, sku_data, item, **kwargs):
        json_data = json.loads(sku_data.extract_first())
        item['sku'] = json_data['sku'].split('-')[0]
        item['name'] = json_data['name'].upper()
        item['designer'] = json_data['brand']['name']
        item['description'] = json_data['description']

    def _images(self, res, item, **kwargs):
        imgs = res.extract()
        images = []
        for img in imgs:
            img = "https:" + img
            if img not in images:
                images.append(img)

        item['images'] = images
        item['cover'] = images[0]

    def _sizes(self, res, item, **kwargs):
        osizes = res.extract()
        sizes = []
        for osize in osizes:
            if "SOLD OUT" not in osize:
                sizes.append(osize.split(' - ')[0])
        item['originsizes'] = sizes

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('./div[@class="price__regular"]//span[contains(@class,"price-item--regular")]/span/text()').extract_first()
        saleprice = res.xpath('.//span[contains(@class,"price-item--sale")]/span/text()').extract_first()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        imgs_data = json.loads(response.xpath('//div[contains(@class,"product__media")]/img/@src').extract_first())
        images = []
        for img in imgs:
            img = "https:" + img
            if img not in images:
                images.append(img)

        return images

    def _page_num(self, data, **kwargs):
        pages = 2
        return pages

    def _list_url(self, i, response_url, **kwargs):
        return response_url + str(i)


_parser = Parser()


class Config(MerchantConfig):
    name = 'sarahflint'
    merchant = 'Sarah Flint'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[@class="card__information"]/h3',
            designer = './a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product-form__buttons"]/button[@name="add"]/span', _parser.checkout)),
            ('sku',('//script[@type="application/ld+json"][contains(text(),"description")]/text()', _parser.sku)),
            ('color', '//div[@class="select"]/select[@name="options[Color]"]/option/text()'),
            ('images',('//div[contains(@class,"product__media")]/img/@src', _parser.images)), 
            ('prices', ('//div[@class="price__container"]', _parser.prices)),
            ('sizes',('//div[@class="select"]/select[@name="options[Size]"]/option/text()', _parser.sizes)),
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
        f = dict(
            s = [
                'https://www.sarahflint.com/collections/boots?page={}'
            ],
        ),
    )


    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
        ),
        )

