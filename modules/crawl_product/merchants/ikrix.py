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

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].upper().strip()

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images and "large" in img:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.xpath(".//p[@class='descrizione narrowFont']//text()").extract() + description.xpath('//div[@id="info-product"]//text()').extract() + description.xpath('//div[@id="ui-accordion-info-product-accordion-panel-1"]//text()').extract()
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
        size_li = []
        size_li2 = []
        for size in sizes:
            size_li.append(size)
            size_li2.append(size.split('|')[-1].strip().replace('(','').replace(')',''))
        item['originsizes'] = size_li
        item['originsizes2'] = size_li2
        if item['category'] in ['a','b'] and size_li==[]:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[contains(@class,"discount")]/text()').extract()
        listprice = prices.xpath('.//span[contains(@class,"original")]/text()').extract()
        if len(listprice) == 0:
            salePrice = prices.xpath('.//span[contains(@class,"discount")]/text()').extract()
            item['originsaleprice'] = salePrice[0].strip()
            item['originlistprice'] = salePrice[0].strip()
        else:
            item['originsaleprice'] = salePrice[0].strip()
            item['originlistprice'] = listprice[0].strip()

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//img[@class="lazyload"]/@data-src').extract()
        images = []
        for img in img_li:
            if img not in images and "large" in img:
                images.append(img)
        return images

    def _page_num(self, data, **kwargs):
        page_num = 200
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '/page/' + str(i)
        return url

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 

        
_parser = Parser()



class Config(MerchantConfig):
    name = 'ikrix'
    merchant = "iKRIX"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ik-grid-responsive-row"]/div',
            designer = './/div[@class="product-brand"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[contains(@id,"ik-add-to-cart-button")]', _parser.checkout)),
            ('name', '//div[@class="title fw6"]/text()'),
            ('color','//div[@class=" mt-3"]/span/text()'),
            ('designer', '//div[@class="brand fw6"]/a/text()'),
            ('images', ('//img[@class="lazyload"]/@data-src', _parser.images)),
            ('sku', ('//input[@name="node_id"]/@value', _parser.sku)),
            ('description', ('//html',_parser.description)), # TODO:
            ('sizes', ('//div[@class="ikx-add-to-cart-block"]//label[not(contains(@class,"sold-out"))]/input/@data-size', _parser.sizes)),
            ('prices', ('//div[@class="price"]', _parser.prices))
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
            size_info_path = '//div[@id="info-product-accordion"]//text()',

            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.ikrix.com/us/men/accessories",
            ],
            b = [
                'https://www.ikrix.com/us/men/bags',
            ],
            c = [
                "https://www.ikrix.com/us/men/clothing",
            ],
            s = [
                'https://www.ikrix.com/us/men/shoes'
            ],
        ),
        f = dict(
            a = [
                "https://www.ikrix.com/us/women/accessories",
            ],
            b = [
                'https://www.ikrix.com/us/women/bags'
            ],
            c = [
                'https://www.ikrix.com/us/women/clothing',
            ],
            s = [
                "https://www.ikrix.com/us/women/shoes",
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
            country_url = "/us/",
            currency_sign = '$'
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            country_url = "/cn/",
            currency_sign = '$'
        ),
        JP = dict(
            language = 'JA',
            currency = 'JPY',
            country_url = "/jp/",
            currency_sign = '\xa5',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            country_url = "/kr/",
            currency_sign = '$'
        ),
        SG = dict(
            currency = 'SGD',
            country_url = "/sg/",
            currency_sign = 'S$',
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = "HK$",
            country_url = "/hk/",
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = "\u00A3",
            country_url = "/gb/",
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = "CA$",
            country_url = "/ca/",
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            country_url = "/au/",
            currency_sign = '$'
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = "/de/",
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = "/no/",
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = "/ru/",
        ),


        )
        
