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

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first().upper().split(' - ')[0]
        item['color'] = res.extract_first().upper().split(' - ')[-1]
        item['designer'] = 'CHARLES TYRWHITT'

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first().strip()

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./b/span[@aria-hidden="true"]/text()').extract_first()
        saleprice = prices.xpath('./span[contains(@class,"js-thumb-now-price")]/span[@aria-hidden="true"]/text()').extract_first()

        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _images(self, res, item, **kwargs):
        image_li = []
        for image in res.extract():
            if image not in image_li:
                image_li.append(image.strip())
        item["images"] = image_li
        item["cover"] = image_li[0]

    def _sizes(self,res,item,**kwargs):
        sizes = res.extract()
        item["originsizes"] = [size.strip() for size in sizes if size]

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "charles"
    merchant = "Charles Tyrwhitt"

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[contains(@class,"product-tile__img")]',
            designer = './p/text()',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//span[@class="js-product-markup-offer-availability"] | //button[@data-tracking="cart-add-to-bag"]/span',_parser.checkout)),
            ('sku', '//span[@class="js-product-markup-sku"]/text()'),
            ('name', ('//div[@class="d-none"]/span[@class="js-product-markup-name"]/text()', _parser.name)),
            ('description','//div[@class="d-none"]//span[@class="js-product-markup-description"]/text()'),
            ('price', ('//div[contains(@class,"price")]', _parser.prices)),
            ('images', ('//div[contains(@class,"pdpimage__item")]//img[contains(@class,"pdp-main__image")]/@src', _parser.images)),
            ('sizes', ('//div[@data-var-attr-id="collarSize"]/ul/li/div/text()', _parser.sizes)),
        ]),
        image=dict(
            image_path = '//div[contains(@class,"pdpimage__item")]//img[contains(@class,"pdp-main__image")]/@src',
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[contains(@class,"pdp-main__benefits")]/ul/li/text()',
        ),
    )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.charlestyrwhitt.com/us/mens-accessories/?sz=150&start=0'
            ],
            c = [
                'https://www.charlestyrwhitt.com/us/mens-shirts/?sz=150&start=0',
                'https://www.charlestyrwhitt.com/us/mens-sweaters/?sz=150&start=0',
                'https://www.charlestyrwhitt.com/us/mens-pants/?sz=150&start=0',
                'https://www.charlestyrwhitt.com/us/loungewear/?sz=150&start=0',
                'https://www.charlestyrwhitt.com/us/mens-suits/?sz=150&start=0',
                'https://www.charlestyrwhitt.com/us/mens-blazers/?sz=150&start=0',
                'https://www.charlestyrwhitt.com/us/mens-jackets-and-coats/?sz=150&start=0',
            ],
            s = [
                'https://www.charlestyrwhitt.com/us/mens-shoes/?sz=150&start=0'
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )