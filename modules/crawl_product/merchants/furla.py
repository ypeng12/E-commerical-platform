from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from copy import deepcopy
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = json.loads(checkout.extract_first())
        if 'OutOfStock' in checkout['offers']['availability']:
            return True
        else:
            item['tmp'] = checkout
            return False

    def _color(self, colors, item, **kwargs):
        item['color'] = item['tmp']['color']
        item['url'] = item['tmp']['offers']['url']

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'FURLA'

    def _description(self, descs, item, **kwargs):
        descs = descs.extract()
        desc_li = []
        for desc in descs:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = images[0]

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        if item['category'] in ['c','s']:
            for osize in sizes_data.extract():
                item['originsizes'].append(osize.strip())
        else:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            saleprice = prices.xpath('.//span[@class="price-sales"]/text()').extract()[0]
            listprice = prices.xpath('.//span[@class="price-standard"]/text()').extract()[0]
        except:
            saleprice = prices.xpath('.//span[@class="price-sales"]/text()').extract()[0]
            listprice = prices.xpath('.//span[@class="price-sales"]/text()').extract()[0]

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//picture[@class="primary-image lazyload"]/source[@type="image/jpeg"]/@srcset').extract()

        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        return images

    def _page_num(self, data, **kwargs):
        page_num = 30
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?section=' + str(i)
        return url
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="results-hits"]/text()[last()]').extract_first().strip().lower().replace('results','').replace('showing','').replace('\n','').strip())
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = 'furla'
    merchant = "FURLA"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"product-tile")]',
            designer = './/span[@class="designer"]/text()',
            link = './/a[@class="thumb-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('sku', '//div/@data-pid'),
            ('designer', ('//h1/text()',_parser.designer)),
            ('name', '//div[@class="product-name"]/text()'),
            ('images', ('//picture[@class="primary-image lazyload"]/source[@type="image/jpeg"]/@srcset', _parser.images)),
            ('color',('//div[@class="row product-variation"]//div/span/text()',_parser.color)),
            ('description', ('//*[@class="product-description"]//text()',_parser.description)),
            ('sizes', ('//select[@id="va-size"]/option[contains(@value,"size")]/text()', _parser.sizes)),
            ('prices', ('//div[@class="product-price"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[contains(@class,"HTMLListColorSelector")]//ul/li/@data-ytos-color-model',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="small-6 colums"]//text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.furla.com/us/en/eshop/women/accessories/",
                "https://www.furla.com/us/en/eshop/women/small-leather-goods/",
            ],
            b = [
                "https://www.furla.com/us/en/eshop/women/bags/",
                "https://www.furla.com/us/en/eshop/women/wallets/",
            ],
            s = [
                "https://www.furla.com/us/en/eshop/women/accessories/shoes/",
            ],
        ),
        m = dict(
            a = [
                "https://www.furla.com/us/en/eshop/mens/accessories/",
            ],
            b = [
                "https://www.furla.com/us/en/eshop/mens/bags-%26-backpack/",
            ],


        params = dict(
            ),
        ),

    )


    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '.com/us/'
        ),
        CN = dict(
            area = 'AS',
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = '.cn/cn/',
            translate = [
                ('/women/bags/','/woman/woman-bags/'),
                ('/women/wallets/','/woman/woman-bags/'),
                ('/women/small-leather-goods/','/woman/woman-slg/'),
                ('/women/accessories/','/woman/woman-accessories/'),
                ('/women/accessories/shoes/','/woman/woman-shoes/'),
                ('/mens/accessories/','/man/man-accessories/'),
                ('/mens/accessories/','/man/man-slg/'),
                ('/mens/bags-%26-backpack/','/man/man-bags/'),
            ]
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '.com/gb/',
            translate = [
                ('/women/bags/','/woman/woman-bags/'),
                ('/women/wallets/','/woman/woman-bags/'),
                ('/women/small-leather-goods/','/woman/woman-slg/'),
                ('/women/accessories/','/woman/woman-accessories/'),
                ('/women/accessories/shoes/','/woman/woman-shoes/'),
                ('/mens/accessories/','/man/man-accessories/'),
                ('/mens/accessories/','/man/man-slg/'),
                ('/mens/bags-%26-backpack/','/man/man-bags/'),
            ]
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '.com/de/',
            thousand_sign = '',
            translate = [
                ('/women/bags/','/woman/woman-bags/'),
                ('/women/wallets/','/woman/woman-bags/'),
                ('/women/small-leather-goods/','/woman/woman-slg/'),
                ('/women/accessories/','/woman/woman-accessories/'),
                ('/women/accessories/shoes/','/woman/woman-shoes/'),
                ('/mens/accessories/','/man/man-accessories/'),
                ('/mens/accessories/','/man/man-slg/'),
                ('/mens/bags-%26-backpack/','/man/man-bags/'),
            ]
        )
        )
        


