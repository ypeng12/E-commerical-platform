from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):
    # def _parse_multi_items(self, response, item, **kwargs):
    #     print response.body

    def _sku(self, skus, item, **kwargs):
        skus = skus.extract_first().upper()
        item['sku'] = skus
        item['designer'] = 'BLISS'

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            item['images'].append(img)
        item['cover'] = item['images'][0]


    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.strip()
        item['color'] = ''

    def _sizes(self, sizes, item, **kwargs):

        item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = prices.extract()[0]
        item['originlistprice'] = ''



    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//a[@class="productView-thumbnail-link"]/@href').extract() 
        images = []
        for img in imgs:
            images.append(img)


        return images
    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//figure[@class="card-figure"]//a/@href').extract())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = "bliss"
    merchant = "Bliss"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            items = '//figure[@class="card-figure"]',
            designer = './/a[@class="brand-name"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('sku',('//input[@name="product_id"]/@value',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('description', ('//div[@data-drop="bliss-long-description"]//li/text()',_parser.description)),
            ('prices', ('//span[@class="price price--withoutTax"]/text()', _parser.prices)),
            ('images',('//a[@class="productView-thumbnail-link"]/@href',_parser.images)), 
            ('sizes',('//html',_parser.sizes)),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    list_urls = dict(
        f = dict(

            e = [
          
                "https://www.blissworld.com/shop-all/cleansers-moisturizers/?p=",
                "https://www.blissworld.com/shop-all/masks-treatments/?p=",
                "https://www.blissworld.com/shop-all/bath-body/?p=",
                "https://www.blissworld.com/shop-all/hair-removal-firming/?p=",
                "https://www.blissworld.com/featured-products-2/?p="

            ],
        ),
        m = dict(
            s = [
                
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
            cur_rate = 1,   # TODO
            
        ),


        )

        


