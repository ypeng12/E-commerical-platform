from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _name(self, response, item, **kwargs):
        json_data = json.loads(response.extract_first())
        item['name'] = json_data['title']
        item['designer'] = json_data['vendor'].upper()
        item['tmp'] = json_data

    def _parse_multi_items(self, response, item, **kwargs):
        img_li = []
        imgs = response.xpath('//div[contains(@class,"gallery__thumbnails")]/span[@data-media-type="image"]/img/@src').extract()
        for img in imgs:
            img = "https:" + img.replace('_200x', '_800x')
            img_li.append(img)

        json_data = item['tmp']
        rid = str(json_data['id'])

        for variant in json_data['variants']:
            if variant['available']:
                item_color = deepcopy(item)
                item_color['sku'] = rid + '_' + str(variant['id'])
                item_color['color'] = variant['title']
                item_color['images'] = ["https:" + variant['featured_image']['src']] if variant['featured_image'] else img_li

                item_color['cover'] = item_color['images'][0]

            yield item_color

    def _description(self, res, item, **kwargs):
        description = res.extract_first()
        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = ['IT']

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('./span[contains(@class,"product__price")]/text()').extract_first()
        saleprice = res.xpath('./span[contains(@class,"product__price--old")]/text()').extract_first()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice if saleprice else listprice


    def _page_num(self, data, **kwargs):
        page_num = data.strip()
        return int(page_num)

    def _parse_images(self, response, **kwargs):
        img_li = json.loads(response.xpath('//script[@type="application/ld+json"][2]/text()').extract_first())
        images = []
        for img in img_li['images']:
            if img not in images:
                images.append(img)
        return images

_parser = Parser()



class Config(MerchantConfig):
    name = 'axiology'
    merchant = "Axiology"
    url_split = False
    merchant_headers = {'User-Agent':'ModeSensBotAxiology20231207'}

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="o-pagination__li o-pagination__number--next"]/text()',_parser.page_num),
            items = '//div[@class="row"]//div[@class="card__buttons"]',
            designer = './/a[@class="card__title"]/text()',
            link = './/div[@class="card__buttons"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-original-text="Add to cart"]', _parser.checkout)),
            ('name', ('//script[@type="application/json"][@sa-product-json]/text()', _parser.name)),
            ('description', ('//div[contains(@class,"accordion__item--content")]/p/text()', _parser.description)),
            ('price', ('//div[contains(@class,"product__price--holder")]', _parser.images)),
            ('sizes', ('//li[@class="c-pwa-radio-boxes__item c-pwa-radio-boxes__item--default"]//label[not(contains(@class,"is-back-in-stock-eligible"))]/text()', _parser.sizes)),
            ]),
        look = dict(
            ),
        size_info = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),

        )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            e = [
                'https://axiologybeauty.com/collections/all',
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
            area = 'EU',
            currency = 'GBP',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD', 
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
            area = 'EU',
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        )