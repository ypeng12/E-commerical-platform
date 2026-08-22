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
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = 100
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i)
        url = response_url.split('?')[0] + '?page=%s'%(num)
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
            if not cover and "_FRONT.jpg" in img.lower():
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

    def _sku(self, sku_data, item, **kwargs):
        try:
            item["color"] = sku_data.xpath('//div[@id="frame-color-pr"]/text()').extract_first() + " ".join(sku_data.xpath('//div[@id="lens-color-pr"]//text()').extract()).strip().replace("  "," ").replace("  "," ").replace("  ","")
        except:
            item["color"] = ""
        sku = sku_data.xpath('//p[@class="product-single__sku"]/text()').extract_first().strip()
        item['sku'] = (sku + "_" + item["color"]) if item['color'] else sku

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip().split(" - ")[0])

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        if "COMING SOON" in item["color"]:
            item['originsizes'] = []

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[contains(@id,"ComparePrice-")]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[contains(@id,"ProductPrice")]/text()').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//span[contains(@id,"ProductPrice")]/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[contains(@id,"ProductPrice")]/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="starting-slide"]//noscript/img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'solstice'
    merchant = 'Solstice Sunglasses'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination"]/span[5]/a/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="grid-product__content"]',
            designer = './/div[@class="grid-product__meta"]/div[@class="grid-product__vendor"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//button[contains(@id,"AddToCart")]', _parser.checkout)),
            ('name','//h1[@class="h2 product-single__title"]/text()'),
            ('designer','//div[@class="product-single__vendor"]/text()'),
            ('images',('//div[@class="starting-slide"]//noscript/img/@src',_parser.images)),
            ('sku',('//html',_parser.sku)),
            ('description', ('//div[@id="des-content-pr"]//text()',_parser.description)),
            ('sizes',('////select[@name="id"]/option/text()',_parser.sizes)),
            ('prices', ('//html', _parser.prices)),
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
                "https://solsticesunglasses.com/collections/men?page=",
                "https://solsticesunglasses.com/collections/outlet/gender_men?page="
            ],
        ),
        f = dict(
            a = [
                "https://solsticesunglasses.com/collections/women?page=",
                "https://solsticesunglasses.com/collections/outlet/gender_women?page="
                ],

        params = dict(
            # TODO:

            ),
        ),

    )


    countries = dict(



        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '.com/',

            ),



        )

        


