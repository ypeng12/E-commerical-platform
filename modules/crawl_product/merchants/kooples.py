from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):

    def _checkout(self, scripts, item, **kwargs):
        scripts_data = scripts.extract()
        for script in scripts_data:
            if 'spConfig' in script:
                script_str = script
                break

        script_str = script_str.split('Product.Config(')[-1].split('$$')[0].split(');')[0]
        script_dict = json.loads(script_str)
        avail = 0
        for size in list(script_dict['attributes'].values())[0]['options']:
            if size['stock']>0:
                avail = avail+1
        if avail == 0:
            sold_out = True
        else:
            sold_out = False
            item['tmp'] = script_dict
        return sold_out

    def _page_num(self, data, **kwargs):
        items_num = data.split('(')[-1].split(')')[0]
        page_num = int(items_num) / 20
        return page_num + 1

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?ajax=1&html=1&p=%s'%(i)
        return url

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'THE KOOPLES'
        
    def _sizes(self, sizes, item, **kwargs):
        json_dict = item['tmp']
        products = json_dict['attributes']['257']['options']
        size_li = []
        for product in products:
            if product['stock'] > 0:
                size_li.append(product['label'])

        item['originsizes'] = size_li

    def _prices(self, price, item, **kwargs):
        json_dict = item['tmp']
        salePrice = json_dict['basePrice']
        listPrice = json_dict['oldPrice']

        item['originlistprice'] = listPrice if len(listPrice) else salePrice
        item['originsaleprice'] = salePrice      

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
        item['cover'] = images[0]
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append(img.replace('http:','https:'))
        item['images'] = img_li

_parser = Parser()


class Config(MerchantConfig):
    name = 'kooples'
    merchant = 'The Kooples'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[contains(@class,"product-total")]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-image-visible"]',
            designer = './/div[@class="brand"]/text()',
            link = './/a[@class="product-image"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script/text()', _parser.checkout)),
            ('sku', '//div/@data-product-sku'),
            ('color','//ul[@class="product-colors-list"]/li[@class="current-product"]//figcaption/text()'),
            ('name', '//h1[contains(@class,"product-page-title")]/text()'),    # TODO: path & function
            ('designer', ('//html',_parser.designer)),
            ('description', ('//p[@class="editors-note-text"]/text()',_parser.description)),
            ('image',('//div[contains(@class,"product-swiper-slide")]/picture/source[1]/@data-srcset',_parser.images)),
            ('sizes',('//html',_parser.sizes)),
            ('prices',('//html',_parser.prices)),
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(
            ),
        designer = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.thekooples.com/us/women/accessories.html?ajax=1&html=1&p=',
            ],
            b = [
                'https://www.thekooples.com/us/all.html?ajax=1&html=1&p=',
            ],
            c = [
                "https://www.thekooples.com/us/women/dresses.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/blouses-us.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/tops-t-shirts-us.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/jackets.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/skirts-shorts.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/trousers.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/knitwear.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/short-jackets.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/denim.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/women/jumpsuits.html?ajax=1&html=1&p=",
            ],
            s = [
                'https://www.thekooples.com/us/women/shoes.html?ajax=1&html=1&p=',
            ],
        ),
        m = dict(
            a = [
                'https://www.thekooples.com/us/men/accessories.html?ajax=1&html=1&p=',
            ],
            b = [
            ],
            c = [
                "https://www.thekooples.com/us/men/shirts.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/short-jackets.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/knitwear.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/suits-1.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/jackets.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/trousers-and-shorts.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/denim.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/t-shirts.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/polo-s.html?ajax=1&html=1&p=",
                "https://www.thekooples.com/us/men/coats-parkas.html?ajax=1&html=1&p=",
            ],
            s = [
            "https://www.thekooples.com/us/men/shoes.html?ajax=1&html=1&p="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'www.',
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
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            country_url = '.co.uk/',
            ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            country_url = '.com/en/',
            language = 'DE',
            ),

        )

        


