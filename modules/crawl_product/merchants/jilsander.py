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
        
    def _page_num(self, data, **kwargs):
        page_num = 1

        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _color(self, data, item, **kwargs):
        color = data.extract_first().strip().upper()
        item['color'] = color
        
        item['sku'] = item['sku'] + color
    def _sku(self, sku_data, item, **kwargs):

        item['sku'] = sku_data.extract_first().split('/')[-1].split('.html')[0]

    def _designer(self, designer_data, item, **kwargs):
        item['designer'] = 'JIL SANDER'
          
    def _images(self, images, item, **kwargs):
        item['images'] = []
        imgs = images.extract()
        for img in imgs:
            image = img
            if 'https:' not in image:
                image = image.replace('http:','https:')
            item['images'].append(image)
        
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc or 'shipping' in desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        sizes = sizes_data.extract()
        if len(sizes) > 0:
            for size in sizes:
                item['originsizes'].append(size.strip())
        elif item['category'] in ['a', 'b', 'e']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice= prices.xpath('.//span[@class="sales"]/span/@content').extract()
        listPrice = prices.xpath('.//span[@class="regular"]/span/@content').extract()
        if listPrice:
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = listPrice[0]
        else:
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = salePrice[0]


    def _parse_images(self, response, **kwargs):
        images = []
        imgs = response.xpath('//div[contains(@id,"pdp")]//div[@class="carousel-item"]//img/@src').extract()
        for img in imgs:
            image = img
            images.append(image) 
        return images


    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@class="image-container"]/a/@href').extract())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'jilsander'
    merchant = 'JIL SANDER'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//span[@class="paging-current-page"]/text()',_parser.page_num),
            # list_url = _parser.list_url,
            items = '//div[@class="image-container"]',
            designer = './div/a/@data-brand',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[contains(@class,"add-to-cart")]', _parser.checkout)),
            ('sku', ('//meta[@property="og:url"]/@content',_parser.sku)),
            ('color',('//button[@class="color-attribute color_product"]/span[contains(@class,"selected")]/@data-displayvalue', _parser.color)),
            ('name', '//h1[@class="product-name"]/text()'),    # TODO: path & function
            ('designer', ('//html', _parser.designer)),
            ('images', ('//div[contains(@id,"pdp")]//div[@class="carousel-item"]//img/@src', _parser.images)),
            ('description', ('//div[@id="details-panel"]//ul[@class="ul-listing"]//li/text()',_parser.description)), # TODO:
            ('sizes', ('//a[@class="  do_selectsize"]/@data-attr-value', _parser.sizes)),
            ('prices', ('//div[@class="prices"]', _parser.prices))
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
                'https://www.jilsander.com/en-us/mens/other/accessories?p=',
                "https://www.jilsander.com/en-us/mens/other/jewellery?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/mens/accessories?p="
            ],
            b = [
                'https://www.jilsander.com/en-us/mens/other/bags?p=',
                "https://www.jilsander.com/en-us/mens/other/smallleathergoods?p="
            ],
            c = [
                "https://www.jilsander.com/en-us/mens/rtw?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/mens/coatsandjackets?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/mens/trousers?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/mens/tops?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/mens/shirts?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/mens/knitwearandjersey?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/mens/denim?p=",


            ],
            s = [
                'https://www.jilsander.com/en-us/mens/other/shoes?p=',
                "https://www.jilsander.com/en-us/jilsanderplus/mens/shoes?p="
            ],

        ),
        f = dict(
            a = [
                'https://www.jilsander.com/en-us/women/other/jewellery?p=',
                'https://www.jilsander.com/en-us/jilsanderplus/women/accessories?p='
            ],
            b = [
                'https://www.jilsander.com/en-us/women/other/bags?p=',
                "https://www.jilsander.com/en-us/women/other/smallleathergoods?p="
            ],
            c = [
                "https://www.jilsander.com/en-us/women/rtw?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/coatsandjackets?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/dresses?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/tops?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/shirts?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/knitwearandjersey?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/pyjamas?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/denim?p=",
                "https://www.jilsander.com/en-us/jilsanderplus/women/skirts?p=",

            ],
            s = [
                'https://www.jilsander.com/en-us/women/other/shoes?p=',
                "https://www.jilsander.com/en-us/jilsanderplus/women/shoes?p="
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
            country_url = '/en-us/',
        ),

        # can just borrowse, cant buy in cn
        # CN = dict(
        #     currency = 'CNY',
        #     language = 'ZH',
        #     country_url = '/cn/',
        #     translate = [
        #     ('store.jilsander.com','store.jil-sander.net.cn'),
        #     ('/women/','/%E5%A5%B3%E5%A3%AB/'),
        #     ('/men/','/%E7%94%B7%E5%A3%AB/'),
        #     ('/coats','/%E4%B8%8A%E8%A1%A3'),
        #     ('/bags','/%E5%8C%85%E8%A2%8B'),
        #     ('/skirts','/%E5%8D%8A%E8%A3%99'),
        #     ('/down-jackets','/%E7%BE%BD%E7%BB%92%E6%9C%8D'),
        #     ('/jackets','/%E5%A4%B9%E5%85%8B'),
        #     ('/jewelry','/%E7%8F%A0%E5%AE%9D'),
        #     ('/shirts','/%E8%A1%AC%E8%A1%AB'),
        #     ('/pants','/%E8%A3%A4%E8%A3%85'),
        #     ('/dresses','/%E8%BF%9E%E8%A1%A3%E8%A3%99'),
        #     ('/accessories','/%E9%85%8D%E9%A5%B0'),
        #     ('/knitwear','/%E9%92%88%E7%BB%87%E8%A1%AB'),
        #     ('/shoes','/%E9%9E%8B%E5%B1%A5')
        #     ]
        # ),

        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            country_url = '/en-kr/',
        ),

        HK = dict(
            currency = 'HKD',
            # discurrency = 'USD',
            country_url = '/en-hk/',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/en-gb/',
        ),

        CA = dict(
            currency = 'CAD',
            country_url = '/en-ca/',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency ='USD',
            country_url = '/en-au/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/en-de/',
            area = 'EU',

        ),
        )

        

