from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        add_to_cart = checkout.extract_first()
        if add_to_cart and 'Add to Cart' in add_to_cart:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract_first().split('var __st=')[-1][:-1])
        item['sku'] = data['rid']
        item['designer'] = 'ORA ERA'

    def _description(self, desc, item, **kwargs):
        description = desc.extract()
        desc_li = []
        color = ''
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
            if 'Color:' in desc:
                color = desc.split(':')[-1].strip().upper()
        description = '\n'.join(desc_li)

        item['description'] = description
        item['color'] = color

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            image = 'https:' + img.replace('_100x', '_800x')
            images.append(image)
        item['images'] = images
        item['cover'] = images[0]

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = ['One Size']
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[@class="current_price"]/span/text()').extract_first()
        listprice = prices.xpath('.//span[@class="was_price"]/text()').extract_first()

        item['originsaleprice'] = saleprice.strip()
        item['originlistprice'] = listprice.strip() if listprice else saleprice.strip()

    def _list_url(self, i, response_url, **kwargs):
        return response_url

_parser = Parser()


class Config(MerchantConfig):
    name = 'oraera'
    merchant = 'ORA ERA'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a[@class="last"]/text()',
            list_url = _parser.list_url,
            items = '//div[@itemtype="http://schema.org/ItemList"]/div',
            designer = './/div[@class="brand-name"]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@name="add"]/span/text()', _parser.checkout)),
            ('sku', ('//script[@id="__st"]/text()',_parser.sku)),
            ('name', '//h1[@class="product_name"]/text()'),
            ('images', ('//div/div[@data-media-type="image"]//img/@src', _parser.images)),
            ('description', ('//div[@class="description"]//text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//div[@class="modal_price"]', _parser.prices))
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
            b = [
                'https://www.oraera.com/collections/products'
            ]
        )
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        )
        )

        


