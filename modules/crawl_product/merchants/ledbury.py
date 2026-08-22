from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first().split('-')[-1].strip()
        item['designer'] = 'LEDBURY'
        item['color'] = ''

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        if not sizes:
            sizes = ['IT']
        item['originsizes'] = []
        for size in sizes:
            size = size.split('-')[0].upper().replace('CLASSIC','').replace('SLIM','').replace('TAILORED','').strip().split('/')
            size = 'x'.join(size).strip().replace('x  x','x').replace('x 1','1').split('x')[0].strip()
            if size not in item['originsizes']:
                item['originsizes'].append(size.strip())

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="price theme-money"]/text()').extract_first()
        listPrice = prices.xpath('.//span[@class="was-price theme-money"]/text()').extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else salePrice

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description

    def _images(self, images, item, **kwargs):
        images = images.extract()
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append(img.replace('//cdn.','https://cdn.'))
        item['images'] = img_li
        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//a[@style="pointer-events:none;"]/@href').extract()
        image_li = []
        for img in images:
            if 'http' not in img:
                img = 'https:' + img
            if img not in image_li:
                image_li.append(img)

        return image_li


_parser = Parser()


class Config(MerchantConfig):
    name = 'ledbury'
    merchant = 'Ledbury'

    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//div[contains(@class,"partial--product")]',
            designer = './/div[@class="product_grid_brand"]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add_to_bag_btn"]', _parser.checkout)),
            ('sku', ('//script[contains(@id,"ProductJson")]/@id', _parser.sku)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('description', ('//div[@class="product-desc-block prod-desc"]//div[@class="product-desc-block-content"]/text()',_parser.description)),
            ('image',('//a[@style="pointer-events:none;"]/@href',_parser.images)),
            ('sizes',('//select[@name="id"]/option/text()',_parser.sizes)),
            ('prices',('//html',_parser.prices)),
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        designer = dict(
            ),
        )



    list_urls = dict(
        f = dict(
            a = [

            ],
        ),
        m = dict(
            a = [
                'https://www.ledbury.com/collections/all-accessories?p=',
            ],
            b = [
            ],
            c = [
                "https://www.ledbury.com/collections/all-shirts?p=",
                "https://www.ledbury.com/collections/all-clothing?p="

            ],
            s = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),


    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = '.com/us/',
            currency_sign = '$',
            ),

        )

        


