from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy


class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first() and 'Out of stock' in checkout.extract_first():
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        obj = json.loads(data.extract_first())[3]

        item['name'] = obj['props']['currentProduct']['displayName']
        if 'onSaleChildSkus' in obj['props']['currentProduct']:
            item['tmp'] = obj['props']['currentProduct']['onSaleChildSkus']
        else:
            item['tmp'] = [obj['props']['currentProduct']['currentSku']]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        details = ''
        for desc in description:
            if desc.strip() and desc.strip()[-1] != ':':
                detail = desc.strip() + '\n'
            else:
                detail = desc.strip()
            details += detail
        item['description'] = details.strip()

    def _parse_multi_items(self, response, item, **kwargs):
        for color in item['tmp']:
            item_color = deepcopy(item)
            item_color['sku'] = color['skuId']
            item_color['color'] = color['skuName'] if 'skuName' in color else ''
            item_color['originlistprice'] = color['listPrice']
            item_color['originsaleprice'] = color['salePrice'] if 'salePrice' in color else color['listPrice']
            self.prices(response, item_color, **kwargs)
            item_color['originsizes'] = [color['size']] if 'size' in color else ['IT']
            self.sizes(response, item_color, **kwargs)
            item_color['cover'] = 'https://www.sephora.com' + color['skuImages']['image1500']
            item_color['images'] = [item_color['cover']]
            for img in color['alternateImages']:
                image = 'https://www.sephora.com' + img['image1500']
                if 'not-available' not in image:
                    item_color['images'].append(image)
            item_color['url'] = item_color['url'] + '?skuId=' + item_color['sku']
            yield item_color

    def _parse_item_url(self, response, **kwargs):
        obj = json.loads(response.body)
        pages = int(obj['totalProducts']/60) +2
     
        for p in range(0,pages):
            url = response.url.split('?')[0] + '?currentPage='+str(p)

            results = getwebcontent(url)
            results = json.loads(results)

            products = results['products']
            for product in products:
                href = product['targetUrl']
                url =  urljoin('https://www.sephora.com', href)
                yield url,'SEPHORA'

_parser = Parser()



class Config(MerchantConfig):
    name = "sephora"
    merchant = "SEPHORA"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-at="selected_swatch"]/@aria-label', _parser.checkout)),
            ('sku', ('//script[@id="linkJSON"]/text()', _parser.sku)),
            ('designer', '//span[@class="css-euydo4"]/text()'),
            ('description', ('//div[@id="tabpanel0"]/div//text()',_parser.description)),
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

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            e = [
                "https://www.sephora.com/api/catalog/categories/cat130038/products?currentPage=", #Hair
                "https://www.sephora.com/api/catalog/categories/cat140006/products?currentPage=",#Makeup
                "https://www.sephora.com/api/catalog/categories/cat150006/products?currentPage=", #skin
                "https://www.sephora.com/api/catalog/categories/cat160006/products?currentPage=", # Fragrance
                "https://www.sephora.com/api/catalog/categories/cat130042/products?currentPage=", # Tools
                "https://www.sephora.com/api/catalog/categories/cat140014/products?currentPage=", #Body and Bath
                "https://www.sephora.com/api/catalog/categories/cat1830032/products?currentPage=",
            ],
        ),
        m = dict(
            e = [
                "https://www.sephora.com/api/catalog/categories/cat130044/products?currentPage=",
            ],

        params = dict(
            # TODO:
            ),
        ),
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
        ),

        )

