from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        page_num = response.xpath('//div[@class="toolbar-top"]//div[@class="amount"]/p/text()').extract_first().strip()
        nums = int(page_num.split('of')[1].split('items')[0].strip())
        num = nums // 24
        return num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?p=1', '?p=%s'%i)
        return url

    def _parse_item_url(self, response, **kwargs):
        list_url = json.loads(response.xpath('//script[contains(text(),"numberOfItems")]/text()').extract_first().strip())
        for url in list_url['itemListElement']:
            yield url['url'],'thedoublef'

    def _checkout(self, checkout, item, **kwargs):
        checkout_json = json.loads(checkout.extract_first())
        item['tmp'] = checkout_json
        if 'in stock' in checkout_json['offers']['availability'] or 'InStock' in checkout_json['offers']['availability']:
            return False
        else:
            return True

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in images.extract():
            if image not in image_li:
                image_li.append(image)
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./div[contains(@class,"old-price")]/span/span/span/text()').extract_first()
        saleprice = prices.xpath('./div[contains(@class,"final-price")]/span/span/span/text()').extract_first()
        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _sku(self,res,item,**kwargs):
        code = item['url'].rsplit('/')[-2].split('-')[-4:]
        item["sku"] = '-'.join(code).upper()

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['name']
        item['designer'] = item['tmp']['brand']

    def _sizes(self,res,item,**kwargs):
        size_code = res.xpath('//form[@id="product_addtocart_form"]/input[@name="product"]/@value').extract_first()
        size_url = 'https://www.thedoublef.com/us_en/catalog/product/sizes?products={}'
        resp = requests.get(size_url.format(size_code))
        sizes = json.loads(resp.text)
        sizes_li = []
        for size in sizes[size_code]:
            if size['in_stock']:
                sizes_li.append(size['size_label'])
        item['originsizes'] = sizes_li

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="selectors hidden"]//img/@src').extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return image_li

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
    name = "Thedoublef"
    merchant = "thedoublef"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"numberOfItems")]/text()', _parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            ),
        product=OrderedDict([
            ('checkout',('//script[@type="application/ld+json"]/text()',_parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('name', ('//html', _parser.name)),
            ('color','//span[@class="product-color-active text-3xs"]/text()'),
            ('price',('//div[@class="price-container"]',_parser.prices)),
            ('description','//div[@class="product-description text-sm leading-relaxed"]/text()'),
            ('images', ('//div[@class="selectors hidden"]//img/@src | //div/img[contains(@class,"product-photo")]/@src', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-description text-sm leading-relaxed"]/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.thedoublef.com/us_en/woman/accessories/?page=1',
            ],
            b = [
                'https://www.thedoublef.com/us_en/woman/bags/?page=1',
            ],
            c = [
                'https://www.thedoublef.com/us_en/woman/clothing/?page=1',
            ],
            s = [
                'https://www.thedoublef.com/us_en/woman/shoes/?page=1',
            ]
        ),
        m = dict(
            a = [
                'https://www.thedoublef.com/us_en/man/accessories/?page=1',
            ],
            b = [
                'https://www.thedoublef.com/us_en/man/bags/?page=1',
            ],
            c = [
                'https://www.thedoublef.com/us_en/man/clothing/?page=1',
            ],
            s = [
                'https://www.thedoublef.com/us_en/man/shoes/?page=1',
                'https://www.thedoublef.com/us_en/man/sneakers-hub/?page=1'
            ]
        )
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '/en_us/',       
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/de_en/'
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/uk_en/'
        ),
    )