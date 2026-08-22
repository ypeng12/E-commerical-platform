# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

# https://stockx.com/omega-speedmaster-moonwatch-anniversary-limited-series-31163423003001-blue #no prices

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _parse_json(self, obj, item, **kwargs):
        item['sku'] = obj['product']['id'].upper()
        item['name'] = obj['product']['title']
        item['designer'] = obj['product']['brand'].upper()
        item['images'] = []
        for image in obj['product']['media']['gallery']:
            item['images'].append(image.split('?')[0])
        color = ''
        details = []
        for desc in obj['product']['traits']:
            if desc['name'] == 'Color':
                color = desc['value']
            detail = desc['name'] + ': ' + str(desc['value'])
            details.append(detail)
        item['description'] = '\n'.join(details)
        item['color'] = color

        for value in list(obj['product']['children'].values()):
            print(value['market']['lowestAsk'])
            print(value['market']['lastSale'])
            print(value['shoeSize'])
            print('=======================')

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
        if item['category'] in ['c','s']:
            item_dict = item['tmp']
            sizes = []
            for code_sizes in item_dict['SizesByCode10']:
                if item['sku'] in code_sizes['Code10']:
                    sizes = code_sizes['Sizes']
                    break
            for size in sizes:
                item['originsizes'].append(size['Description'].strip())

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('./span[@class="full price"]/span[@class="value"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('./span[@class="discounted price"]/span[@class="value"]/text()').extract()[0]
        except:
            item['originlistprice'] = prices.xpath('./span[@class="price"]/span[@class="value"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('./span[@class="price"]/span[@class="value"]/text()').extract()[0]

    def _parse_images(self, response, **kwargs):
        images = []

        try:
            script = response.xpath('//script[contains(text(),"window.preLoaded =")]/text()').extract_first()
            data = json.loads(script.split('window.preLoaded =')[-1].rsplit(';',1)[0].strip())

            for image in data['product']['media']['gallery']:
                images.append(image.split('?')[0])
        except:
            pass

        if not images:
            img = response.xpath('//div[@class="image-container"]/img/@src | //div[@class="product-media"]//img/@src').extract_first()
            images.append(img.split('?')[0])

        return images


_parser = Parser()



class Config(MerchantConfig):
    name = 'stockx'
    merchant = "StockX"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//ul[@class="products"]/@data-ytos-opt',_parser.page_num),
            items = '//li[@class="products-item   "]',
            designer = './/span[@class="designer"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            # ('checkout', ('//span[@data-ytos-btn-label]', _parser.checkout)),
            # ('sku', ('//html', _parser.sku)),
            # ('name', '//meta[@name="title"]/@content'),
            # ('designer', ('//html',_parser.designer)),
            # ('images', ('//div', _parser.images)),
            # ('color',('//ul[@class="clearfix"]/li/img/@alt',_parser.color)),
            # ('description', ('//div[contains(@class,"attributesUpdater details")]//span[@class="value"]//text()',_parser.description)),
            # ('sizes', ('//div[@class="taglie clearfix"]/select/option[not(@disabled)]/text()', _parser.sizes)),
            # ('prices', ('//*[@id="itemInfo"]//div[@class="itemPrice"]', _parser.prices))
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

    json_path = dict(
        method = _parser.parse_json,
        obj_path = '//script[@type="text/javascript"]',
        keyword = 'window.preLoaded =',
        flag = ('window.preLoaded =',';'),
        field = dict(
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
            language = 'EN', 
            currency = 'USD',
        )
        )
        


