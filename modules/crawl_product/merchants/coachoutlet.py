# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils import utils
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        # data = json.loads(checkout.extract()[-1])
        # if 'offers' not in data['hasVariant']:
        #     return True
        if 'Add to Bag' in checkout.extract_first():
            # item['error'] = 'ignore' # just checkout
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        data = data.extract_first()
        if data and '_a0' in data:
            item['sku'] = data.split('?')[0].split('/')[-1].split('_a0')[0].strip().upper()
        else:
            item['sku'] = ''

    def _name(self, data, item, **kwargs):
        json_data = json.loads(data.extract_first())
        data = json_data['props']['pageProps']['pageData']
        item['name'] = data['name']
        item['color'] = data['defaultColor']['text']
        item['designer'] = 'COACH OUTLET'
        item['description'] = data['longDescription'].replace('<li> ','').replace('</li>', '')
        item['tmp'] = data

        if item['sku'] != data['id'].replace('-', '_'):
            item['error'] = 'ignore'
            return False

    def _images(self, res, item, **kwargs):
        images = item['tmp']['media']['thumbnails']
        imgs_li = []
        for image in images:
            imgs_li.append(image['src'])
        item['images'] = imgs_li
        item['cover'] = imgs_li[0]

    def _prices(self, prices, item, **kwargs):
        color_id = item['tmp']['defaultVariant']['id']
        variants = item['tmp']['variant']
        for variant in variants:
            if variant['id'] == color_id:
                for price_info in variant['pricingInfo']:
                    listprice = price_info['list']['formatted']
                    saleprice = price_info['sales']['formatted']
                    break

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _sizes(self, sizes, item, **kwargs):
        sizes_li = []
        color_id = item['tmp']['defaultVariant']['variationValues']['color']
        variants = item['tmp']['variant']
        for variant in variants:
            if variant['variationValues']['color'] == color_id and 'OutOfStock' not in variant['offers']['availability']:
                if 'size' in variant['variationValues'].keys():
                    sizes_li.append(variant['variationValues']['size'])
                else:
                    sizes_li = ['IT']

        item['originsizes'] = sizes_li

    def _parse_size_info(self, response, size_info, **kwargs):
        size_infos = response.xpath(size_info['size_info_path']).extract()
        fit = []
        for i in size_infos:
            if '"' in i:
                fit.append(i.strip())
        size_info = '\n'.join(fit)

        return size_info

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="element-wrapper"]/div/img/@src').extract()
        return images
    
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//input[@id="result-count"]/@value').extract_first().strip())
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = "coachoutlet"
    merchant = "Coach Outlet"
    # url_split = False


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="products-view visible-xs row"]//span[contains(text(),"of")]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="search-result-content row"]/div//div[@class="product-image"]',
            designer = './/h5[@class="brand-name function-bold"]/text()',
            link = './a[@itemprop="url"]/@href',
            ),
        product = OrderedDict([
            # ('checkout',('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('checkout',('//button[@id="add-to-cart"]/text()', _parser.checkout)),
            ('sku', ('//link[@as="image"]/@href', _parser.sku)),
            ('name', ('//script[@id="__NEXT_DATA__"]/text()', _parser.name)),
            ('images',('//html',_parser.images)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//select[@id="control-select-size"]/option[contains(@value,"coach")]/@data-attr-value',_parser.sizes)),
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
            size_info_path = '//div[@class="pdp-info__details-content"]/ul/li/text()',
            ),
        blog = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
        ),
        m = dict(
        )
    )

    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
            ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            discurrency = 'USD',
        )
        )
