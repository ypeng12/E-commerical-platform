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
            return False
        else:
            return True

    def _color(self, res, item, **kwargs):
        color_datas = res.extract_first()
        item['color'] = color_datas.split(' - ')[-1] if color_datas else ''

    def _designer(self, designer_data, item, **kwargs):
        item['designer'] = 'REPETTO'
          
    def _images(self, images, item, **kwargs):
        item['images'] = []
        imgs = images.extract()
        for img in imgs:
            item['images'].append(img)
                
        item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, res, item, **kwargs):
        json_data = res.extract_first().split('var spConfig = new Product.Config(')[-1].split('Translator.add')[0].strip().rsplit(');', 1)[0]
        datas = json.loads(json_data)
        sizes_data = []
        for data in datas['attributes']['196']['options']:
            if data['in_stock']:
                sizes_data.append(data['label'].split(' - ')[0])

        item['originsizes'] = sizes_data

        if item['category'] in ['a', 'b', 'e']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./span[@class="price"]/text()').extract_first()
        saleprice = prices.xpath('./span[@class="price"]/text()').extract_first()
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice
   

_parser = Parser()


class Config(MerchantConfig):
    name = 'repetto'
    merchant = 'Repetto'

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//ul[contains(@class,"products")]/li',
            designer = './div/a/@title',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="addtocart"]', _parser.checkout)),
            ('sku',  '//div[@class="tab-contents"]/div[@id="tab-description"]/meta[@itemprop="sku"]/@content'),
            ('color',('//div[@class="product-details"]//div[@class="product-photo"]//a/@title', _parser.color)),
            ('name', '//div[@class="product-info"]/div[contains(@class,"product-title")]/h1/text()'),
            ('designer', ('//html', _parser.designer)),
            ('images', ('//div[@class="product-details"]//figure/a/@href', _parser.images)),
            ('description', ('//div[@class="tab-contents"]/div[@id="tab-description"]/p/text()',_parser.description)),
            ('sizes', ('//script[contains(text(),"new Product.Config")]/text()', _parser.sizes)),
            ('prices', ('//div[@class="price-box"]/span[@class="regular-price"]', _parser.prices))
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
            c = [
                'https://www.repetto.com/us/men/dance.html'
            ],
            s = [
                'https://www.repetto.com/us/men/men.html'
            ],
        ),
        f = dict(
            b = [
                'https://www.repetto.com/us/women/leather-goods.html'
            ],
            c = [
                'https://www.repetto.com/us/women/athleisure.html',
                'https://www.repetto.com/us/women/dance.html'
            ],
            s = [
                'https://www.repetto.com/us/women/women-shoes.html'
            ],
        ),
        k = dict(
            b = [
                'https://www.repetto.com/us/kids/kids-dance-bags.html'
            ],
            c = [
                'https://www.repetto.com/us/kids/dance.html'
            ],
            s = [
                'https://www.repetto.com/us/kids/kids-shoes.html'
            ],
        ),
    )

    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
        ),
    )