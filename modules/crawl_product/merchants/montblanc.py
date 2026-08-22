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

    def _page_num(self, pages, **kwargs): 
        page_num = 1
        return page_num

    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = item["url"].split('_cod')[-1].split(".html")[0].strip()



    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img

            if img not in images:
                images.append(img)
            if not cover and "_main" in img.lower():
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
        item["designer"] = "MONTBLANC"

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):
        try:
            item['originsaleprice'] = prices.xpath('.//div[@class="itemPrice"]//span[@class="value"]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//div[@class="itemPrice"]//span[@class="value"]/text()').extract()[0].strip()
        except:
            try:
                pricesjson=prices.xpath(".//@data-fp").extract()[0]
                pobj = json.loads(pricesjson)
                item['originsaleprice'] = str(pobj[kwargs["country"]])
                item['originlistprice'] = str(pobj[kwargs["country"]])
            except:
                item['originsaleprice'] = ""
                item['originlistprice'] = ""

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="alternativeProductShots"]//li//img/@src').extract()
        images = []
        for img in imgs:
            img = img
            if img not in images:
                images.append(img)

        return images
        
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="totalResultsCount"]/text()').extract_first().strip())
        return number




_parser = Parser()



class Config(MerchantConfig):
    name = 'montblanc'
    merchant = 'Montblanc'
    # url_split = False
    headers = {
    'X-Akamai-Bot-Allow':'ada42e9a8d5c0fe577cda6bc8ba2ad0a'
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="products"]/@data-ytos-opt',_parser.page_num),
            items = '//a[@class="item_l"]',
            designer = './/div[@class="brand-name"]',
            link = './@href',
            ),
        product = OrderedDict([
            # ('checkout', ('//*[@class="mb-pdp-addtobag"]|//input[@name="shoppingbagvalue"]', _parser.checkout)),
            ('images',('//div[@class="alternativeProductShots"]//li//img/@src',_parser.images)), 
            ('sku',('//input[@name="productCookieId"]/@value',_parser.sku)),
            ('color','//p[@class="brand_colour"]/text()[2]'),
            ('name', '//h1/span/text()'),
            ('description', ('//div[@id="desc-panel-content"]//span/text()',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
            ('prices', ('//div[contains(@class,"mb-product__info")]', _parser.prices)),
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
                "https://www.montblanc.com/en-us/collection/men-s-accessories.html?p=",
                "https://www.montblanc.com/en-us/collection/eyewear.html?p=",
                "https://www.montblanc.com/en-us/collection/watches/montblanc-1858-collection.html?p=",
                "https://www.montblanc.com/en-us/collection/watches/montblanc-heritage.html?p=",
                "https://www.montblanc.com/en-us/collection/watches/montblanc-star-legacy.html?p=",
                "https://www.montblanc.com/en-us/collection/watches/montblanc-summit-collection.html?p=",
                "https://www.montblanc.com/en-us/collection/watches/montblanc-boheme-collection.html?p=",
                "https://www.montblanc.com/en-us/collection/writing-instruments.html?p="
            ],
            e = [
                "https://www.montblanc.com/en-us/collection/fragrance.html?p="
                ],
            b = [
                "https://www.montblanc.com/en-us/collection/leather.html?p=",
                "https://www.montblanc.com/en-us/collection/leather.html?filter=-439620744,-1604315233,2117149471,-2110820078,58052473,-1640751246,-470450878,1234281492,-78258777"
                ],

        ),
        f = dict(
            a = [
                'https://www.montblanc.com/en-us/collection/jewellery.html?p='
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
            country_url = ".com/en-us/",
        ),



        
        CN = dict(
            area = 'AS',
            currency = 'CNY',
            language = "ZH",
            currency_sign = '\uffe5',
            country_url = ".cn/zh-cn/"

        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            language = "JA",
            currency_sign = '\uffe5',
            country_url = ".com/ja-jp/"


        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            language = "KO",
            currency_sign = '\uffe6',
            country_url = ".com/ko-kr/"
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            currency_sign = 'S$',
            country_url = ".com/en-shop/"

        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            language = "ZH",
            currency_sign = 'HK$',
            country_url = ".com/tcn-shop/"

        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = ".com/en-gb/"

        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            language = "RU",
            country_url = ".com/ru-shop/"
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = '$',

            country_url = ".com/en-ca/"

        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            currency_sign = "AU$",
            country_url = ".com/en-shop/"
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            language = "DE",
            currency_sign = '\u20ac',
            country_url = ".com/de-de/",
            thousand_sign = "."

        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            currency_sign = 'kr',
            country_url = ".com/en-shop/"
        ),
# #      
        )

        


