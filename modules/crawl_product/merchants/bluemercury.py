from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser,parseProdLink
from utils.cfg import *
import time
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        product_id = data.xpath('.//button[@data-swaction="addToWishlist"]/@data-product-id').extract_first()
        variants_data = json.loads(data.xpath('//script[@type="application/json"][contains(text(),"productData")]/text()').extract_first())
        variant_id = variants_data['variantData']['barcode']
        item['sku'] = str(product_id) + '_' + str(variant_id)

    def _name(self, data, item, **kwargs):
        json_data = json.loads(data.extract_first())
        item['name'] = json_data['name']
        item['designer'] = json_data['brand']['name'].upper()
        item['description'] = json_data['description']
        item['color'] = json_data['offers'][0]['name']

    def _prices(self, data, item, **kwargs):
        listprice = data.xpath('./div/span/text()').extract_first()
        saleprice = data.xpath('./div/span/text()').extract_first()
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = ['OneSize']

    def _images(self, res, item, **kwargs):
        imgs = res.extract()
        item['images'] = []
        for img in imgs:
            item['images'].append(img)

        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
        images = []
        for img in imgs:
            images.append(img)

        return images

_parser = Parser()


class Config(MerchantConfig):
    name = "bluemercury"
    merchant = 'Bluemercury'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            items = '//li[@class="product-grid_item"]',
            designer = './/span[@class="product-card_brand"]/text()',
            link = './/a[@class="product-card_link js-product-card_link"]/@href',
            ),
        product = OrderedDict([
            ('checkout',('//div[@class="AddToCart__Add__Text"]/span/@data-bag-desc', _parser.checkout)),
            ('sku',('//html', _parser.sku)),
            ('name', ('//script[@type="application/ld+json"][contains(text(),"offers")]/text()', _parser.name)),
            ('prices', ('//div[@class="MainProductPrice__regular"]', _parser.prices)),
            ('sizes',('//html',_parser.sizes)),
            ('images',('//meta[@property="og:image"]/@content',_parser.images)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//script[contains(text(),"PRELOADED_STATE")]/text()',
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        blog = dict(
            ),
        checknum = dict(
            ),

        )

    list_urls = dict(
        f = dict(
            a = [
                'https://bluemercury.com/collections/best-sellers',
            ]
        )
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = '$',
        ),

        )
