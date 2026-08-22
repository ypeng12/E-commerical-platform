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
        if "InStock" in checkout.extract_first():
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = 5
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=', '?page=%s'%i)
        return url

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first().split('var productObj = ')[1].split('// MERGE : Overwrite parent product variants')[0].rsplit(';',1)[0])
        item['tmp'] = json_data
        item['name'] = json_data['title'].upper()
        item['designer'] = json_data['vendor']
        item['description'] = json_data['description'].replace('<p>','').replace('</p>','')
        item['color'] = json_data['variants'][0]['option1']

    def _images(self, images, item, **kwargs):
        img_li = item['tmp']['images']
        images = []
        for img in img_li:
            img = 'https:' + img.split('?')[0]
            if img not in images and '_sw.jpg' not in img:
                images.append(img)
        item['images'] = images
        item['cover'] = "https:" + item['tmp']['featured_image']

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = item['tmp']['variants']
        size_li = []
        for size in sizes:
            if size['available']:
                size_li.append(size['option2'])
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('./span[@itemprop="price"]/span/text()').extract_first()
        listprice = prices.xpath('./span[@class="was"]/span/text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

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
    name = 'blanknyc'
    merchant = 'BlankNYC'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="bc-sf-filter-product-bottom"]',
            designer = './p[1]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@id="product-details--wrapper"]/link/@href', _parser.checkout)),
            ('sku','//div[@class="nosto_product"]/span[@class="product_id"]/text()'),
            ('name', ('//script[@class="product-json"]/text()', _parser.name)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@id="product-price"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="product-image-container"]/div[contains(@class,"product-main-image")]/a/img[contains(@class,"product-image-content")]/@src'
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '',   
            ),
        )
    list_urls = dict(
        m = dict(
            c = [
                'https://www.blanknyc.com/collections/men?page='
            ],
        ),
        f = dict(
            c = [
                'https://www.blanknyc.com/collections/women?page='  
            ],
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            country_url = 'blanknyc.com'
        ),
        )


