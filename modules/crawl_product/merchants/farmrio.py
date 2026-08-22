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
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_data = 100
        count = int(num_data)
        return count

    def _list_url(self, i, response_url, **kwargs):
        num = i
        url = response_url.split('?')[0] + '?page=%s'%num
        return url

    def _sku(self, sku_data, item, **kwargs):
        code = sku_data.extract_first()
        item['sku'] = code if code and code.isdigit() else ''
        item['designer'] = 'FARM RIO'

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            if "http" not in img:
                img = "https:" + img

            if img not in images:
                images.append(img)
            if not cover and "_01_" in img:
                cover = img
        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, res, item, **kwargs):
        avail_sizes = res.xpath('.//label[contains(@class,"product-form__label")]/span/text()').extract()
        item['originsizes'] = []
        for size in avail_sizes:
            item['originsizes'].append(size.strip())

    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = prices.xpath('.//div[@class="price__sale"]//span[contains(@class,"price-item--sale")]/text()').extract()[0].strip()
        item['originlistprice'] = prices.xpath('.//div[@class="price__sale"]//span/s[contains(@class,"price-item--regular")]/text() | .//div[@class="price__sale"]//span[contains(@class,"price-item--regular")]/text()').extract()[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"product__media")]/img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'farmrio'
    merchant = 'FARM Rio'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="image-carousel"]',
            designer = './/html',
            link = './a[1]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product-form__buttons"]/button[@name="add"]/span', _parser.checkout)),
            ('sku',('//span[@class="product_id"]/text()',_parser.sku)),
            ('images',('//div[contains(@class,"product__media")]/img/@src',_parser.images)), 
            ('name', '//h1[contains(@class,"product__title")]/text()'),
            ('color', '//ul[@data-name="color"]/li/text()'),
            ('description', ('//div[contains(@class,"accordion__content")]/p/text()',_parser.description)),
            ('prices', ('//div[contains(@class,"price")]', _parser.prices)),
            ('sizes',('//fieldset[contains(@class,"product-form__input--size")]',_parser.sizes)),
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
        ),
        f = dict(
            a = [
                'https://www.farmrio.com/collections/accessories',
            ],
            b = [
                "https://www.farmrio.com/collections/handbags",
            ],
            c = [
                "https://www.farmrio.com/collections/dresses?page=1",
                "https://www.farmrio.com/collections/tops",
                "https://www.farmrio.com/collections/jumpsuits",
                "https://www.farmrio.com/collections/skirts-shorts",
                "https://www.farmrio.com/collections/solids",
                "https://www.farmrio.com/collections/pants",
                "https://www.farmrio.com/collections/sweaters-knits",
                "https://www.farmrio.com/collections/denim",
                "https://www.farmrio.com/collections/outerwear",
                "https://www.farmrio.com/collections/swimwear",
            ],
            s = [
                "https://www.farmrio.com/collections/shoes",
            ],
        ),
    )


    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
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
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        )
        )


