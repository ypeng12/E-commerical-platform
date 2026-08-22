from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = 20
        return pages

    def _checkout(self, checkout, item, **kwargs):
        json_data = json.loads(checkout.extract_first())
        item['tmp'] = json_data
        if "InStock" in json_data['offers']['availability']:
            return False
        else:
            return True
    
    def _list_url(self, i, response_url, **kwargs):
        rpage = '.%s.'%str(i)
        url = response_url.replace('.1.',rpage)
        return url

    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = item['tmp']['mpn']
        item['name'] = item['tmp']['name'].upper()
        item['designer'] = "MIU MIU"

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

    def _images(self, response, item, **kwargs):
        imgs = response.extract()
        images = []
        for img in imgs:
            image = img.split(', ')[0].strip()
            if 'cq5dam.web.hf8f8f8.1000.1000' in img and 'cq5dam.web.hf8f8f8.600.600' not in img:
                images.append(image)
        item['images'] = images
        item['cover'] = images[0]

    def _sizes(self, response, item, **kwargs):
        size_li = []
        for size in response.extract():
            if size:
                size_li.append(size.replace(',','.'))

        item["originsizes"] = size_li

    def _prices(self, response, item, **kwargs):
        saleprice = response.extract_first()
        listprice = response.extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        imgs = response.extract()
        images = []
        for img in imgs:
            image = img.split(', ')[0].strip()
            if 'cq5dam.web.hf8f8f8.1000.1000' in img and 'cq5dam.web.hf8f8f8.600.600' not in img:
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
    name = 'miumiu'
    merchant = 'MIU MIU'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="products-view visible-xs row"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//article[@class="plp__item"]',
            designer = '//article[@class="plp__item"]/div[@class="hidden tealium-info"]/@analytics-data',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[@id="jsonldProduct"]/text()', _parser.checkout)),
            ('sku', ('//div[@class="c-cod"]/text()',_parser.sku)),
            ('color','//div[@class="color-picker"]/div[@class="color-picker__info"]/span[@class="color-picker__value"]/text()'),
            ('description', ('//div[@class="info-prodet__info"]/div[@class="info-prodet__info__wrapper"]/div//ul/li/text()',_parser.description)),
            ('images', ('//div[@class="gallery-slider__container"]/div[@class="gallery-slider__item"]/picture/source/@data-srcset', _parser.images)),
            ('sizes', ('//div[contains(@class,"product-detail__size-picker")]/div[@class="size-picker"]/ul/li/a/span/text()', _parser.sizes)),
            ('prices', ('//div[@class="product-detail__price-block"]/span/text()', _parser.prices))
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
            size_info_path = '//div[@class="info-prodet__info"]/div[@class="info-prodet__info__wrapper"]/div//ul/li/text()',
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.miumiu.com/us/en/accessories.1.html',
                'https://www.miumiu.com/us/en/jewels.1.html'
            ],
            b = [
                'https://www.miumiu.com/us/en/bags.1.html'
            ],
            c = [
                'https://www.miumiu.com/us/en/ready_to_wear.1.html'
            ],
            s = [
                'https://www.miumiu.com/us/en/shoes.1.html'
            ],

        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/us/',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/gb/',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/de/',
        ),
        # CN = dict(
        #     language = 'ZH',
        #     currency = 'CNY',
        #     country_url = '.cn',
        #     currency_sign = u'\xa5',
        #     translate = [
        #     ('catalogId=11152&langId=-1','catalogId=11654&langId=-7'),
        #     ('storeId=11251','storeId=30251'),
        #     ('categoryId=3074457345616679169','categoryId=3074457345616716684'),
        #     ('categoryId=3074457345616679170','categoryId=3074457345616715847'),
        #     ('categoryId=3074457345616679171','categoryId=3074457345616716700'),
        #     ('categoryId=3074457345616679172','categoryId=3074457345616715844'),
        #     ('categoryId=3074457345616679173','categoryId=3074457345616715854'),
        #     ('categoryId=3074457345616679174','categoryId=3074457345616715846'),
        #     ('categoryId=3074457345616689168','categoryId=3074457345616716677')
        #     ]
        # ),
        )

        


