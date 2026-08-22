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

    def _sku(self, res, item, **kwargs):
        scripts = res.extract_first()
        data = json.loads(scripts.split('window.SwymProductInfo.product =')[1].split('window.SwymProductInfo.variants = window.SwymProductInfo.product.variants;')[0].strip().strip(';'))
        item['tmp'] = data
        sku_size = data['variants'][0]['option2']
        sku_tmp = data['variants'][0]['sku']
        sku = sku_tmp.rsplit(sku_size,1)[0] if sku_tmp.endswith(sku_size) else ''
        item['sku'] = sku

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['title'].upper()
        item['designer'] = item['tmp']['vendor'].upper()
        item['color'] = item['tmp']['variants'][0]['option1']
        desc_xml = item['tmp']['description']
        description = etree.HTML(desc_xml)
        item['description'] = description.xpath('//*/text()')

    def _images(self, images, item, **kwargs):
        img_li = item['tmp']['images']
        images = []
        for img in img_li:
            if img not in images and 'https:' not in img:
                images.append('https:' + img)
        item['cover'] = 'https:' + item['tmp']['featured_image']
        item['images'] = images

    def _sizes(self, sizes_data, item, **kwargs):
        sizes_li = []
        for size in item['tmp']['variants']:
            if size['available']:
                sizes_li.append(size['option2'])
        item['originsizes'] = sizes_li

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('./span[@class="price"]/text()').extract_first()
        listprice = prices.xpath('./span[@class="original_price"]/text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _parse_images(self, response, **kwargs):
        img_json = response.xpath('//script[@id="swym-snippet"]/text()').extract_first()
        img_data = json.loads(img_json.split('window.SwymProductInfo.product =')[1].split('window.SwymProductInfo.variants = window.SwymProductInfo.product.variants;')[0].strip().strip(';'))
        images = []
        for img in img_data['images']:
            img = 'https:' + img.split('?')[0]
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
    name = 'simkhai'
    merchant = "SIMKHAI"

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="collection-product"]',
            designer = './a/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@aria-label="Add to cart"]/text()', _parser.checkout)),
            ('sku', ('//script[@id="swym-snippet"]/text()',_parser.sku)),
            ('name', ('//html',_parser.name)),
            ('images', ('//html', _parser.images)),
            ('prices', ('//div[contains(@class,"product_price")]', _parser.prices)),
            ('sizes', ('//html', _parser.sizes))
            ]),
        look = dict(
            ),
        swatch = dict(
            
            ),
        image = dict(
            method=_parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@itemprop="description"]//text()',   
            ),
        )
    list_urls = dict(
        f = dict(
            c = [
                'https://jonathansimkhai.com/collections/shop-all/?p='
            ],
        ),
    )


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
        


