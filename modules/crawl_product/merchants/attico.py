from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        if res.extract_first():
            return False
        else:
            return True

    def _sku(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first())
        item['sku'] = str(json_data['sku'])

        item['designer'] = 'ATTICO'
        item['name'] = json_data['name'].upper()
        item['color'] = json_data['color']
        item['tmp'] = json_data

    def _images(self, res, item, **kwargs):
        item['images'] = item['tmp']['image']

    def _prices(self, res, item, **kwargs):
        originlistprice = res.xpath('./span[contains(@class,"js-product_price-standard")]/text()').extract_first()
        originsaleprice = res.xpath('./span[contains(@class,"b-product_price-sales")]/text()').extract_first()
        item['originsaleprice'] = originsaleprice if originsaleprice else originlistprice
        item['originlistprice'] = originlistprice

    def _sizes(self, res, item, **kwargs):
        sizes_data = res.extract()
        sizes_li = set()
        for size in sizes_data:
            if size.strip():
                sizes_li.add(size.strip())
        item['originsizes'] = list(sizes_li)

    def _parse_images(self,response,**kwargs):
        images_json = json.loads(response.xpath('//script[@type="application/ld+json"][contains(text(),"Product")]/text()').extract_first())
        return images_json['image']

    def _page_num(self,pages,**kwargs):
        # pages = pages/24+1
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + str(i)
        return url

_parser = Parser()

class Config(MerchantConfig):
    name = "attico"
    merchant = "The Attico"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[contains(@class,"b-product_tile js-product_tile")]',
            designer = './@data-brand/text()',
            link = './div[@class="b-product-hover_box js-product-hover_box"]/div[@class="b-product_image-container js-image-container"]/a/@href',
        ),
        product = OrderedDict([
            ('checkout', ('//button[@title="Add to bag"]/text()', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"][contains(text(),"Product")]/text()', _parser.sku)),
            ('description', '//div[@class="b-product_long_description"]/text()'),
            ('images', ('//html', _parser.images)),
            ('prices', ('//div[@class="b-product_price js-product_price"]', _parser.prices)),
            ('sizes', ('//div[@class="b-variation-value Size"]/ul/li/a/text()', _parser.sizes)),
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
               "https://www.theattico.com/en/shop/accessories/?page="
                ],
            b = [
                "https://www.theattico.com/en/shop/bags/?page=",
                ],
            c = [
                "https://www.theattico.com/en/shop/ready-to-wear/?page="
            ],
            s = [
                "https://www.theattico.com/en/shop/shoes/?page="
            ],
        ),

        params = dict(
            page = 1,
            ),
        )

    countries = dict(
        US=dict(
            language = 'EN',
            currency = 'USD',
        ),
    )