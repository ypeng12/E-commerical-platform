from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):

    def _parse_multi_items(self, response, item, **kwargs):
        data = json.loads(response.body)['product']
        item['url'] = response.url.split('.json')[0]

        if kwargs['category'] == 'b':
            if data['fashionVariantsProductData'][0]['stockStatusIT'] != 'AVAILABLE':
                item['originsizes'] = ''
                item['sizes'] = ''
                if 'sku' in response.meta:
                    item['sku'] = response.meta['sku']
                item['error'] = 'Out Of Stock'
                yield item
                return
        item['name'] = data['name']

        item['sku'] = data['code']
        item['color'] = data['fashionVariantsProductData'][0]['colorType']


        images = []
        try:
            for img in data['fashionVariantsProductData'][0]['normals']:
                images.append(img['url'].replace('//', 'http://'))

            item['images'] = images
            item['cover'] = item['images'][0]
        except:
            item['images'] = []
            item['cover'] = ''
        tmps = data['fashionVariantsProductData']
        if not tmps:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['error'] = 'Out Of Stock'
            yield item
            return
        item['originsizes'] = []
        if kwargs['category'] == 's':
            sizes = []
            for tmp in tmps:
                if tmp['stockLevel'] != 0:
                    info = tmp['size']
                    size = toItSize(info.split('(')[0])
                    sizes.append(size)
                    item['originsizes'].append(info)
            item['originsizes'] = '####' + ';'.join([x[0].replace('IT','')+'-'+x[1] for x in zip(sizes,item['originsizes'])])
            sizes.sort()
            item['sizes'] = ';'.join(sizes)
            # item['originsizes'] = ';'.join(item['originsizes'])
            if len(item['sizes']) == 0:
                item['originsizes'] = ''
                item['sizes'] = ''
                item['error'] = 'Out Of Stock'
        else:
            item['originsizes'] = 'IT'
            item['sizes'] = 'IT'

        item['designer'] = "ROGER VIVIER"
        prices = data['fashionVariantsProductData'][0]['priceData']['formattedValue']
        try:
            item['originsaleprice'] = data['fashionVariantsProductData'][0]['priceData']['formattedValue']
            if data['fashionVariantsProductData'][0]['fullPrice']:
                item['originlistprice'] = data['fashionVariantsProductData'][0]['fullPrice']['value']
            else:
                item['originlistprice'] = item['originsaleprice']
        except Exception as ex:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['error'] = 'Out Of Stock'
            yield item
        self.prices(prices, item, **kwargs)
        description = [data['longDesc2']] if data['longDesc2'] else []
        detail = data['description'].replace('<ul>','').replace('</ul>','').replace('</li>','').split('<li>') if data['description'] else []
        detail = description + detail
        self.description(detail,item,**kwargs) if detail else ''

        if item['originsizes'] and item['originsizes'][-1] != ';':
            item['originsizes'] += ';'
        if item['sizes'] and item['sizes'][-1] != ';':
            item['sizes'] += ';'
        yield item            

        
    def _description(self, description, item, **kwargs):
        description = description
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.replace('<!DOCTYPE html>','').replace('<html>','').replace('<head>','').replace('</head>','').replace('<body>','').replace('</body>','').replace('</html>','')

  
    def _parse_item_url(self, response, **kwargs):
        country = kwargs['country'].upper()
        html = json.loads(response.body)
        pages = html['searchPageData']['pagination']['numberOfPages'] - 1
        url = response.url.replace('?p=1','') + '?q=%3Acustom-asc%3A&pageEnd=' + str(pages)
        result = getwebcontent(url)
        html1 = json.loads(result)
        url = None
        for p in html1['searchPageData']['results']:
            link = p['product']['url']
            if country == "US":
                url = "http://store.rogervivier.com/US" + link + ".json"
            elif country == "CN":
                url = "http://store.rogervivier.cn/CN" + link + ".json"
            elif country == "GB":
                url = "http://store.rogervivier.com/GB" + link + ".json"
            elif country == "DE":
                url = "http://store.rogervivier.com/AT" + link + ".json"
            yield url,'ROGER VIVIER'

    def _parse_images(self, response, **kwargs):
        # Not Getting Urls from DB
        print(response)

_parser = Parser()



class Config(MerchantConfig):
    name = "rv"
    merchant = "Roger Vivier"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            items = '//div[@class="products"]/article',
            designer = '@data-ytos-track-product-data',
            link = './a/@href',
            ),
        product = OrderedDict([
            # ('checkout', ('//html', _parser.checkout)),

            # ('sku', ('//html',_parser.sku)),
            # ('name', '//span[@class="modelName inner"]/text()'),  
            # ('images', ('//ul[@class="alternativeImages"][1]/li/img/@data-origin', _parser.images)),
            # ('description', '//div[@class="descriptionContent accordion-content"]/text()|//div[@class="descriptionContent"]//text()'''),
            # ('sizes', ('//html', _parser.sizes)), 
            # ('prices', ('//html', _parser.prices)),
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
                "http://store.rogervivier.com/US/E-SHOP/Accessories/c/139.json?p=",
                ],
            b = [
                "http://store.rogervivier.com/US/E-SHOP/Bags/c/129.json?p=",
            ],
            s = [
                "http://store.rogervivier.com/US/E-SHOP/Shoes/c/119.json?p=",
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
            # TODO:
            ),
        ),

        country_url_base = '/US/',
    )

    parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/US/',
            ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            area = 'AS',
            country_url = '/CN/',
            currency_sign = '\xa5',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/GB/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign='',
            country_url = '/DE/',

        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '/HK_EN/',

        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            currency_sign = 'C$',
            country_url = '/CA_EN/',

        ),

        )

        


