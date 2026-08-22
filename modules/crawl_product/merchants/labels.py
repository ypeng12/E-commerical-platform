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
        pages = int(20)
        return pages

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "http:" + img
            if img not in images and "shop.labelsfashion.com" in img:
                images.append(img)
            if not cover and "_1" in img.lower():
            	cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description1, item, **kwargs):
        
        description = description1.xpath('//div[@id="product.info.descript"]//text()').extract()   
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        script = description1.xpath("//script/text()")
        json_data = ''
        for script in script.extract():
             if "color: '" in script:
                json_data = script
                break
        item["color"] = json_data.split("color: '")[-1].split("'")[0].upper()
        item["designer"] = item["designer"].upper()
    def _sizes(self, sizes_data, item, **kwargs):
        for script in sizes_data.extract():
             if 'product_addtocart_form' in script:
                json_data = script
                break

        try:       
            json_str = json_data.strip()
            json_dict = json.loads(json_str)
            item['tmp'] = json_dict['#product_addtocart_form']['configurable']['spConfig']
            values = json_dict['#product_addtocart_form']['configurable']['spConfig']['attributes']['137']['options']
            originsizes = []
            for value in values:
                size = value['label']
                if 'sold' in size.lower() or 'select' in size.lower():
                    continue
                originsizes.append(size.split("-")[0])
        except:
            originsizes = ''
        size_li = []
        if item['category'] in ['a','b']:
            if not originsizes:
                size_li.append('IT')
            else:
                size_li = originsizes
        elif item['category'] == 'c':
            for size in originsizes:
                size_li.append(size.replace('GLOBAL', '').strip())
        elif item['category'] == 's':
            size_li = originsizes
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//*[contains(@id,"old-price-")]//span[@class="price"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//div[@class="product product-tax-price"]/span/text()').extract()[0].split("excl")[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//div[@class="product product-tax-price"]/span/text()').extract()[0].split("excl")[0].strip()
            item['originlistprice'] = prices.xpath('.//div[@class="product product-tax-price"]/span/text()').extract()[0].split("excl")[0].strip()
        if item["country"] in ["GB","DE","NO"]:
            try:
                item['originlistprice'] = prices.xpath('.//*[contains(@id,"old-price-")]//span[@class="price"]/text()').extract()[0].strip()
                item['originsaleprice'] = prices.xpath('.//*[contains(@id,"product-price-")]]/text()').extract()[0].split("excl")[0].strip()
            except:
                item['originsaleprice'] = prices.xpath('.//*[contains(@id,"product-price-")]/text()').extract()[0].split("excl")[0].strip()
                item['originlistprice'] = prices.xpath('.//*[contains(@id,"product-price-")]/text()').extract()[0].split("excl")[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@id,"gallery-slider")]//img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "http:" + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()

class Config(MerchantConfig):
    name = 'labels'
    merchant = 'Labels Fashion'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="lc_bld plp_counter"]/text()', _parser.page_num),
            items = '//div[@class="product details product-item-details"]',
            designer = './div[@class="product designer product-item-designer"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="buynow"]', _parser.checkout)),
            ('designer','//p[@class="product designer product-item-designer"]/text()'),
            ('description', ('//html',_parser.description)),
            ('images',('//div[contains(@id,"gallery-slider")]//img/@src',_parser.images)), 
            ('sku',('//div[@class="price-box price-final_price"]/@data-product-id',_parser.sku)),
            ('name', '//div[@class="product product-name"]/text()'),
            ('sizes',('//script[@type="text/x-magento-init"]/text()',_parser.sizes)),
            ('prices', ('//div[@class="column main"]', _parser.prices)),
            

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
            a = [
                "https://shop.labelsfashion.com/women/accessories?p="
            ],
            b = [
                "https://shop.labelsfashion.com/women/bags?p="
            ],
            c = [
                "https://shop.labelsfashion.com/women/clothing?p=",
            ],
            s = [
                "https://shop.labelsfashion.com/women/shoes?p="
            ],

        ),
        m = dict(

            a= ["https://shop.labelsfashion.com/men/accessories?p="],

            b = [
                "https://shop.labelsfashion.com/men/bags?p="
            ],

            c = [
                "https://shop.labelsfashion.com/men/clothing?p=",
            ],
            s = [
                "https://shop.labelsfashion.com/men/shoes?p="
            ],





        params = dict(
            # TODO:

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

# country rate info ??????
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

        


