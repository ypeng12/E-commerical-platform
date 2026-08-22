from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        data = json.loads(res.extract_first())
        item['tmp'] = data
        pid = data['sku']
        code_image = data['image'][0].split('zoom/')[1].split('.JPG')[0].split('_')[0:2]
        if code_image[0] in pid:
            item['sku'] = '_'.join(code_image)
        else:
            item['sku'] = ''

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['name'].upper()
        item['color'] = item['tmp']['color']

        item['designer'] = item['tmp']['brand']['name']
        item['description'] = item['tmp']['description'].replace('<br>',' ')

    def _images(self, res, item, **kwargs):
        image_li = item['tmp']['image']
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('./span[contains(@class,"b-product_price-standard")]/text()').extract_first()
        saleprice = res.xpath('./span[contains(@class,"b-product_price-sales")]/text()').extract_first()
        item["originlistprice"] = listprice if listprice else saleprice
        item["originsaleprice"] = saleprice if saleprice else listprice

    def _sizes(self,res,item,**kwargs):
        size_li = []
        for size in res.extract():
            if size.strip():
                size_li.append(size.strip())
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
    name = "herno"
    merchant = "Herno"

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
            ('checkout',('//button[contains(@title,"Add to bag")]/text()',_parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"][contains(text(),"image")]/text()', _parser.sku)),
            ('name', ('//html', _parser.name)),
            ('images', ('//html', _parser.images)),
            ('price', ('//div[@class="b-product_price js-product_price"]', _parser.prices)),
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
                'https://us.herno.com/en/women/accessories/foulard/?page={}',
                'https://us.herno.com/en/women/accessories/neckpiece/?page={}',
                'https://us.herno.com/en/women/accessories/sleeves/?page={}',
            ],
            b = [
            ],
            c = [
                'https://us.herno.com/en/women/outerwear/?page={}',
                'https://us.herno.com/en/women/down-jackets/?page={}',
                'https://us.herno.com/en/women/knitwear/?page={}',
            ],
            s = [
                'https://us.herno.com/en/women/accessories/shoes/?page={}'
            ]
        ),
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
                'https://us.herno.com/en/men/outerwear/?page={}',
                'https://us.herno.com/en/men/down-jackets/?page={}',
                'https://us.herno.com/en/men/knitwear/?page={}',
            ],
            s = [
                'https://us.herno.com/en/men/accessories/shoes/?page={}'
            ]
        ),

        country_url_base = 'herno.com',
    )

    countries = dict(
        US=dict(
            currency='USD',
            country_url='us.herno.com'
        ),
        EU=dict(
            currency='EUR',
            country_url='herno.com'
        ),
    )