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
        num_data = data.lower().strip().split('result')[0].strip()
        count = int(num_data)
        page_num = count / 50 + 1
        return page_num

    def _list_url(self, num, response_url, **kwargs):
        url = urljoin(response_url.split('?')[0], '?page=%s'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first()
        item['sku'] = sku if sku and sku.isdigit() else ''

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        item['color'] = item['color'].upper() if item['color'].upper() != 'NO COLOR' else ''

    def _sizes(self, sizes, item, **kwargs):
        osizes = sizes.extract()
        size_li = []
        for osize in osizes:
            if osize.strip() and osize.strip() not in size_li:
                size_li.append(osize.strip())
        if item['category'] in ['a','b'] and not size_li:
            size_li = ['IT']
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        price = prices.extract_first()
        item['originlistprice'] = price
        item['originsaleprice'] = price

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//ul[@class="thumbnails"]/li/div/img/@data-main_image').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="total-results"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'olivela'
    merchant = 'Olivela'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="total-results"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//a[@class="content"]',
            designer = './div[@class="designer-name"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[text()=" Add to Bag "]', _parser.checkout)),
            ('sku',('//span[@itemprop="productID"]/text()',_parser.sku)),
            ('images',('//ul[@class="thumbnails"]/li/div/img/@data-main_image',_parser.images)), 
            ('designer', '//h1/a/text()'),
            ('name', '//h1/div[@class="product-subname"]/text()'),
            ('color','//span[@id="selected-color-name"]/text()'),
            ('description', ('//div[@id="itemDetails"]//div[@class="description"]//text()',_parser.description)),
            ('prices', ('//span[@itemprop="price"]/@content', _parser.prices)),
            ('sizes',('//ul[@id="sizeDropdown"]/li/a/text()',_parser.sizes)),
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
        u = dict(
            a = [
                'https://www.olivela.com/home?page=1'
            ]
        ),
        f = dict(
            a = [
                'https://www.olivela.com/women/accessories?page=1',
                'https://www.olivela.com/jewelry?page=1'
            ],
            b= [
                'https://www.olivela.com/women/bags?page=1'
            ],
            c = [
                'https://www.olivela.com/women/clothing?page=1',
            ],
            s = [
                'https://www.olivela.com/women/shoes?page=1'
            ],

            e = [
                "https://www.olivela.com/beauty?page=1"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            country_url = '/us/',
            
            )
        )

        


