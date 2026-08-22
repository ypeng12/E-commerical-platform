from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract()[0].split('"Viewed Product",')[-1].split(');')[0].strip())
        item['sku'] = str(data['productId']) + '_' + str(data['variantId'])
          
    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                images.append(urljoin('https:', img))
        item['cover'] = images[0]
        item['images'] = images[:2] if len(images) >= 2 else images

    def _description(self, description, item, **kwargs):
        item['designer'] = 'TAYLOR MORRIS EYEWEAR'
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, data, item, **kwargs):
        item['originsizes'] = ['IT']
        listprice = data.xpath('//div[@class="six columns omega"]/p[@class="modal_price"]/span[@itemprop="price"]//span[@class="money"]/text()').extract()
        saleprice = data.xpath('//div[@class="six columns omega"]/p[@class="modal_price"]/span[@class="was_price"]//span[@class="money"]/text()').extract()
        item['originsaleprice'] = listprice[0]
        item['originlistprice'] = saleprice[0] if saleprice else listprice[0]
        rate_url = 'https://gex.global-e.com/gempro/initsession/1000104?optCountry=%s&optCurrency=%s' %(item['country'], item['currency'])
        response = requests.get(rate_url)
        rate = float(response.text.split('geFactor:')[-1].split(',')[0].strip())
        item['listprice'] = float(item['originlistprice'].replace('\xa3','')) * rate
        item['saleprice'] = float(item['originsaleprice'].replace('\xa3','')) * rate

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//ul[@class="slides"]/li/a/img/@src').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                images.append(urljoin('https:', img))
        images = images[:2] if len(images) >= 2 else images
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'tme'
    merchant = 'Taylor Morris Eyewear'

    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = '//div[@class="products"]/div[@itemprop="itemListElement"]',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="six columns omega"]//span[@class="sold_out"]/text()', _parser.checkout)),
            ('sku', ('//script[@class="analytics"]/text()',_parser.sku)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('images', ('//ul[@class="slides"]/li/a/img/@src', _parser.images)),
            ('color','//div[@class="information"]//h3/text()'),
            ('description', ('//div[@itemprop="description"]//ul/li/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
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
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
                'https://taylormorriseyewear.com/collections/all',
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
            currency = 'USD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        )
        


