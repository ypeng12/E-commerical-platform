from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.ladystyle import blog_parser

class Parser(MerchantParser):
    def _checkout(self, scripts, item, **kwargs):
        if "add to" in scripts.extract_first().lower():
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        sku = data.extract_first()
        if sku.isdigit():
            item['sku'] = sku
        else:
            item['sku'] = ''

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _color(self, res, item, **kwargs):
        color = res.extract()
        item['color'] = color[-1]

    def _sizes(self, sizes_data, item, **kwargs):
        if item['designer'].upper() == 'CHANEL PRE-OWNED':
            item['condition'] = 'p'
        size_li = []
        sizes = sizes_data.xpath(
            './/div[@class="detail__sizes"]//span[@class="detail__size-block"]//span/text()').extract()
        for size in sizes:
            size_li.append(size.strip())
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        originlistprice = prices.xpath('.//div[@itemprop="offers"]//span[@itemprop="price"]/text()').extract_first()
        if originlistprice.strip():
            originsaleprice = originlistprice
        else:
            originlistprice = prices.xpath('.//div[@itemprop="offers"]//span[@itemprop="price"]//span[@class="detail__price--old ty-medium"]/text()').extract_first()
            originsaleprice = prices.xpath('.//div[@itemprop="offers"]//span[@itemprop="price"]//span[@class="detail__price--new ty-medium -d-ml--xxs js-product-price"]/text()').extract_first()
        item['originsaleprice'] = originsaleprice.strip().split()[-1]
        item['originlistprice'] = originlistprice.strip().split()[-1]

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0]+'?p=' + str((i))
        return url

    def _parse_blog(self, response, **kwargs):
        html_origin = response.xpath('//div[@class="std"]').extract_first().encode('utf-8')
        title = response.xpath('//h1/text()').extract_first()
        title = title if title else response.xpath('//span[@class="h2"]/text()').extract_first()
        title = title.strip() if title else ''
        key = response.url.split('?')[0].split('/')[-1]
        cover = response.xpath('//div[@class="page-builder-module module1 full-width"]/span/@data-image-desktop').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        images = {"type": "image","alt": ""}
        images['src'] = cover
        html_parsed['items'].append(images)
        imgs_set = []

        for node in response.xpath('//div[@class="std"]/div[contains(@class,"page-builder-module")]/* | //div[@class="std"]/div[@class="hide-content-from-mobile"]/*'):
            txts = node.xpath('.//p | .//td/text()').extract()
            for text in txts:
                if text.strip():
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text.strip()
                    html_parsed['items'].append(texts)

            imgs = node.xpath('.//img/@src | .//span/@data-image-desktop').extract()
            for img in imgs:
                if img not in imgs_set:
                    imgs_set.append(img)
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="items-count"]//strong/text()').extract_first().strip().replace(',','').lower())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'tessabit'
    merchant = 'Tessabit'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@class="pager-container"]//span[@class="number"]/text()',
            list_url = _parser.list_url,
            items = '//div[@class="product-wrapper"]',
            designer = './/div[@class="h3 brand-name"]/text()',
            link = './/a[@class="product-image"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="ty-customheader--h3-squeezed"]/text()', _parser.checkout)),
            ('name', '//div[@class="col-xs-12"]//h3/text()'),
            ('designer','//div[@class="col-xs-12"]//span[@itemprop="name"]/text()'),
            ('images', ('//div[@class="detail__sidescroller"]//img[@class="image lazyload"]/@data-srcset', _parser.images)),
            ('sku', ('//input [@id="idProdotto"]/@value', _parser.sku)),
            ('color',('//div[@class="ty-customheader--h3-squeezed -d-mb--xs"]//span/text()', _parser.color)),
            ('description', '//meta[@name="description"]/@content'), # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="product-gallery-carousel"]//a[@class="product-image"]/@href',
            ),
        size_info = dict(
            ),
        blog = dict(
            official_uid=228301,
            link = '//div[@class="page-builder-module module7 half-width"]/a/@href',         
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.tessabit.com/us/man/accessories/?p=',
            ],
            b = [
                'https://www.tessabit.com/us/man/bags/?p=',
            ],
            c = [
                'https://www.tessabit.com/us/man/clothing/?p=', 

            ],
            s = [
                'https://www.tessabit.com/us/man/shoes/?p=',
            ],
        ),
        f = dict(
            a = [
                'https://www.tessabit.com/us/woman/accessories/?p=',
            ],
            b = [
                'https://www.tessabit.com/us/woman/bags/?p=',
            ],
            c = [
                'https://www.tessabit.com/us/woman/clothing/?p=', 

            ],
            s = [
                'https://www.tessabit.com/us/woman/shoes/?p=',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )

    blog_url = dict(
        EN = ['https://www.tessabit.com/cn/the-edit-en/?p=']
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/us/',
        ),
        CN = dict(
            currency = 'CNY',
            country_url = '/cn/',
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '/jp/',
        ),
        KR = dict( 
            currency = 'KRW',
            country_url = '/kr/',
            discurrency = 'USD',    
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '/hk/',
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/row/',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/gb/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/row/',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '/au/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/de/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency ="EUR",
            country_url = '/roe/',
        ),
        )
        
