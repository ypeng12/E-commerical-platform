from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = 5
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i)
        url = response_url.split('?')[0] + '?page=%s'%(num)
        return url

    def _images(self, images, item, **kwargs):
        colorCode = item['color'].replace('/','').upper().replace(" ",'').strip().split('-')[0]
        imgs = images.xpath('.//div[contains(@class,"'+colorCode+'")]//img/@src').extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
            if not cover and "_FRONT.jpg" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        
    def _sku(self, sku_data, item, **kwargs):
        item["color"] = item["color"].upper()
        item['sku'] = sku_data.extract_first().strip() +"_" +item["color"]

    def _sizes(self, sizes1, item, **kwargs):
        sizes = ''
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        if "COMING SOON" in item["color"]:
            item['originsizes'] = []
        item["designer"] = "QUAY"

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@id="ComparePrice"]/text()').extract()[-1].replace('"','')
            item['originsaleprice'] = prices.xpath('.//span[@id="ProductPrice"]/text()').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//span[@id="ProductPrice"]/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[@id="ProductPrice"]/text()').extract_first()

_parser = Parser()


class Config(MerchantConfig):
    name = 'quay'
    merchant = 'Quay Australia'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="productsTotalCount"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//a[@data-homepage-element="featured-collection"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="AddToCart"]', _parser.checkout)),
            ('name','//h1[@itemprop="name"]/text()'),
            ('color','//select/option[@selected="selected"]/text()'), 
            ('images',('//html',_parser.images)),
            ('sku',('//select/option[@selected="selected"]/@data-sku',_parser.sku)),
            ('description', ('//div[@class="product__description"]//text()',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.quayaustralia.com/collections/quay-man-sunglasses?page=",
                "https://www.quayaustralia.com/collections/mens-blue-light?page=",
            ],
        ),
        f = dict(
            a = [
                "https://www.quayaustralia.com/collections/women-sunglasses?page=",
                "https://www.quayaustralia.com/collections/blue-light?page=",
                "https://www.quayaustralia.com/collections/cases-care?page=",
                "https://www.quayaustralia.com/collections/chains?page="
                ],

        params = dict(
            # TODO:

            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '.com/',
            # cookies = {
            #     'quay_site_loc':'US',
            #     'cart_currency':"USD",
            # },
            ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '.co.uk/',
            # cookies = {
            #     'quay_site_loc':'UK',
            #     'cart_currency':"GBP",
            # }
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',

        ),
        AU = dict(
            area = 'GB',
            currency = 'AUD',
            country_url = '.com.au/',
            # cookies = {
            #     'quay_site_loc':'AU',
            #     'cart_currency':"AUD",
            # },
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '.eu/',
            # cookies = {
            #     'quay_site_loc':'EU',
            #     'cart_currency':"EUR",
            # },
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '.eu/',
            # cookies = {
            #     'quay_site_loc':'EU',
            #     'cart_currency':"EUR",
            # }
        ),
        )

        


