from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        json_Data = checkout.extract_first().split('__PRELOADED_STATE__')[-1].strip().replace('= ','')
        obj = json.loads(json_Data)
        obj = obj["products"]["details"]['products']['result']
        for p in obj:
            obj = obj[p]
        
        if obj:
            item['tmp'] = obj
            return False
        else:
            return True

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + "?page="+str((i))
        return url
    def _page_num(self, data, **kwargs):
        page = 20
        return page

    def _sku(self, sku_data, item, **kwargs):
        sku = item['tmp']['id']
        item['sku'] = sku
        item['designer'] = item['tmp']["brand"]["name"].upper()
        item['name'] = item['tmp']['name']

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['resources']
        images = []
        cover = imgs["primary"]["sources"]["800"]
        print(cover)
        for key, value in imgs.items():
            try:
                img = imgs[key]["sources"]["800"]
            except:
                continue
            if img not in images:
                images.append(img)
            	

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

    def _sizes(self, sizes, item, **kwargs):
        merchantId = item['tmp']["merchant"]["id"]
        sizes = item['tmp']["sizes"]
        item['originsizes'] = []
        for size in sizes:
            size1 = size["scaleAbbreviation"]+size["name"]
            stock = size["stock"]
            for s in stock:
                if s["merchantId"] == merchantId and s["quantity"] > 0:
                    item['originsizes'].append(size1)

        
    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = str(item['tmp']["price"]["includingTaxesWithoutDiscount"])
            item['originsaleprice'] = str(item['tmp']["price"]["includingTaxes"])
        except:

            item['originsaleprice'] = ''
            item['originlistprice'] = ''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//a[@class="productView-thumbnail-link"]/@href').extract()

        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images


_parser = Parser()



class Config(MerchantConfig):
    name = 'altuzarra'
    merchant = 'Altuzarra'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@data-test="productItem"]',
            designer = './@data-product-brand',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ("//script[contains(text(),'__PRELOADED_STATE__')]/text()", _parser.checkout)),
            ('images',('//a[@class="productView-thumbnail-link"]/@href',_parser.images)), 
            ('sku',('//div[@class="storeAvailabilityModal-form-product-sku"]/text()',_parser.sku)),
            ('color','//div[@data-test="product-colorContainer"]/text()'),
            ('description', ('//div[@data-test="product-description"]//text()',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
            ('prices', ('//html', _parser.prices)),
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
        )

    list_urls = dict(
        f = dict(
            c = [
                "https://www.altuzarra.com/en-us/sets/ready-to-wear?p=",
            ],
            b = [
                "https://www.altuzarra.com/en-us/sets/bags?p="
            ]
        ),
        m = dict(
            a = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'EU',
            currency = 'USD',
            country_url = '/en-us/',
        ),
        CN = dict(
            area = 'AS',
            currency = 'CNY',
            country_url = '/en-cn/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/en-ca/',
        ),
        HK = dict(
            area = 'AS',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '/en-hk/',
        ),
        AU = dict(
            area = 'AS',
            currency = 'AUD',
            currency_sign = '$',
            country_url = '/en-au/',
        ),
        JP = dict(
            area = 'AS',
            currency = 'JPY',
            country_url = '/en-jp/',
        ),
        KR = dict(
            area = 'AS',
            currency = 'KRW',
            country_url = '/en-kr/',
        ),
        SG = dict(
            area = 'AS',
            currency = 'SGD',
            countryurl = '/en-sg/',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-gb/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en-de/',
            thousand_sign = '.'
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            country_url = '/en-ru/',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'USD',
            currency_sign = '\u20ac',
            country_url = '/en-no/',
            thousand_sign = '.'
        )
   
        )

        


