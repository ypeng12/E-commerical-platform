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
            if not cover and "-1.jpg" in img.lower():
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

        item['sku'] = sku_data.extract_first().strip().replace(" ",'') +"_" +item["color"]

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip().split("/")[0].strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        try:
            item['color'] = sizes[-1].split("/")[-1].split("-")[0].strip().upper()
        except:
            item['color'] = ""

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="was"]/span[@class="money"]/text()').extract()[0].replace("AUD",'')
            item['originsaleprice'] = prices.xpath('.//span[@class="product-price"]/span[@class="money"]/text()').extract()[0].replace("AUD",'')
        except:

            item['originsaleprice'] =prices.xpath('.//span[@class="product-price"]//span[@class="money"]/text()').extract_first().replace("AUD",'')
            item['originlistprice'] =prices.xpath('.//span[@class="product-price"]//span[@class="money"]/text()').extract_first().replace("AUD",'')

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//a[@data-slide-id="zoom"]/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'estro'
    merchant = 'Estro'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination"]/span[5]/a/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-info-inner"]',
            designer = './/a/span[@class="prod-vendor"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//input[@id="addToCart"]', _parser.checkout)),
            ('name','//h1[@itemprop="name"]/text()'),
            ('designer','//div[@id="content"]//h3/a/text()'),
            ('description', ('//div[@class="description"]//text()',_parser.description)),
            ('sizes',('//select[contains(@id,"product")]/option/text()',_parser.sizes)),
            ('prices', ('//p[@id="product-price"]', _parser.prices)),
            ('images',('//a[@data-slide-id="zoom"]/@href',_parser.images)),
            ('sku',('//div[@class="select"]//option/@data-sku',_parser.sku)),
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
                "https://www.estro.com.au/collections/men-accessories?page=",
            ],
            b = [
                "https://www.estro.com.au/collections/men-bag?page=",
            ],
            c = [
                "https://www.estro.com.au/collections/men-clothing-1?page=",
                "https://www.estro.com.au/collections/underwear?page=",
            ],
            s = [
                "https://www.estro.com.au/collections/men-shoes?page=",
            ],
        ),
        f = dict(
            a = [
                "https://www.estro.com.au/collections/women-accessories?page=",
                "https://www.estro.com.au/collections/jewelry?page="
                ],
            b = [
                "https://www.estro.com.au/collections/women-bags?page=",
            ],
            c = [
                "https://www.estro.com.au/collections/women-clothing?page=",
                "https://www.estro.com.au/collections/lingerie?page="
            ],
            s = [
                "https://www.estro.com.au/collections/women-shoes?page=",
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
            country_url = '.com.au/',
            discurrency = "AUD",
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = "AUD",
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = "AUD",
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = "AUD",
        ),
        SG = dict( 
            currency = 'SGD',
            discurrency = "AUD",
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = "AUD",
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = "AUD",
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = "AUD",
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = "AUD",
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = "AUD",
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = "AUD",
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = "AUD",
        ),
        )

        


