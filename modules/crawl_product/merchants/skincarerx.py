from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract()
        if not checkout:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        data = json.loads(res.extract_first())
        item['sku'] = data['sku']

        item['name'] = data['name'].upper()
        item['designer'] = data['brand']['name'].upper()
        item['description'] = data['description']
        item['tmp'] = data

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./span[@class="productPrice_rrpPriceInfo"]/p/text()').extract_first()
        saleprice = prices.xpath('./p[contains(@class,"productPrice_price")]/text()').extract_first()
        if listprice is not None:
            item["originlistprice"] = listprice.strip().strip("MSRP:")
        else:
            item["originlistprice"] = saleprice.strip()
        item["originsaleprice"] = saleprice.strip()

    def _images(self, images, item, **kwargs):
        item["images"] = item['tmp']['image']

    def _sizes(self,res,item,**kwargs):
        item["originsizes"] = ['IT']

    def _parse_images(self, response, **kwargs):
        images = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        return images['image']

    def page_num(self, data, **kwargs):
        nums = data.strip()
        return int(nums.split('results')[0].strip())//48+1

    def _list_url(self, i, response_url, **kwargs):
        return response_url + str(i)

_parser = Parser()


class Config(MerchantConfig):
    name = "skincarerx"
    merchant = "SkincareRX"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="responsiveProductListHeader_resultsCount"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="productBlock_imageLinkWrapper"]',
            designer = 'SkincareRX',
            link = './a[@class="productBlock_link"]/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[@data-component="productAddToBasket"]/text()',_parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('price', ('//span[@class="productPrice_priceInfo"]', _parser.prices)),
            ('images', ('//button[@class="product-gallery-nav__item"]/img/@src', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="care"]/div[@class="accordion-body"]/p/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            e = [
                'https://www.skincarerx.com/cosmetics/view-all.list?pageNumber='
            ],
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )