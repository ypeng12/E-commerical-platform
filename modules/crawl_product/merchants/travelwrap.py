from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):


    def _sku(self, data, item, **kwargs):
        data = data.extract()
        item['sku'] = ''
        for d in data:
            if 'sku' in d:
                item['sku'] = d.split('"sku":"')[-1].split('"')[0]


    def _designer(self, data, item, **kwargs):
        item['designer'] = 'THE TRAVELWRAP COMPANY'

    def _sizes(self, sizes, item, **kwargs):
        
        item['originsizes'] = ['IT']


    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//p[@class="special-price"]/span[@class="price"]/text()').extract_first()
        listPrice = prices.xpath('.//p[@class="old-price"]/span[@class="price"]/text()').extract_first()
        if not salePrice:
            salePrice =  prices.xpath('.//span[@class="regular-price"]/span[@class="price"]/text()').extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else salePrice
        item['originsaleprice'] = item['originsaleprice'].strip()
        item['originlistprice'] = item['originlistprice'].strip() 

    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@class="detail-overview"]//text()').extract() + description.xpath('.//div[@class="prod-det-con"]/text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description
        item['color'] = ''
        if 'Palette:' in description:
            item['color'] = description.split('Palette:')[-1].split('\n')[0]


    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        img_li = []
        for img in images:
            if img not in img_li and img != '#':
                img_li.append(img)
        item['images'] = img_li



_parser = Parser()



class Config(MerchantConfig):
    name = 'travelwrap'
    merchant = 'The Travelwrap Company'

    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//li[@class="item"]',
            designer = './/div[@class="product_grid_brand"]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('sku', ('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('name', '//div[@class="product-name"]/h1/text()'),    # TODO: path & function
            ('designer', ('//html',_parser.designer)),
            ('description', ('//html',_parser.description)),
            ('image',('//div[@class="MagicToolboxSelectorsContainer"]/a/@href',_parser.images)),
            ('sizes',('//html',_parser.sizes)),
            ('prices',('//div[@class="price-box"]',_parser.prices)),
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//ul[@id="pdp_angle"]/li[not(@class="no-display")]/a/@href',
            ),
        size_info = dict(
            ),
        designer = dict(
            ),
        )



    list_urls = dict(
        f = dict(
            c = [
                "https://www.thetravelwrapcompany.com/us/all-travelwraps.html?p="

            ],
        ),
        m = dict(
            a = [
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
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = '/us/',
            currency_sign = '$',
            ),

        GB = dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/',
            currency_sign = "\u00A3",
        ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            country_url = '/ca/',
            currency_sign = 'C$',
        ),

        # Have different Store then US
        AU = dict(
            area = 'AU',
            currency = 'AUD',
            currency_sign = 'A$',
            country_url = '/au/',
        ),

        DE = dict(
            area = 'GB',
            currency = 'EUR',
            country_url = '/eu/',
            currency_sign = "\u20AC"
        ),

        )

        


