# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from lxml import etree
from utils.cfg import *
from urllib.parse import urljoin


class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        availability = checkout.extract_first()
        if availability and availability == 'in stock':
            return False
        else:
            return True

    def _sku(self, scripts, item, **kwargs):
        script = scripts.extract_first()
        data = json.loads(script.split('window.__PRELOADED_STATE__ =')[-1].split('window.__SITE_FEATURES')[0].rsplit(';',1)[0])
        for key,value in list(data['products']['details']['cachedProducts'].items()):
            item['sku'] = key
            item['tmp'] = value

    def _sizes(self, data, item, **kwargs):
        orisizes = item['tmp']['sizes']
        size_li = []
        for osize in orisizes:
            size_tag = osize['scaleAbbreviation']
            size = osize['name']
            if size_tag and size.isdigit():
                size = size_tag.strip() + size
            size_li.append(size)
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//*[@data-test="product-price"]/text()').extract()[0]
            saleprice = prices.xpath('.//*[@data-test="product-salePrice"]/text()').extract()[0]
        except:
            listprice = prices.xpath('.//*[@data-test="product-price"]/text()').extract()[0]
            saleprice = prices.xpath('.//*[@data-test="product-price"]/text()').extract()[0]
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _description(self, descs, item, **kwargs):
        details = descs.xpath('.//div[@id="description-info-content"]//text() | .//div[@id="details-info-content"]//ul/li/text()').extract()
        desc_li = []
        for desc in details:
            desc = desc.strip()
            if not desc or '--td' in desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description.replace(':\n',': ')

    def _images(self, images, item, **kwargs):
        images = []
        primary = item['tmp']['resources']['primary']['sources']['600']
        images.append(primary)
        secondary = item['tmp']['resources']['secondary']['sources']['600']
        images.append(secondary)
        for detail in item['tmp']['resources']['details']:
            images.append(detail['sources']['600'])
        item['images'] = images
        item['cover'] = images[0]

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?pageIndex=%s'%(i)
        return url

    def _parse_item_url(self, response, **kwargs):
        pages = int(response.xpath('//li[@class="_1u_Px"]//a[@class="_301yh"]/text()').extract()[-1])
        for x in range(1, pages+1):
            url = response.url.split('?')[0] + '?pageindex='+str(x)
            result = getwebcontent(url)
            html = etree.HTML(result)
            products = html.xpath('//a[@data-test="ProductListingPage-productLink"]/@href')
            for quote in products:
                href = quote
                url =  urljoin(response.url, href)
                yield url,''

    def _parse_images(self, response, **kwargs):
        script = response.xpath('//script[contains(text(),"window.__PRELOADED_STATE__")]/text()').extract_first()
        data = json.loads(script.split('window.__PRELOADED_STATE__ =')[-1].split('window.__SITE_FEATURES')[0].rsplit(';',1)[0])

        for key,value in list(data['products']['details']['cachedProducts'].items()):
            source = value
        images = []
        primary = source['resources']['primary']['sources']['600']
        images.append(primary)
        secondary = source['resources']['secondary']['sources']['600']
        images.append(secondary)
        for detail in source['resources']['details']:
            images.append(detail['sources']['600'])

        return images

_parser = Parser()



class Config(MerchantConfig):
    name = 'modes'
    merchant = 'Modes'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout', ('//*[@property="product:availability"]/@content', _parser.checkout)),
            ('sku', ('//script[contains(text(),"window.__PRELOADED_STATE__")]/text()', _parser.sku)),
            ('name', '//p[@itemprop="name"]/text()'),
            ('designer', '//div[@itemprop="brand"]/a/text()'),
            ('color', '//meta[@property="product:color"]/@content'),
            ('description', ('//html',_parser.description)),
            ('image',('//html',_parser.images)),
            ('sizes',('//html',_parser.sizes)),
            ('prices',('//html',_parser.prices)),
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        designer = dict(
            ),
        )



    list_urls = dict(
        f = dict(
            a = [
                'https://www.modes.com/us/shopping/woman/accessories?pageIndex=',
            ],
            b = [
                'https://www.modes.com/us/shopping/woman/bags?pageIndex=',
            ],
            s = [
                'https://www.modes.com/us/shopping/woman/shoes?pageIndex=',
            ],
            c = [
                'https://www.modes.com/us/shopping/woman/clothing?pageIndex=',
            ],
        ),
        m = dict(
            a = [
                'https://www.modes.com/us/shopping/man/accessories?pageIndex=',
            ],
            b = [
                'https://www.modes.com/us/shopping/man/bags?pageIndex=',
            ],
            s = [
                'https://www.modes.com/us/shopping/man/shoes?pageIndex=',
            ],
            c = [
                'https://www.modes.com/us/shopping/man/clothing?pageIndex='
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'www.',
    )

    countries = dict(
        US = dict(
            language = 'EN',
            currency = 'USD',
            currency_sign = '$',
            country_url = '/us/'
            ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/gb/',
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = '/cn/',
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = '/jp/',
        ),
        KR = dict(
            currency = 'KRW',
            currency_sign = '\u20a9',
            country_url = '/kr/',
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/sg/',
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '/hk/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/ca/',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '/au/',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = '/de/',
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = '\u20bd',
            thousand_sign = ' ',
            country_url = '/ru/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            thousand_sign = ' ',
            country_url = '/no/',
        ),

        )

        


