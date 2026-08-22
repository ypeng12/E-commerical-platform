from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first()
        item['designer'] = 'PIMAX'

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            image = img.replace('http:','https:')
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _color(self, data, item, **kwargs):
        item['color'] =  ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = ''

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = ['One Size']

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./del//span/text()').extract()[1]
        saleprice = prices.xpath('./ins//span/text() | .//span/text()').extract()[1]
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
        images = []
        for img in imgs:
            image = img.replace('http:','https:')
            images.append(image)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()


class Config(MerchantConfig):
    name = 'pimax'
    merchant = 'Pimax'

    path = dict(
        base = dict(
            ),
        plist = dict(
            ),
        product = OrderedDict([
            ('checkout', ('//option[@disabled="disabled"]', _parser.checkout)),
            ('sku', ('//div[@data-elementor-type="product-post"]/@data-elementor-id', _parser.sku)),
            ('name', '//h1[@itemprop="name"]/text() | //div[@class="wooco_component_product_name"]/text()'),
            ('images', ('//meta[@property="og:image"]/@content', _parser.images)),
            ('color',('//*[@class="product-color"]/text',_parser.color)),
            ('description', ('//div[@class="origin-content"]/ul/li/text()',_parser.description)), # TODO:
            ('sizes', ('//*[@id="va-size"]/option/text()', _parser.sizes)),
            ('prices', ('//div[@class="price-wrapper"]/p', _parser.prices))
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
        u = dict(
            a = [
            ]
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),
        )
        


