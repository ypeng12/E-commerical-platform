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
        
    def _page_num(self, data, **kwargs):
        page_num = data.split()[-1].strip()

        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _color(self, data, item, **kwargs):
        try:
            item['color'] = data.xpath('.//option[@value="'+item['sku']+'"]/text()').extract()[0].split(' / ')[0].strip().upper()
        except:
            item['color'] = ''
    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = sku_data.xpath('.//li[contains(@class,"product_image")]/@class').extract()[0].split('product_image')[-1].strip()

    def _designer(self, designer_data, item, **kwargs):
        item['designer'] = 'RAINS'
          
    def _images(self, images, item, **kwargs):

        item['images'] = []
        imgs = images.extract()
        for img in imgs:
            image = img
            if 'http' not in img:
                image = 'https:'+img
            if item['color'].strip().replace(' ','_') in image.upper() and image not in item['images']:
                item['images'].append(image)
        try:
            item['cover'] = item['images'][0]
        except:
            item['cover'] = ''
            item['error'] = 'NO images for the Varient'

    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@id="description"]//text()').extract() + description.xpath('.//div/ul/li//text()').extract()
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
            sizes = sizes_data.extract()
            if len(sizes) > 0:
                for size in sizes:
                    if item['color'] in size.upper():
                        item['originsizes'].append(size.strip().split('-')[0].split(' / ')[-1].strip())

        elif item['category'] in ['a', 'b', 'e']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        regularprice = prices.extract()
        item['originlistprice'] = regularprice[0].strip()
        item['originsaleprice'] = item['originlistprice']
   

_parser = Parser()



class Config(MerchantConfig):
    name = 'rains'
    merchant = 'Rains'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            list_url = _parser.list_url,
            items = '//ul[@class="variant_swatches"]/li',
            designer = './div/a/@data-brand',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add-to-bag"]', _parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            ('color',('//html', _parser.color)),
            ('name', '//h1[@class="h2"]/text()'),    # TODO: path & function
            ('designer', ('//html', _parser.designer)),
            ('images', ('//div[@id="carousel"]//li/img/@data-big', _parser.images)),
            ('description', ('//div[@class="product_description tabs"]',_parser.description)), # TODO:
            ('sizes', ('//select[@class="selectbox"]/option/text()', _parser.sizes)),
            ('prices', ('//h3[@class="price"]/text()', _parser.prices))
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
                'https://www.uk.rains.com/collections/waterproof-accessories'
            ],
            b = [
                'https://www.uk.rains.com/collections/bags'
            ],
            c = [
                'https://www.uk.rains.com/collections/jackets-women',
                'https://www.uk.rains.com/collections/womens-quilted-jackets',
                'https://www.uk.rains.com/collections/womens-insulated-jackets',
                'https://www.uk.rains.com/collections/womens-bottoms',
                'https://www.uk.rains.com/collections/ss19-holographic-full/Female'
            ],

        ),
        f = dict(

            c = [
                'https://www.uk.rains.com/collections/jackets-men',
                'https://www.uk.rains.com/collections/mens-quilted-jackets',
                'https://www.uk.rains.com/collections/mens-insulated-jackets',
                'https://www.uk.rains.com/collections/mens-bottoms',
                'https://www.uk.rains.com/collections/ss19-holographic-full/Male'
            ],


        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '.uk.',
    )


    countries = dict(
        # US = dict(
        #     country_url = '.uk.'
        #     ),
        GB = dict(
            language = 'EN', 
            currency = 'GBP',
            currency_sign = "\u00A3",
            country_url = '.uk.'

        ),

        DE = dict(
            language = '', 
            currency = 'EUR',
            thousand_sign = '.',
            currency_sign = "\u20AC",
            translate = {('.uk.','.de.')}

        ),
        DK = dict(
            language = 'DA', 
            currency = 'DKK',
            thousand_sign = '.',
            currency_sign = "DKK",
            translate = {('.uk.','.dk.')}

        ),
        )

        


