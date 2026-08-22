from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
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

    def _name(self, res, item, **kwargs):
        tmp_data = res.extract_first().split('window.product = ')[1]
        item['tmp'] = json.loads(tmp_data)
        item['name'] = item['tmp']['title'].upper()
        item['designer'] = item['tmp']['vendor'].upper()

        description = etree.HTML(item['tmp']['description'])
        item['description'] = "\n".join(description.xpath('//*/text()')[0])


    def _images(self, res, item, **kwargs):
        img_li = res.extract()
        images = []
        for img in img_li:
            if img not in images and 'https:' not in img:
                images.append('https:' + img)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, res, item, **kwargs):
        sizes_li = []
        for size in item['tmp']['variants']:
            if size['available']:
                sizes_li.append(size['option2'])
        item['originsizes'] = sizes_li

    def _prices(self, prices, item, **kwargs):
        saleprice = str(item['tmp']['price'])[:-2] + '.' + str(item['tmp']['price'])[-2:]
        listprice = str(item['tmp']['price_max'])[:-2] + '.' + str(item['tmp']['price_max'])[-2:]
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_multi_items(self,response,item,**kwargs):
        color_datas = set()
        variants = item['tmp']['variants']
        for variant in variants:
            color_datas.add(variant['option1'])
        for color_data in color_datas:
            item_color = deepcopy(item)
            images_li = []
            sizes_li = []
            for variant in variants:    
                if color_data == variant['option1']:
                    item_color['color'] = color_data.upper()
                    item_color['sku'] = variant['featured_image']['src'].split('.jpg?v=')[1]

                    if variant['available']:
                        sizes_li.append(variant['option2'] if variant['option2'] else 'IT')
                    item_color['originsizes'] = sizes_li
                    self.sizes(sizes_li, item_color, **kwargs)

                images = item['tmp']['media']
                for image in images:
                    if color_data == image['alt'].split(' | ')[0].strip() and image not in images_li:
                        images_li.append(image['src'])
                item_color['images'] = images_li[:4]
                item_color['cover'] = item_color['images'][0]
            yield item_color

    def _parse_images(self, response, **kwargs):
        jsonimg_li = response.xpath('//script[contains(text(),"window.product")]/text()').extract_first()
        image_json = json.loads(jsonimg_li.split('window.product = ')[1])
        colors = set()
        images = []
        for col in image_json['variants']:
            colors.add(col['option1'])
        for image in image_json['variants']:
            if len(colors) == 1:
                images.append(image['featured_image']['src'])
            else:
                for color in colors:
                    for media in image_json['media']:
                        if color == media['alt'].split(' | ')[0].strip() and image not in images:
                            images.append(media['src'])
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and 'Dimensions' in info.strip():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()


class Config(MerchantConfig):
    name = 'gorjana'
    merchant = "gorjana"

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="collection-product"]',
            designer = './a/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="AddToCart"]/text()', _parser.checkout)),
            ('name', ('//script[contains(text(),"window.product")]/text()',_parser.name)),
            ('prices', ('//div[contains(@class,"product_price")]', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@itemprop="description"]//text()',   
            ),
        )
    list_urls = dict(
        f = dict(
            a = [
                'https://gorjana.com/collections/best-sellers'
            ],
        ),
    )

    parse_multi_items = _parser.parse_multi_items

    countries = dict(
        US = dict(
            language = 'EN', 
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD'
        ),

        )
