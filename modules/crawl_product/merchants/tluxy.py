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
        if 'Add to cart' in res.extract_first():
            return False
        else:
            return True

    def _sku(self,res,item,**kwargs):
        item["sku"] = res.extract_first().split('Product Code: ')[-1].strip().upper()

    def _name(self, res, item, **kwargs):
        data = json.loads(res.extract_first())
        item['tmp'] = data
        item['name'] = data['name'].upper()
        item['designer'] = data['brand'].upper()
        item['description'] = data['description']

    def _color(self,res,item,**kwargs):
        item["color"] = res.extract_first().strip()

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span[contains(@class, "product__price--compare")]/text()').extract_first()
        saleprice = prices.xpath('.//span[contains(@class, "on-sale")]/text()').extract_first()
        if saleprice is not None:
            item["originsaleprice"] = saleprice.strip()
        else:
            item["originsaleprice"] = listprice
        item["originlistprice"] = listprice

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in images.extract():
            image = "https:" + image
            if image not in image_li:
                image_li.append(image)
        item["images"] = image_li
        item["cover"] = image_li[0]

    def _sizes(self, res, item, **kwargs):
        sizes_data = json.loads(res.extract_first())
        sizes_li = []
        for sizes in sizes_data:
            if sizes['available']:
                sizes_li.append(sizes['option1'])
        item["originsizes"] = sizes_li

    def _parse_num(self,pages,**kwargs):
        # pages = pages/24+1
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('&sz=1', '&sz=%s'%i)
        return url

    def _page_num(self, data, **kwargs):
        page = data.extract_first()
        return page

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

    def _parse_images(self, response, **kwargs):
        images = []
        for img in response.xpath('//div[@class="product__thumb-item"]/div/a/@href').extract():
            img = "https:" + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()

class Config(MerchantConfig):
    name = "Tluxy"
    merchant = "tluxy"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = ('//div[@class="pagination"]//span[position()=5]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="grid-product__content"]',
            designer = './/div[@class="grid-product__vendor"]/text()',
            link = './a/@href',
        ),

        product = OrderedDict([
            ('checkout', ('//span[@data-default-text="Add to cart"]/text()', _parser.checkout)),
            ('sku', ('//li[contains(text(),"Product Code")]/text()', _parser.sku)),
            ('name', ('//div[@id="shopify-section-product-template"]/div[@class="product-section"]/script/text()', _parser.name)),
            ('color',('//select[@data-index="option2"]/option/text()',_parser.color)),
            ('description','//div[@id="design"]/div[@class="accordion-body"]/p/text()'),
            ('price', ('//div[@class="product-single__meta"]', _parser.prices)),
            ('images', ('//div[@class="product__thumb-item"]/div/a/@href', _parser.images)),
            ('sizes', ('//textarea[@aria-label="Product JSON"]/text()', _parser.sizes)),
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
        f = dict(
            a = [
                "https://tluxy.it/collections/women-accessories?page={}"               
                ],
            b = [
                "https://tluxy.it/collections/women-bags?page={}",
                ],
            c = [
                "https://tluxy.it/collections/women-clothing?page={}",
            ],
            s = [
                "https://tluxy.it/collections/women-shoes?page={}"
            ],
        ),
        m = dict(
            a = [
                "https://tluxy.it/collections/men-accessories?page={}"               
                ],
            b = [
                "https://tluxy.it/collections/men-bag?page={}",
                ],
            c = [
                "https://tluxy.it/collections/men-clothing-1?page={}",
            ],
            s = [
                "https://tluxy.it/collections/men-shoes?page={}"
            ],
        )
    )

    countries = dict(
        DE = dict(
            language = 'EN',
        )
    )
