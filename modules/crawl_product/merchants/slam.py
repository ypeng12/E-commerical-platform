from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json

class Parser(MerchantParser):
    def _checkout(self,res,item,**kwargs):
        if res:
            return False
        else:
            return True

    def _sku(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        item['color'] = json_data['model'][0]['color'].upper()
        sku = json_data['@id'].split('#product')[0].split('-')[-1].upper()
        if sku.startswith('J'):
            item['sku'] = sku
        else:
            item['sku'] = ''

    def _sizes(self,res,item,**kwargs):
        sizes_data = item['tmp']['model']
        sizes_li = []
        for size in sizes_data:
            if 'InStock' in size['offers']['availability']:
                sizes_li.append(size['additionalProperty'][0]['value'])
        item['originsizes'] = sizes_li

    def _prices(self,res,item,**kwargs):
        item['originlistprice'] = str(item['tmp']['offers']['highPrice'])
        item['originsaleprice'] = str(item['tmp']['offers']['lowPrice'])

    def _description(self,res,item,**kwargs):
        descs = item['tmp']['description']
        desc_str = []
        for desc in descs:
            if desc.strip():
                desc_str.append(desc.strip())
        item['description'] = desc

    def _images(self, images, item, **kwargs):
        images = images.extract()
        img_li = []
        for img in images:
            img = 'https:' + img
            if img not in img_li:
                img_li.append(img)
        item['images'] = img_li
        item['cover'] = img_li[0]
        
    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-single__photo--container"]/div[contains(@class,"product-single__photo-wrapper")]/img[@class="product-single__photo lazyload"]/@src').extract()
        images = []

        for img in imgs:
            image = 'https:' + img if 'http' not in img else img
            if '_800x' not in image or image in images:
                continue
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
    name = "slam"
    merchant = "Slam Jam"

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="pdp-link"]',
            designer = './a/span[@itemprop="name"]/text()',
            link = './a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//button[@id="AddToCart-product-template"]/span/text()',_parser.checkout)),
            ('name','//div[@class="product-details"]/div[@class="product-details__sx"]/div/h1[@class="product-title"]/text()'),
            ('sku', ('//script[@data-desc="seo-product"]/text()', _parser.sku)),
            ('designer','//div[@class="product-details"]/div[@class="product-details__sx"]/div/h2[@class="product-vendor"]/a/text()'),
            ('description',('//div[@class="descr descr--long"]/ul/li/text()',_parser.description)),
            ('prices',('//div[@class="price"]',_parser.prices)),
            ('image',('//div[@class="product-single__photo--container"]/div[contains(@class,"product-single__photo-wrapper")]/img[@class="product-single__photo lazyload"]/@src',_parser.images)),
            ('sizes', ('//select[@id="select-prenotation"]', _parser.sizes))
        ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            image_path = '//div[@class="product-details__images slider"]',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@itemprop="description"]//p/text()',
            ),
        checknum = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.slamjam.com/en_US/woman/accessories?page="
            ],
            c = [
                "https://www.slamjam.com/en_US/woman/clothing?page=",
            ],
            s = [
                "https://www.slamjam.com/en_US/woman/footwear?page="
            ]
        ),
        m = dict(
            a = [
                "https://www.slamjam.com/en_US/man/accessories?page="
            ],
            c = [
                "https://www.slamjam.com/en_US/man/clothing?page=",
                "https://www.slamjam.com/en_US/man/uniforms?page="
            ],
            s = [
                "https://www.slamjam.com/en_US/man/footwear?page="
            ],
            h = [
                "https://www.slamjam.com/en_US/man/lifestyle?page="
            ]
        )
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,
            country_url = 'en_US',
            ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'en_GB',
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = "A$",
            country_url = 'en_AU',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'en_IT',
        ),
    )