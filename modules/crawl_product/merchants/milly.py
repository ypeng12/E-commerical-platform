from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "add to bag" in checkout.extract_first().lower():
            return False
        else:
            return True

    def _sku(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        item['sku'] = json_data['featured_image'].split('_1.jpg')[0].split('/')[-1]

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['title'].upper()
        item['designer'] = item['tmp']['vendor']
        item['color'] = item['tmp']['variants'][0]['option1']
        item['description'] = item['tmp']['description'].replace('<p>','').replace('<>')

    def _images(self, res, item, **kwargs):
        images = item['tmp']['images']
        image_li = []
        for image in images:
            if "https" not in image:
                image_li.append("https:" + image)
        item['images'] = image_li
        item['cover'] = "htpps:" + item['tmp']['featured_image']

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('./span[contains(@class,"product-price--old")]/text()').extract_first()
        saleprice = res.xpath('./span[contains(@class,"product-price--current")]/text()').extract_first()
        item["originlistprice"] = listprice if listprice else saleprice
        item["originsaleprice"] = saleprice

    def _sizes(self,res,item,**kwargs):
        size_li = []
        for size in item['tmp']['variants']:
            if size['available']:
                size_li.append(size['option2'])
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="application/ld+json"][contains(text(),"image")]/text()').extract_first())
        return data['image']

    def _page_num(self, data, **kwargs):
        return 5

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

_parser = Parser()

class Config(MerchantConfig):
    name = "milly"
    merchant = "Milly"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[@class="b-product-hover_box js-product-hover_box"]',
            designer = './a/@aria-label',
            link = './a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//button[@id="add-to-cart"]/span[@id="add-to-cart-text"]/text()',_parser.checkout)),
            ('sku', ('//script[@id="product__json"]/text()', _parser.sku)),
            ('name', ('//html', _parser.name)),
            ('images', ('//html', _parser.images)),
            ('price', ('//span[@class="product-header__pricing"]', _parser.prices)),
            ('sizes', ('//ul[@class="js-swatches b-swatches_size"]/li/a[contains(@data-togglerhover-slider,"n-stock-msg")]/text()', _parser.sizes)),
        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
            'https://www.milly.com/collections/accessories'
            ],
            c = [
            'https://www.milly.com/collections/clothing'
            ],
        ),
        k = dict(
            c = [
            'https://www.milly.com/collections/milly-minis'
            ],
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',
        ),
        GB=dict(
            currency='GBP',
            discurrency='USD'
        ),
    )