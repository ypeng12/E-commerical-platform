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

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract()[-1].strip()
        item['sku'] = sku.split('#')[-1][:-3].strip().upper()
        item['designer'] = 'MCM'

    def _images(self, images, item, **kwargs):
        item['images'] = images.extract()
        item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.extract()
        item['originsizes'] = []
        for s in sizes:
            if s.upper().strip() != 'SIZE':
                item['originsizes'].append(s.strip())
        if not item['originsizes'] and item['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        item['originlistprice'] = prices.xpath('.//span/text()').extract()[0]
        item['originsaleprice'] = prices.xpath('.//span/text()').extract()[0]

    def _parse_item_url(self, response, **kwargs):

        url1 = response.url.replace('?sz=1','') + '?sz=40&start=insertH&format=page-element&source=showmore'
        for page in range(0,100):
            url2 = url1.replace('insertH',str(page*40))
            page = page+1
            result = getwebcontent(url2)
            html = etree.HTML(result)

            for href in html.xpath('//div[@class="grid-cell"]/a/@href'):
                if href is None:
                    continue
                url =  urljoin(response.url, href)
                yield url,'MCM'


            if not html.xpath('//a[@class="load-more"]/text()'):
                break

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and 'inches' in info.strip().lower():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//nav[@class="breadcrumb"]/text()[last()-1]').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('items',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'mcm'
    merchant = "MCM"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            # items = '//div[@class="ml-thumb-image"]',
            # designer = './/h4[@itemprop="brand"]/text()',
            # link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add-to-cart"]', _parser.checkout)),
            ('sku', ('//p[@class="sku-id"]/text()',_parser.sku)),
            ('name', '//h1[@class="product-name bold"]/text()'),
            ('images', ('//div[@id="pdpMain"]//div[@class="row-col-8 full-width-col js-main-image-container"]//div[@class="product-image"]/img/@src', _parser.images)),
            ('color','//div[@class="label va-color"]/text()'),
            ('description', ('//div[@id="panel1"]/div//text()',_parser.description)), # TODO:
            ('sizes', ('//ul[@id="size-list"]//li/a/span/text()', _parser.sizes)),
            ('prices', ('//div[@class="product-price"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@id="pdpMain"]//div[@class="row-col-8 full-width-col js-main-image-container"]//div[@class="product-image"]/img/@src'
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="full-width-col"]/ul/li/text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://us.mcmworldwide.com/en_US/men/accessories/all-accessories?sz=',
                'https://us.mcmworldwide.com/en_US/men/belts?sz='
            ],
            b = [
                'https://us.mcmworldwide.com/en_US/men/bags/all-bags?sz=',
                'https://us.mcmworldwide.com/en_US/men/backpacks?sz=',
                'https://us.mcmworldwide.com/en_US/men/wallets/all-wallets?sz=',
            ],
            c = [
                'https://us.mcmworldwide.com/en_US/men/clothing/all-clothing?sz=',
            ],
            s = [
                'https://us.mcmworldwide.com/en_US/men/shoes/all-shoes?sz=',
            ],

        ),
        f = dict(
            a = [
                'https://us.mcmworldwide.com/en_US/women/accessories/all-accessories?sz=',
            ],
            b = [
                'https://us.mcmworldwide.com/en_US/women/bags/all-bags?sz=',
                'https://us.mcmworldwide.com/en_US/women/backpacks?sz=',
                'https://us.mcmworldwide.com/en_US/women/wallets/all-wallets?sz=',
            ],
            c = [
                'https://us.mcmworldwide.com/en_US/women/clothing/all-clothing?sz=',
            ],
            s = [
                'https://us.mcmworldwide.com/en_US/women/shoes/all-shoes?sz=',
            ],
            e = [
                "https://us.mcmworldwide.com/en_US/women/fragrance?sz=",
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = 'us.mcmworldwide.com/en_US/',
        ),
        CN = dict(
            area = 'CN',
            currency = 'CNY',
            country_url = 'cn.mcmworldwide.com/en_CN/',
            currency_sign = '\xa5',
        ),
        # JP = dict(
        #     currency = 'JPY',
        #     country_url = 'jp.mcmworldwide.com/en_JP/',
        #     currency_sign = u'\xa5',
        # ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            country_url = 'uk.mcmworldwide.com/en_GB/',
            currency_sign = '\xa3',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            country_url = 'de.mcmworldwide.com/en_DE/',
            currency_sign = '\u20ac',
        ),
        )

        


