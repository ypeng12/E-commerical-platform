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
        num_data = data.strip()
        count = int(num_data)
        page_num = count / 30 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*30
        url = response_url.split('?')[0] + '?start=%s&sz=30&format=page-element'%num
        return url

    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = sku_data.extract_first().strip() + '_' +item['color'].upper()
        item['designer'] = 'CLUB MONACO'

    def _images(self, images, item, **kwargs):
        item['images'] = images.extract()
        item['cover'] = item['images'][0] if item['images'] else ''

    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//span[@class="price-standard"]/text()').extract()[0]
            saleprice = prices.xpath('.//span[@class="price-sales"]/text()').extract()[0]
        except:
            listprice = prices.xpath('.//span[@class="lowblack"]/text()').extract_first()
            saleprice = prices.xpath('.//span[@class="lowblack"]/text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//picture[contains(@id,"s7Image")]//img/@data-yo-src').extract()
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="productsTotalCount"]/text()').extract_first())
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'clubmonaco'
    merchant = 'Club Monaco'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="productsTotalCount"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[@class="swatch-list "]/li/a|//a[@class="thumb-link"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="add-to-cart"]', _parser.checkout)),
            ('color','//span[@class="selected-value select-attribute"]/text()'),
            ('sku',('//span[@itemprop="productID"]/text()',_parser.sku)),
            ('name','//h1[@class="product-name"]/text()'),
            ('images',('//picture[contains(@id,"s7Image")]//img/@data-yo-src',_parser.images)),
            ('description', ('//div[@id="pdp-description-accordion-panel"]//text()|//div[@id="pdp-details-accordion-panel"]//text()',_parser.description)),
            ('sizes',('//ul[@class="no-swiper primarysize  size-swatches"]/li[@class="variations-attribute selectable"]/a/@data-color',_parser.sizes)),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
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
        m = dict(
            a = [
                "https://www.clubmonaco.com/en/men-accessories-belts?p=",
                "https://www.clubmonaco.com/en/men-accessories-grooming?p=",
                "https://www.clubmonaco.com/en/men-accessories-jewelry?p=",
                "https://www.clubmonaco.com/en/men-accessories-grooming?p=",
                "https://www.clubmonaco.com/en/men-accessories-socks?p="
            ],
            b = [
                "https://www.clubmonaco.com/en/men-accessories-bags?p="
            ],
            c = [
                "https://www.clubmonaco.com/en/men-clothing?p="
            ],
            s = [
                "https://www.clubmonaco.com/en/men-shoes?p="
            ],
        ),
        f = dict(
            a = [
                "https://www.clubmonaco.com/en/women-accessories-hats-and-hair-accessories?p=",
                "https://www.clubmonaco.com/en/women-accessories-jewelry?p=",
                ],
            b = [
            	"https://www.clubmonaco.com/en/women-accessories-handbags?p="
            ],
            c = [
                "https://www.clubmonaco.com/en/women-clothing?p="
            ],
            s = [
                "https://www.clubmonaco.com/en/women-shoes?p="
            ]
        )
    )


    countries = dict(
         US = dict(
            language = 'EN',
            currency = 'USD'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = "USD"
        )
    )

        


