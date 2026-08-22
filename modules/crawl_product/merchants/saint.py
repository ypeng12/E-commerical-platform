from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "Add to bag" in checkout.extract_first():
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data['product']
        item['sku'] = json_data['product']['id']
        item['name'] = item['tmp']['title'].split(' - ')[0].upper()
        item['designer'] = item['tmp']['vendor']
        item['description'] = item['tmp']['description']
        item['color'] = item['tmp']['title'].split(' - ')[1]

    def _images(self, images, item, **kwargs):
        image_li = []
        images = item['tmp']['images']
        for image in images:
            if 'https' not in image:
                image_li.append('https:' + image)
        item['images'] = image_li
        item['cover'] = item['tmp']['featured_image']

    def _sizes(self, res, item, **kwargs):
        sizes = item['tmp']['variants']
        size_li = []
        for size in sizes:
            if size['available']:
                size_li.append(size['option1'])
        item['originsizes'] = size_li

        saleprice = item['tmp']['price']
        listprice = item['tmp']['price_max']
        item["originsaleprice"] = str(saleprice)[0:-2] + '.' + str(saleprice)[-2:]
        item["originlistprice"] = str(listprice)[0:-2] + '.' + str(listprice)[-2:]

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@data-media-type="image"]/div/noscript/img/@src').extract()
        image_li = []
        for image in images:
            if 'https' not in image:
                image_li.append('https:' + image)
        return image_li

    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info.strip(' - '))
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "saint"
    merchant = "Saint + Sofia"

    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = '//div[@class="CollectionInner__Products"]//div[@class="ProductItem__Info ProductItem__Info--center"]/h2',
            designer = './a/text()',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[@data-action="selecting-options"]/span/text()',_parser.checkout)),
            ('sku', ('//script[@data-product-json]/text()', _parser.sku)),
            ('size', ('//script[@data-product-json]/text()', _parser.sizes)),
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
            size_info_path = '//div[@class="row_tab-container"][contains(@data-tab-title,"Care")]/div/p/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://uk.saintandsofia.com/collections/womens-scarves',
                'https://uk.saintandsofia.com/collections/womens-jewellery'
            ],
            b = [
                'https://uk.saintandsofia.com/collections/womens-handbags',
            ],
            c = [
                'https://uk.saintandsofia.com/collections/womens-trousers',
                'https://uk.saintandsofia.com/collections/womens-dresses',
                'https://uk.saintandsofia.com/collections/womens-skirts',
                'https://uk.saintandsofia.com/collections/womens-sweaters-jumpers',
                'https://uk.saintandsofia.com/collections/womens-knitwear',
                'https://uk.saintandsofia.com/collections/womens-tshirts-tops',
                'https://uk.saintandsofia.com/collections/womens-blazers',
                'https://uk.saintandsofia.com/collections/womens-jackets',
                'https://uk.saintandsofia.com/collections/womens-coats',
            ],
            s = [
                'https://uk.saintandsofia.com/collections/womens-trainers',
                'https://uk.saintandsofia.com/collections/womens-boots'
                'https://uk.saintandsofia.com/collections/womens-sandals-slides'
            ]
        ),
        m = dict(
            c = [
                'https://uk.saintandsofia.com/collections/menswear',
            ],
        ),
        u = dict(
            h = [
                'https://uk.saintandsofia.com/collections/fashion-books'
            ]
        ),
    )

    countries = dict(
        GB=dict(
            currency='GBP',       
        ),
    )