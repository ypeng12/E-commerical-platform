from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import unquote

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        sold_out = checkout.extract()
        if sold_out:
            return False
        else:
            return True

    def _designer(self,designer,item, **kwargs):
        item['designer'] = 'NEOSTRATA'
        item['color'] = ''

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('./span[@class="price-standard"]/text()').extract_first()
        saleprice = res.xpath('./span[@class="price-sales"]/text()').extract_first()

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _images(self, res, item, **kwargs):
        images_li = []
        images = res.extract()
        for i in images:
            if "https:" in i and i not in images_li:
                images_li.append(i)

        item["images"] = images_li
        item["cover"] = images_li[0]

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = ['One-Size']

    def _parse_images(self,response,**kwargs):
        images_li = []
        images = response.xpath('//div[@class="product-primary-image"]/a/@href').extract()
        for i in images:
            if "https:" in i and i not in images_li:
                images_li.append(i)

        return images_li

_parser = Parser()


class Config(MerchantConfig):
    name = "neostrata"
    merchant = "Neostrata"

    path = dict(
        plist = dict(
            items = '//div[@class="product-name"]',
            designer = './a/text()',
            link = './a/@href',
        ),
        product=OrderedDict([
            ('checkout', ('//button[@id="add-to-cart"]', _parser.checkout)),
            ('sku', '//div[@data-recid="pdp-pi-recommendations"]/@data-productid'),
            ('name', '//div[contains(@class,"product-detail")]/h1/text()'),
            ('designer', ('//html',_parser.designer)),
            ('description', '//div[@class="pdp-short-description"]/p/text()'),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
            ('images', ('//div[@class="product-primary-image"]/a/@href', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look=dict(
        ),
        swatch=dict(
        ),
    )
    list_urls = dict(
        f = dict(
            e = [
                "https://www.neostrata.com/products/new-and-now"
            ],

        params = dict(
            # TODO:

            ),
        ),

    )

    countries = dict(
        US=dict(
            language='EN',
            area='US',
            currency='USD',
        ),
        GB=dict(
            currency='GBP',
            duscurrency='USD',

        ),
    )