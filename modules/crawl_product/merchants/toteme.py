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
            return False

    def _page_num(self, data, **kwargs):
        page_num = data
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract_first().split('var __st=')[1].rsplit(';',1)[0])
        item['sku'] = data['rid']

    def _name(self, data, item, **kwargs):
        json_data = json.loads(data.extract_first())
        item['tmp'] = json_data
        item['name'] = json_data['title']
        item['designer'] = json_data['vendor'].split(' - ')[0]
        description = json_data['description']
        desc = etree.HTML(description)
        item['description'] = desc.xpath('//text()')[0]

    def _images(self, images, item, **kwargs):
        datas = item['tmp']['images']
        images = []
        for image in datas:
            if "https" not in images:
                images.append("https:" + image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, data, item, **kwargs):
        json_data = item['tmp']
        sizes = []
        for size in json_data['variants']:
            if size['available']:
                sizes.append(size['option1'])
        item['originsizes'] = sizes

    def _prices(self, data, item, **kwargs):
        listprice = str(item['tmp']['compare_at_price'] if item['tmp']['compare_at_price'] else '')[:-2]
        saleprice = str(item['tmp']['price'])[:-2]

        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        json_data = json.loads(response.xpath('//script[@id="product-"]/text()').extract_first())
        images = []
        for img in json_data['images']:
            img = 'https:' + img
            if img not in images:
                images.append(img)
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
    name = 'toteme'
    merchant = "TOTÊME"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination"]/span//text()',_parser.page_num),
            items = '//div[@class="template-collection__body"]/div/div',
            designer = './a/@data-cy',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product-form__actions"]/div/button[@data-cy="addToCart"]/span/text()', _parser.checkout)),
            ('sku',('//script[@id="__st"]/text()',_parser.sku)),
            ('name', ('//script[@id="product-"]/text()',_parser.name)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
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
                'https://toteme-studio.com/collections/belts?page=',
                'https://toteme-studio.com/collections/hats?page=',
                'https://toteme-studio.com/collections/soft-accessories?page='
            ],
            b = [
                'https://toteme-studio.com/collections/bags?page='
            ],
            c = [
                'https://toteme-studio.com/collections/shop-all?page='  
            ],
            s = [
                'https://toteme-studio.com/collections/shoes?page='
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
            country_url = 'toteme-studio.com'
        ),
        DE = dict(
            currency = 'EUR',
            country_url = 'int.toteme-studio.com',
        ),
    )
        


