# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils import utils

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout.xpath('//button[@title="Add to Bag"]') or checkout.xpath('//button[@title="sold out"]'):
            return True
        else:
            return False

    def _sku(self, scripts, item, **kwargs):
        sku_script = ''
        for script in scripts.extract():
            if 'productSku' in script:
                sku_script = script
                break
        prd_dict = json.loads(sku_script.split('{app.pageContextObject =')[-1].split(';}')[0].strip())
        item['sku'] = prd_dict['trackerData']['productSku']
        item['name'] = prd_dict['trackerData']['ecommerce']['detail']['products'][0]['name']
        item['designer'] = 'KERASTASE'
        item['tmp'] = prd_dict

    def _images(self, response, item, **kwargs):
        imgs = response.xpath('.//div[@id="thumbnails"]//ul/li/a/img/@data-src').extract()
        item['images'] = []
        for img in imgs:
            if img not in item['images']:
                item['images'].append(img)
        if not len(item['images']):
            item['images'] = response.xpath('.//div[@class="product_primary_image"]//img/@data-src').extract()
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        prd_dict = item['tmp']
        item['originlistprice'] = prd_dict['trackerData']['productPrice']
        item['originsaleprice'] = prices.xpath('.//meta[@itemprop="price"]/@content').extract_first()


_parser = Parser()


class Config(MerchantConfig):
    name = "kerastase"
    merchant = "K\u00e9rastase"


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//li[@class="pagingDots"]/following-sibling::li/a/text()',
            items = '//div[@class="product_tile_wrapper b-product_tile-wrapper"]',
            designer = '//div[@class="designer"]',
            link = './/a[@class="product_name "]/@href',
            ),
        product = OrderedDict([
            ('checkout',('//html', _parser.checkout)),
            ('sku', ('//script/text()', _parser.sku)),
            # ('name', '//html'),
            # ('designer', ''),
            ('description', '//h2[@class="product_subtitle "]/text()'),
            ('color','//div[@class="color"]/text()'),
            ('prices', ('//html', _parser.prices)),
            ('images',('//html',_parser.images)),
            ('sizes',('//html',_parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
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
            e = [
                'https://www.kerastase-usa.com/collections/aura-botanica?sz=10&start=100000&format=ajax&lazy=true&p='
                'https://www.kerastase-usa.com/collections/blond-absolu?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/chronologiste?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/densifique?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/discipline?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/elixir-ultime?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/nutritive?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/resistance?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/reflection?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/collections/specifique?sz=10&start=100000&format=ajax&lazy=true&p=',
                'https://www.kerastase-usa.com/shampoos?sz=10&start=100000&format=ajax&lazy=true&p='
                'https://www.kerastase-usa.com/conditioners?sz=10&start=100000&format=ajax&lazy=true&p='

            ]
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
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = '$',
            country_url = '.com',
            ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = 'USD',
        #     country_url = '.jp',
        #     # vat_rate = 1.064
        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.128
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.093
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.076
        # ),
        # GB = dict(
        #     currency = 'GBP',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.10
        # ),
        # RU = dict(
        #     currency = 'RUB',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.0
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.076
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.083
        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.067
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     discurrency = 'USD',
        #     country_url = 'intl.',
        #     # vat_rate = 1.093
        # ),

        )
