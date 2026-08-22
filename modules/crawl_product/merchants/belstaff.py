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
        page_num = int(data.replace('(','').replace(')','').replace(',',''))/72
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*72
        url = response_url.split('?')[0] + '?start=%s&sz=72&page=%s'%(num,i)
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https://www.belstaff.com" + img
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
        item["color"] = item["color"].upper()
        item['sku'] = sku_data.extract_first().strip() +"_" +item["color"]

        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        
        item["designer"] = "BELSTAFF"
    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//div[@class="product-price"]//span[contains(@class,"product-standard-price")]/text()').extract()[-1].replace('"','')
            item['originsaleprice'] = prices.xpath('.//span[@class="js-sl-price"]/text()').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//span[@class="js-sl-price"]/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[@class="js-sl-price"]/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"primary-image-item pdp-gallery-item")]/a/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https://www.belstaff.com/" + img
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="products-count-number"]/text()').extract_first().strip().replace('(','').replace(')','').replace(',',''))
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'belstaff'
    merchant = 'Belstaff'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="products-count-number"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//a[@class="js-producttile_link"]',
            designer = './/div[@class="item-title"]/a/text()',
            link = './@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="add-to-cart"]', _parser.checkout)),
            ('name','//h1[@class="product-name"]/text()'),
            ('images',('//div[contains(@class,"primary-image-item pdp-gallery-item")]/a/@href',_parser.images)),
            ('color','//span[@class="color-name"]/text()'), 
            ('sku',('//meta[@property="product:retailer_item_id"]/@content',_parser.sku)),
            ('description', ('//div[@class="js-full-content is-desktop"]//text()',_parser.description)),
            ('sizes',('//li[@class="attribute attribute-size "]//li[@title="In Stock"]//span[@class="js-swatch-value"]/text()',_parser.sizes)),
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
                "https://www.belstaff.com/en_US/men/accessories/?page="

            ],
            b = [
                "https://www.belstaff.com/en_US/bags/?page="
            ],
            c = [
                "https://www.belstaff.com/en_US/men/outerwear/?page=",
                "https://www.belstaff.com/en_US/men/clothing/?page=",

            ],
            s = [
                "https://www.belstaff.com/en_US/men/footwear/?page=",
                "https://www.belstaff.com/en_US/footwear/?&start=0&sz=72&format=page-element&page="
            ],

        ),
        f = dict(
            a = [
                "https://www.belstaff.com/en_US/women/accessories/?page=",
                ],

            c = [
                "https://www.belstaff.com/en_US/women/outerwear/?page=",
                "https://www.belstaff.com/en_US/women/clothing/?page="
            ],
            s = [
                "https://www.belstaff.com/en_US/women/footwear/?page="
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

        # UK based one seems to have some priblems, page jsut redirects and stays there
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

        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',

        ),
        # AU = dict(
        #     area = 'GB',
        #     currency = 'AUD',
        #     discurrency = 'GBP',
        #     currency_sign = u'\xa3',
        #     country_url = '.co.uk/',
        # ),
        DE = dict(
            area = 'GB',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '.eu/en/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '.eu/en/',
        ),
        )

        


