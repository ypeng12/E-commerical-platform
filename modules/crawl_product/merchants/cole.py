from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        if "add to bag" in res.extract_first().lower():
            return False
        else:
            return True

    def _name(self,res,item,**kwargs):
        item['name'] = res.extract_first()
        item['designer'] = 'COLE HAAN'

    def _description(self, desc, item, **kwargs):
        descriptions = desc.extract()
        desc_li = []
        for desc in descriptions:
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _prices(self, res, item, **kwargs):
        originlistprice = res.xpath('.//span[@class="strike-through list"]/span/text()').extract_first()
        originsaleprice = res.xpath('.//span[@class="sales"]/span/text()').extract_first()
        item['originsaleprice'] = originsaleprice
        item['originlistprice'] = originlistprice if originlistprice else originsaleprice

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in images.extract():
            if image not in image_li:
                image_li.append(image)
        item["images"] = image_li
        item["cover"] = image_li[0]

    def _sizes(self,res,item,**kwargs):
        sizes = res.extract()
        sizes_li = []
        for size in sizes:
            if size.strip():
                sizes_li.append(size.strip())
        item["originsizes"] = sizes_li

    def _parse_images(self,response,**kwargs):
        images = json.loads(response.xpath('//div[contains(@class,"primary-images")]//div[contains(@class,"zoom")]/img/@src').extract())
        images_li = []
        for image in images:
            images_li.append(image)
        return images_li

    def _parse_num(self,pages, **kwargs):
        pages = pages.split('products')[0].strip()
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(start=0*i,sz=(i+1)*20)
        return url

_parser = Parser()


class Config(MerchantConfig):
    name = "cole"
    merchant = "Cole Haan"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = '//div[contains(@class,"plp-loadall-btn")]/div/button/span[contains(text(),"products")]/text()',
            list_url = _parser.list_url,
            items = '//div[@class="product"]',
            designer = './div/div/span/text()',
            link = './div[@class="product-tile"]/@data-monetate-producturl',
        ),
        product = OrderedDict([
            ('checkout',('//button[contains(@class,"add-to-cart-buy-bar")]/text()',_parser.checkout)),
            ('sku', '//span[@itemprop="productID"]/text()'),
            ('name', ('//h1[@class="product-name"]/text()', _parser.name)),
            ('color','//label[@class="color"]/span[@class="selected-attr"]/text()',),
            ('description', ('//div[@class="details-wrapper"]/ul/li/text()', _parser.description)),
            ('images', ('//div[contains(@class,"primary-images")]//div[contains(@class,"zoom")]/img/@src', _parser.images)),
            ('price', ('//div[@class="price"]', _parser.prices)),
            ('sizes', ('//div[@data-attr="size"]/div/a[not(contains(@class,"unselectable"))]/text()', _parser.sizes)),
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
               "https://www.colehaan.com/womens-accessories-hats",
               "https://www.colehaan.com/womens-accessories-sunglasses"
                ],
            b = [
                "https://www.colehaan.com/womens-handbags",
                "https://www.colehaan.com/womens-wallets"
                ],
            c = [
                "https://www.colehaan.com/womens-essentials"
            ],
            s = [
                "https://www.colehaan.com/womens-shoes?https://www.colehaan.com/womens-shoes=undefined&start={start}&sz={num}"
            ],
        ),
        m = dict(
            a = [
                "https://www.colehaan.com/mens-accessories-belts",
                "https://www.colehaan.com/mens-accessories-hats"
            ],
            b = [
                "https://www.colehaan.com/mens-bags",
                "https://www.colehaan.com/mens-accessories-wallets"
            ],
            c = [
                "https://www.colehaan.com/mens-apparelandouterwear"
            ],
            s = [
               "https://www.colehaan.com/womens-shoes"
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
        ),
    )