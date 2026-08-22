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
        
        item['sku'] = sku_data.extract_first().strip()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img.split("?")[0]

            if img not in images:
                images.append(img)
            if not cover and "_main" in img.lower():
            	cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('.//div[@class="product all-description"]//div[@class="value"]/text()').extract() + description.xpath('.//div[@id="data-additional"]/div//text()').extract() + description.xpath('.//div[@class="condition-grade"]//text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//span[contains(@id,"product-retail")]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0].strip()
        except:
            try:
                item['originlistprice'] = prices.xpath('.//span[@data-price-type="oldPrice"]/span/text()').extract()[0].strip()
                item['originsaleprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0].strip()

            except:
                item['originsaleprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0].strip()
                item['originlistprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0].strip()

        item["name"] = item["color"] + " " + item["designer"] + " " +item["name"]


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//figure[@itemprop="associatedMedia"]/span/img/@src').extract()
        images = []
        for img in imgs:
            img = img.split("?")[0]
            if img not in images:
                images.append(img)

        return images
        

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="toolbar-number"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('items',''))
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            info1 = info.xpath('.//dt/text()').extract_first().strip() + ': ' +  info.xpath('.//dd/text()').extract_first().strip()
            if info1 and info1.strip() not in fits:
                fits.append(info1.strip())
        size_info = '\n'.join(fits)
        return size_info 

_parser = Parser()



class Config(MerchantConfig):
    name = 'lampoo'
    merchant = 'Lampoo'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="of-text"]/span/text()',
            items = '//article[@class="product-item-info"]',
            designer = './/div[@class="product-item-designer"]/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="product-addtocart-button"]', _parser.checkout)),
            ('images',('//figure[@itemprop="associatedMedia"]/span/img/@src',_parser.images)), 
            ('sku',('//form[@id="product_addtocart_form"]/@data-product-sku',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//span[@class="product-info-name"]/text()'),
            ('designer','//span[@class="product-info-designer"]/text()'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//div[@class="product-info-size"]/span/text()',_parser.sizes)),
            ('prices', ('//div[@class="product-info-price"]', _parser.prices)),
            

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
            size_info_path = '//div[@class="additional-attributes attributes-measurement"]//div[@class="additional-attributes-group"]',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(


        ),
        f = dict(
            a = [
                "https://www.lampoo.com/en/women/accessories.html?p="
            ],
            b = [
                "https://www.lampoo.com/en/women/bags.html?p="
            ],
            c = [
                "https://www.lampoo.com/en/women/clothes.html?p="
            ],
            s = [
                "https://www.lampoo.com/en/women/shoes.html?p="
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
            area = 'EU',
            currency = 'USD',
            discurrency = "EUR",
            currency_sign = '\u20ac',

        ),


        CN = dict(
            currency = 'CNY',
            discurrency = "EUR",
            currency_sign = '\u20ac',
            

        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = "EUR",
            currency_sign = '\u20ac',
        ),    
        )

        


