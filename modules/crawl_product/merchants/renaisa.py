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
        page_num = int(10)

        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _sku(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        item['sku'] = json_data['sku']
        item['name'] = json_data['name'].upper()
        item['designer'] = json_data['brand']['name'].upper()
        item['color'] = ''

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
        sizes_data = item['tmp']['offers']
        size_li = []
        for size in sizes_data:
            if "InStock" in size['availability']:
                size_li.append(size['name'])

        item['originsizes'] = size_li

    def _images(self, data, item, **kwargs):
        img_li = data.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append("https:" + img)

        item['cover'] = images[0]
        item['images'] = images

    def _prices(self, prices, item, **kwargs):
        salePrice = str(item['tmp']['offers'][0]['price'])
        listPrice = str(item['tmp']['offers'][0]['price'])

        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice

    def _parse_images(self, data, **kwargs):
        img_li = data.xpath('//div[@data-media-type="image"]/div//noscript/img/@src').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append("https:" + img)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info not in fits:
                fits.append(info.strip())

        size_info = '\n'.join(fits)
        return size_info   

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="count-pr"]/text()').extract_first().strip().split(" ")[0].strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'renaisa'
    merchant = 'Renaisa'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/div[contains(@class,"ProductItem__Info")]/h2/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-action="add-to-cart"]/span/text()', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"][contains(text(),"offers")]/text()', _parser.sku)),
            ('images', ('//div[@data-media-type="image"]/div//noscript/img/@src', _parser.images)),
            ('description', ('//div[@class="Collapsible__Content"]/div/ul/li/text()',_parser.description)), # TODO:
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
            size_info_path = '//div[@class="Collapsible__Inner"]/div/div[@class="Rte"]/ul/li/text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            c = [
                'https://www.renaisa.com/en-us/collections/atlein?page={}'
            ]

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = 'renaisa.com/',
        )
        )
        


