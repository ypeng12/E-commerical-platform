from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if 'Add to basket' in checkout.extract_first():
            item['error'] = 'ignore' # just checkout
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract_first())
        if data['sku'].isdigit() and len(data['sku']) in [6, 7, 8]:
            item['sku'] = data['sku'] 
        else:
            item['sku'] = ''
        item['name'] = data['name']
        item['color'] = data['color']
        item['designer'] = data['brand']['name']
        # item['description'] = data['description']
        item['images'] = data['image']
        item['cover'] = data['image'][0]
        item['condition'] = 'p'

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)
        item['description'] = description

    def _prices(self, prices, item, **kwargs):
        js_url = 'https://apiv2.vestiairecollective.com/products/%s?isoCountry=%s&x-currency=%s&x-language=us&x-siteid=18'%(item['sku'],item['country'],item['currency'])

        result = getwebcontent(js_url)
        obj = json.loads(result)

        saleprice = obj['data']['price']['formatted']
        if 'regularPrice' in obj['data']:
            listprice = obj['data']['regularPrice']['formatted']
        else:
            listprice = saleprice
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _sizes(self, data, item, **kwargs):
        descs = data.extract()
        size = ''
        # for desc in descs:
        #     if 'Size:' in desc:
        #         size = descs.split(':')[-1].strip()
        #         break
        if 'Size:' in descs:
            size = descs[descs.index('Size:') + 1]
        item['originsizes'] = [size] if size else ['IT']

    def _parse_images(self, response, **kwargs):
        script = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        data = json.loads(script)
        images = data['image']
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'vc'
    merchant = 'Vestiaire Collective'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout',('//button[@data-cy="pdp_buy_btn"]/text()', _parser.checkout)),
            ('sku',('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('prices', ('//div[@class="productPrice"]', _parser.prices)),
            ('sizes', ('//ul[contains(@class,"product-description-list_descriptionList__list")]/li/span/text()', _parser.sizes)),
            ('description', ('//div[@class="sellerDescription"]/p/text()',_parser.description)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '',
        )

    )

        