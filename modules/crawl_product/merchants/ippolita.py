from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests

class Parser(MerchantParser):

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        item['sku'] = sku_data.split('#')[-1].strip().upper()

    def _images(self, images, item, **kwargs):
        images = images.extract()
        imgs = []
        cover = None
        for image in images:
            imgs.append(image)
            if '_1' in image or '-1' in image:
                cover = image
        item['images'] = imgs
        if cover:
            item['cover'] = cover 
        else:
            item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        item['designer'] = 'IPPOLITA'
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = ' '.join(desc_li)

        item['description'] = description.strip()

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="price"]//text()').extract_first()
        listPrice = prices.xpath('.//span[@class="price"]//text()').extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else salePrice
        item['originsaleprice'] = item['originsaleprice'].strip()
        item['originlistprice'] = item['originlistprice'].strip()

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('width' in info.strip().lower() or 'length' in info.strip().lower() or 'weight' in info.strip().lower() or 'diameter' in info.strip().lower()):
                fits.append(info.replace('\u2022','').strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = 'ippolita'
    merchant = 'IPPOLITA'

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//div[@id="primary"]//span[@class="showing"]/text()[2]',_parser.page_num),
            # list_url = _parser.list_url,
            # parse_item_url = _parser.parse_item_url,
            items = '//div[@class="product-list-item"]',
            designer = '//p[@class="brand"]/text()',
            link = './/@data-href',
            ),
        product = OrderedDict([
            ('color','//span[@class="swatch-attribute-selected-option"]/text()'),
            ('sku', ('//p[@class="product-style-no"]/text()',_parser.sku)),
            ('name', '//h1[@class="product-title"]/text()'),
            ('images', ('//div[@class="product-main-image-items"]//img/@src', _parser.images)),
            ('description', ('//div[@class="product description cms-content"]//text()',_parser.description)), # TODO:
            ('sizes', ('//div[@class="swatch-attribute-options"]//div/text()', _parser.sizes)),
            ('prices', ('//div[@class="product-info-price"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="product-main-image-items"]//img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product description cms-content"]/div/text()',
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
                'https://www.ippolita.com/collections?product_list_limit=all&all=',
                'https://www.ippolita.com/jewelry?product_list_limit=all&all=',

            ],
            b = [
            ],
            c = [
            ],
            e = [
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
            area = 'US',
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',

        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',

        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',

        ),
        RU = dict(
            discurrency = 'USD',
            currency = 'RUB',

        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',

        ),
        AU = dict(
            
            currency = 'AUD',
            discurrency = 'USD',

        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',

        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),

        )

