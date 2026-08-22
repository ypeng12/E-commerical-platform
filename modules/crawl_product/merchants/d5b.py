from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = 10
        return pages

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, scripts, item, **kwargs):
        price_script = scripts.extract_first()

        data = json.loads(price_script.split('var BCData =')[-1].split(';')[0].strip())
        item['sku'] = data['product_attributes']['sku']
        item['tmp'] = data

    def _designer(self, data, item, **kwargs):
        item['designer'] = data.extract_first().upper()

    def _color(self, data, item, **kwargs):
        try:
            color = data.extract_first().split(':')[-1].strip().upper()
        except:
            color = ''
        item['color'] = color

    def _images(self, imgs, item, **kwargs):
        images = imgs.extract()
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

    def _sizes(self, data, item, **kwargs):
        pre_order = data.xpath('//input[@id="form-action-addToCart"]/@value').extract_first()
        if pre_order and 'Pre-Order' in pre_order:
            memo = ':p'
        else:
            memo = ''
        sizes = []
        real_sizes_attr = item['tmp']['product_attributes']['in_stock_attributes']
        for real_size in real_sizes_attr:
            avail_sizes = data.xpath('//label[@data-product-attribute-value={}]/span/text()'.format(real_size)).extract_first()
            sizes.append(avail_sizes)
        item['originsizes'] = []
        if len(sizes) != 0:
            for size in sizes:
                size = size.split('-')[0].upper().replace('SIZE','').replace('IN STOCK','').strip()
                if size !='':
                    item['originsizes'].append(size + memo)
        elif item['category'] in ['a','b'] and not item['originsizes']:
            item['originsizes'] = ['IT' + memo]

    def _prices(self, datas, item, **kwargs):
        data = item['tmp']
        salePrice = data['product_attributes']['price'].get('sale_price_without_tax')
        listprice = data['product_attributes']['price'].get('non_sale_price_without_tax')
 
        if not salePrice:
            item['originsaleprice'] = data['product_attributes']['price'].get('without_tax')['formatted']
            item['originlistprice'] = data['product_attributes']['price'].get('without_tax')['formatted']
        else:
            item['originsaleprice'] = salePrice['formatted']
            item['originlistprice'] = listprice['formatted']

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//ul[@class="productView-thumbnails"]/li/a/@href').extract()
        return images


_parser = Parser()



class Config(MerchantConfig):
    name = 'd5b'
    merchant = "District 5 Boutique"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@id="resultsCount"]/text()', _parser.page_num),
            items = '//ul[@class="productGrid"]/li',
            designer = './/span[@class="designer"]/text()',
            link = './/a[@title]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@id="form-action-addToCart"]', _parser.checkout)),
            ('sku', ('//script[contains(text(),"var BCData")]/text()', _parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('designer', ('//*[@itemprop="brand"]//span/text()',_parser.designer)),
            ('images', ('//ul[@class="productView-thumbnails"]/li/a/@href | //div[@class="productView-img-container"]/a/img/@src', _parser.images)),
            ('color',('//li[contains(text(),"Color")]/text()',_parser.color)),
            ('description', ('//div[@id="tab-description"]//text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[contains(@class,"HTMLListColorSelector")]//ul/li/@data-ytos-color-model',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            c = [
                'https://www.district5boutique.com/new-arrivals/?page=',
                'https://www.district5boutique.com/in-stock/?page='
            ],

        params = dict(
            )
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        )

        )
        


