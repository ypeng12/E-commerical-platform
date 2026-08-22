from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = item['url'].split('product/')[-1].strip().split('/')[0]
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img.replace('http:','https:').replace('Mini','Large'))
        item['cover'] = images[0]
        item['images'] = images

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

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        sizes = sizes_data.extract()
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not item['originsizes'] and item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//*[@itemprop="price"]/text()').extract()[0].strip()
        listprices = prices.xpath('//span[@class="strike"]//text()').extract()
        listPrice = ''
        for price in listprices:
            if price.strip():
                listPrice = price
                break
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else salePrice


_parser = Parser()



class Config(MerchantConfig):
    name = 'linde'
    merchant = "L'INDE LE PALAIS"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@class="pagination"]/ul/li[last()-1]/a/text()',
            items = '//ul[@class="clearfix"]/li',
            designer = './/span[@class="designer"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="sold-out"]/text()', _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('name', '//*[@itemprop="name"]/text() | //h1[@itemprop="name"]/strong/text()'),
            ('designer', '//h2[@itemprop="brand"]/a/text()'),
            ('images', ('//div[@class="base-zoom"]/div/ul/li/a/img/@src', _parser.images)),
            ('color','//ul[@class="clearfix"]/li/img/@alt'),
            ('description', ('//p[@itemprop="description"]//text()',_parser.description)), # TODO:
            ('sizes', ('//div[@class="taglie clearfix"]/select/option[not(@disabled)]/text()', _parser.sizes)),
            ('prices', ('/html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="base-zoom"]/div/ul/li/a/img/@src',
            replace = ('Mini','Large'),
            ),
        size_info = dict(
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'http://www.lindelepalais.com/en-US/men/accessories?currPage='
            ],
            b = [
                'http://www.lindelepalais.com/en-US/men/bags?currPage='
            ],
            c = [
                'http://www.lindelepalais.com/en-US/men/clothing?currPage='
            ],
            s = [
                'http://www.lindelepalais.com/en-US/men/shoes?currPage='
            ],
        ),
        f = dict(
            a = [
                'http://www.lindelepalais.com/en-US/women/accessories?currPage=',
            ],
            b = [
                'http://www.lindelepalais.com/en-US/women/bags?currPage='
            ],
            c = [
                'http://www.lindelepalais.com/en-US/women/clothing?currPage='
            ],
            s = [
                'http://www.lindelepalais.com/en-US/women/shoes?currPage='
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLocOnlyShip': 'id=237&nome=United States',
            }
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLocOnlyShip': 'id=168&nome=China',
            }
            
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            cookies={
            'TassoCambio': 'IsoTassoCambio=JPY',
            'geoLocOnlyShip': 'id=105&nome=Japan',
            }
            
        ),
        KR = dict( 
            currency = 'KRW',
            discurrency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLocOnlyShip': 'id=202&nome=South Korea',
            }
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLocOnlyShip': 'id=94&nome=Hong Kong',
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLocOnlyShip': 'id=196&nome=Singapore',
            }
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies={
            'TassoCambio': 'IsoTassoCambio=GBP',
            'geoLocOnlyShip': 'id=235&nome=United Kingdom',
            }
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLocOnlyShip': 'id=37&nome=Canada',
            }
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLocOnlyShip': 'id=12&nome=Australia',
            }
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies={
            'TassoCambio': 'IsoTassoCambio=EUR',
            'geoLocOnlyShip': 'id=78&nome=Germany',
            }
        ),

        NO = dict(
            currency = 'NOK',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies={
            'TassoCambio': 'IsoTassoCambio=EUR',
            'geoLocOnlyShip': 'id=160&nome=Norway',
            }
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies={
            'TassoCambio': 'IsoTassoCambio=EUR',
            'geoLocOnlyShip': 'id=180&nome=Russia',
            }
        )

        )
        


