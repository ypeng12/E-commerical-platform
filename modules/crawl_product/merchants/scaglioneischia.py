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
        page_num = data.lower().split("of")[-1].strip().split("total")[0]
        page = int(page_num) / 48 +  1 
        return page

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*72
        url = response_url.split('?')[0] + '?s=%s'%(i)
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https://" + img
            if img not in images:
                images.append(img)
            if not cover and "_LK.jpg" in img.lower():
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
        obj = json.loads(sku_data.extract()[-1].strip())

        # item["color"] = item["color"].upper()
        
        item["color"] = obj["color"].upper()
        item['sku'] = obj["sku"] +"_"+item["color"]
        item['name'] = obj["name"]
        item["designer"] = item["designer"].upper()
        item['tmp'] = obj
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        item['originlistprice'] = item['tmp']["offers"]["highPrice"]
        item['originsaleprice'] = item['tmp']["offers"]["lowPrice"]
        # try:
        #     item['originlistprice'] = prices.xpath('.//p[@class="price"]//del/span[@class="amount"]/text()').extract()[-1].replace('"','')
        #     item['originsaleprice'] = prices.xpath('.//p[@class="price"]/span[@class="amount"]/text()').extract()[0]
        # except:

        #     item['originsaleprice'] =prices.xpath('.//p[@class="price"]/span[@class="amount"]/text()').extract_first()
        #     item['originlistprice'] =prices.xpath('.//p[@class="price"]/span[@class="amount"]/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="single-images"]/div//img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https://" + img
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="result-count"]/text()').extract_first().lower().split("of")[-1].strip().split("total")[0])
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'scaglioneischia'
    merchant = 'Scaglioneischia'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="result-count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[@class="products row"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './li/div/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="inserisci_carrello"]', _parser.checkout)),
            ('name','//h1[@class="product-name"]/text()'),
            ('designer','//meta[@property="product:brand"]/@content'),
            ('images',('//div[@class="single-images"]/div//img/@src',_parser.images)),
            
            ('sku',('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('description', ('//meta[@itemprop="description"]/@content',_parser.description)),
            ('sizes',('//a[@class="size_item"]/text()',_parser.sizes)),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.scaglioneischia.com/en/man/categories/accessories/groups?s="

            ],

            c = [
                "https://www.scaglioneischia.com/en/man/categories/clothing/groups?s=",

            ],
            s = [
                "https://www.scaglioneischia.com/en/man/categories/shoes/groups?s=",
                # "https://www.belstaff.com/en_US/footwear/?&start=0&sz=72&format=page-element&page="
            ],

        ),
        f = dict(
            a = [
                "https://www.scaglioneischia.com/en/woman/categories/accessories/groups?s=",
                ],

            c = [
                "https://www.scaglioneischia.com/en/woman/categories/clothing/groups?s="
            ],
            s = [
                "https://www.scaglioneischia.com/en/woman/categories/shoes/groups?s="
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
            country_url = '.com/en_US/',
            ),

        # CAnt find how they are changing currency
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # JP = dict(
        #     area = 'GB',
        #     currency = 'JPY',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # KR = dict(
        #     area = 'GB',
        #     currency = 'KRW',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # SG = dict(
        #     area = 'GB',
        #     currency = 'SGD',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',

        # ),
        # HK = dict(
        #     area = 'GB',
        #     currency = 'HKD',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        # GB = dict(
        #     area = 'GB',
        #     currency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),

        # CA = dict(
        #     currency = 'CAD',
        #     discurrency = 'USD',

        # ),
        # # AU = dict(
        # #     area = 'GB',
        # #     currency = 'AUD',
        # #     discurrency = 'GBP',
        # #     currency_sign = u'\xa3',
        # #     country_url = '.co.uk/',
        # # ),
        # DE = dict(
        #     area = 'GB',
        #     currency = 'EUR',
        #     currency_sign = u'\u20ac',
        #     country_url = '.eu/en/',
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     discurrency = 'EUR',
        #     currency_sign = u'\u20ac',
        #     country_url = '.eu/en/',
        # ),
        )

        


