from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from copy import deepcopy
from lxml import etree
import requests
import json
import re

class Parser(MerchantParser):
    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('1?','%s?'%i)
        return url

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _parse_json(self, obj, item, **kwargs):
        item['tmp'] = obj
          
    def _parse_multi_items(self, response, item, **kwargs):
        obj = item['tmp']
        datas = obj['product']['traits']['colors']['colorMap']
        sizes = obj['product']['traits']['sizes']['sizeMap'] if 'sizes' in obj['product']['traits'] else {}
        sizeids = obj['product']['relationships']['upcs']
        detail = obj['product']['detail']['bulletText']
        item['description'] = '\n'.join(detail)
        code = str(obj['product']['id'])
        skus = []

        for color_id, color_data in list(datas.items()):
            item_color = deepcopy(item)
            item_color['color'] = color_data['name'].upper()
            item_color['sku'] = code + item_color['color']
            skus.append(item_color['sku'])

            osizes = []
            for sizeid in list(sizeids.values()):
                if not sizeid['availability']['available'] or sizeid['traits']['colors']['selectedColor'] != int(color_id):
                    continue
                if 'sizes' in sizeid['traits'] and int(color_id) in sizes[str(sizeid['traits']['sizes']['selectedSize'])]['colors']:
                    osizes.append(sizes[str(sizeid['traits']['sizes']['selectedSize'])]['name'])

            item_color['originsizes'] = osizes if osizes else ['IT']
            self.sizes(obj, item_color, **kwargs)

            prices = color_data['pricing']['price']['tieredPrice']

            if len(prices) == 1:
                item_color['originlistprice'] = prices[0]['values'][0]['formattedValue']
                item_color['originsaleprice'] = prices[0]['values'][0]['formattedValue']
            else:
                item_color['originlistprice'] = prices[0]['values'][0]['formattedValue']
                item_color['originsaleprice'] = prices[1]['values'][0]['formattedValue']
            self.prices(obj, item_color, **kwargs)

            imgs = color_data['imagery']['images']
            item_color['images'] = []

            for img in imgs:
                image = 'https://images.bloomingdalesassets.com/is/image/BLM/products/' + img['filePath'] + '?op_sharpen=1&wid=700'
                item_color['images'].append(image)

            item_color['cover'] = item_color['images'][0]
            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _parse_images(self, response, **kwargs):
        images = []
        tmp = response.xpath('//script[@data-bootstrap="page/product"]/text()').extract_first()
        obj = json.loads(tmp)
        datas = obj['product']['traits']['colors']['colorMap']
        images = []

        for color_data in list(datas.values()):
            if not response.meta['sku'].upper().endswith(color_data['name'].upper()):
                continue
            imgs = color_data['imagery']['images']

            for img in imgs:
                image = 'https://images.bloomingdalesassets.com/is/image/BLM/products/' + img['filePath'] + '?op_sharpen=1&wid=700'
                images.append(image)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        fits = response.xpath(size_info['size_info_path']).extract()
        size_infos = []

        for fit in fits:
            if 'Dimensions:' in fit or 'Model is' in fit or 'measurements:' in fit or '"W' in fit or '"D' in fit or '"H' in fit or ('heel' in fit and '"' in fit):
                size_infos.append(fit)

        size_info = '\n'.join(size_infos)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = 'bloomingdales'
    merchant = "Bloomingdale's"
    url_split = False
    merchant_headers = {
    'User-Agent':'ModeSensBotBloomingdales190201',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//select[@id="sort-pagination-select-top"]/option[last()]/@value',
            list_url = _parser.list_url,
            items = '//ul[contains(@class,"items")]/li/div',
            designer = './/span[@class="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@class="button add-to-bag"] | //button[@data-auto="add-to-bag"]', _parser.checkout)),
            ('name', '//*[@data-auto="product-name"]/text()'),
            ('designer', '//a[@data-auto="product-brand"]/text()'),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//ul[@data-auto="product-description-bullets"]/li/text()',
            ),
        )

    json_path = dict(
        method = _parser.parse_json,
        obj_path = '//script[@data-bootstrap="page/product"]',
        keyword = 'ProductId',
        flag = ('strat_flag','end_flag'),
        field = dict(
            ),
        )

    parse_multi_items = _parser.parse_multi_items


    list_urls = dict(
        m = dict(
            a = [
                'https://www.bloomingdales.com/shop/mens/designer-belts/Pageindex/1?id=1000060',
                'https://www.bloomingdales.com/shop/mens/cologne-grooming-kit/Pageindex/1?id=1000067',
                'https://www.bloomingdales.com/shop/mens/hats-gloves-scarves/Pageindex/1?id=1000062',
                'https://www.bloomingdales.com/shop/mens/jewelry-cufflinks/Pageindex/1?id=1000061',
                'https://www.bloomingdales.com/shop/mens/luggage/Pageindex/1?id=1006228',
                'https://www.bloomingdales.com/shop/mens/travel-accessories-toiletry-bags/Pageindex/1?id=1006229',
                'https://www.bloomingdales.com/shop/mens/sunglasses/Pageindex/1?id=1000068',
                'https://www.bloomingdales.com/shop/mens/ties-bow-ties-pocket-squares/Pageindex/1?id=1003731',
                'https://www.bloomingdales.com/shop/mens/tech-accessories-cases/Pageindex/1?id=1000833',
                'https://www.bloomingdales.com/shop/mens/wallets-money-clips/Pageindex/1?id=1000065',
                'https://www.bloomingdales.com/shop/mens/watches/Pageindex/1?id=1000066',
            ],
            b = [
                'https://www.bloomingdales.com/shop/mens/bags-briefcases/Pageindex/1?id=1000059',
            ],
            c = [
                'https://www.bloomingdales.com/shop/mens/activewear-workout-clothes/Pageindex/1?id=1004734',
                'https://www.bloomingdales.com/shop/mens/mens-sport-coats-blazers/Pageindex/1?id=1000074',
                'https://www.bloomingdales.com/shop/mens/casual-button-down-shirts/Pageindex/1?id=17648',
                'https://www.bloomingdales.com/shop/mens/coats-jackets/Pageindex/1?id=11548',
                'https://www.bloomingdales.com/shop/mens/dress-shirts/Pageindex/1?id=17647',
                'https://www.bloomingdales.com/shop/mens/hoodies-sweatshirts/Pageindex/1?id=1003569',
                'https://www.bloomingdales.com/shop/mens/jeans/Pageindex/1?id=10172',
                'https://www.bloomingdales.com/shop/mens/pajamas-loungewear-robes/Pageindex/1?id=1004554',
                'https://www.bloomingdales.com/shop/mens/pants/Pageindex/1?id=10189',
                'https://www.bloomingdales.com/shop/mens/polos-shirts/Pageindex/1?id=1000663',
                'https://www.bloomingdales.com/shop/mens/shorts/Pageindex/1?id=11576',
                'https://www.bloomingdales.com/shop/mens/suits-tuxedos/Pageindex/1?id=1003462',
                'https://www.bloomingdales.com/shop/mens/sweaters/Pageindex/1?id=10258',
                'https://www.bloomingdales.com/shop/mens/swimwear/Pageindex/1?id=1003490',
                'https://www.bloomingdales.com/shop/mens/t-shirts-henleys/Pageindex/1?id=11536',
                'https://www.bloomingdales.com/shop/mens/underwear-undershirts/Pageindex/1?id=10237',
                'https://www.bloomingdales.com/shop/mens/dress-socks/Pageindex/1?id=1003733'
            ],
            s = [
                'https://www.bloomingdales.com/shop/mens/designer-shoes/Pageindex/1?id=1000055',
            ],
        ),
        f = dict(
            a = [
                'https://www.bloomingdales.com/shop/fashion-lookbooks-videos-style-guide/jewelry-accessories/Pageindex/1?id=1001781',
            ],
            b = [
                'https://www.bloomingdales.com/shop/handbags/womens-handbags-purses/Pageindex/1?id=17316',
            ],
            c = [
                'https://www.bloomingdales.com/shop/womens-apparel/active-workout-lounge/Pageindex/1?id=1062259',
                'https://www.bloomingdales.com/shop/womens-apparel/blazers/Pageindex/1?id=1005879',
                'https://www.bloomingdales.com/shop/womens-apparel/coats-jackets/Pageindex/1?id=1001520',
                'https://www.bloomingdales.com/shop/womens-apparel/designer-dresses/Pageindex/1?id=21683',
                'https://www.bloomingdales.com/shop/womens-apparel/cocktail-party-bodycon-dresses/Pageindex/1?id=1005206',
                'https://www.bloomingdales.com/shop/womens-apparel/formal-dresses-evening-gowns/Pageindex/1?id=1005210',
                'https://www.bloomingdales.com/shop/womens-apparel/jeans/Pageindex/1?id=5545',
                'https://www.bloomingdales.com/shop/womens-apparel/jumpsuits-rompers/Pageindex/1?id=15299',
                'https://www.bloomingdales.com/shop/womens-apparel/lingerie-bras-panties-shapewear/Pageindex/1?id=5566',
                'https://www.bloomingdales.com/shop/womens-apparel/pants-leggings/Pageindex/1?id=17566',
                'https://www.bloomingdales.com/shop/womens-apparel/matching-sets/Pageindex/1?id=1068159',
                'https://www.bloomingdales.com/shop/womens-apparel/shorts-skirts/Pageindex/1?id=1062159',
                'https://www.bloomingdales.com/shop/womens-apparel/sleepwear-robes/Pageindex/1?id=21429',
                'https://www.bloomingdales.com/shop/womens-apparel/sweaters/Pageindex/1?id=12374',
                'https://www.bloomingdales.com/shop/womens-apparel/womens-swimsuits/Pageindex/1?id=1027052',
                'https://www.bloomingdales.com/shop/womens-apparel/tops-tees/Pageindex/1?id=5619',
            ],
            s = [
                'https://www.bloomingdales.com/shop/womens-designer-shoes/all-fashion-shoes/Pageindex/1?id=17411',
            ],
            e = [
                'https://www.bloomingdales.com/shop/fashion-lookbooks-videos-style-guide/new-beauty-products/Pageindex/1?id=16541',
            ],

        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {
                'shippingCountry':'US',
                'currency':'USD',
            },
        ),
        CN = dict(
            area = 'AP',
            currency = 'CNY',
            cookies = {
                'shippingCountry':'CN',
                'currency':'CNY',
            },
        ),
        JP = dict(
            area = 'AP',
            currency = 'JPY',
            cookies = {
                'shippingCountry':'JP',
                'currency':'JPY',
            },
        ),
        KR = dict(
            area = 'AP',
            currency = 'KRW',
            cookies = {
                'shippingCountry':'KR',
                'currency':'KRW',
            },
        ),
        HK = dict(
            area = 'AP',
            currency = 'HKD',
            cookies = {
                'shippingCountry':'HK',
                'currency':'HKD',
            },
        ),
        SG = dict(
            area = 'AP',
            currency = 'SGD',
            cookies = {
                'shippingCountry':'SG',
                'currency':'SGD',
            },
        ),
        AU = dict(
            area = 'AP',
            currency = 'AUD',
            cookies = {
                'shippingCountry':'AU',
                'currency':'AUD',
            },
        ),
        GB = dict(
            area = 'AP',
            currency = 'GBP',
            cookies = {
                'shippingCountry':'GB',
                'currency':'GBP',
            },
        ),
        DE = dict(
            area = 'AP',
            currency = 'EUR',
            cookies = {
                'shippingCountry':'DE',
                'currency':'EUR',
            },
        ),
        CA = dict(
            area = 'AP',
            currency = 'CAD',
            cookies = {
                'shippingCountry':'CA',
                'currency':'CAD',
            },
        ),
        NO = dict(
            area = 'AP',
            currency = 'NOK',
            cookies = {
                'shippingCountry':'NO',
                'currency':'NOK',
            },
        ),
        RU = dict(
            area = 'AP',
            currency = 'RUB',
            cookies = {
                'shippingCountry':'RU',
                'currency':'RUB',
            },
        )
        )