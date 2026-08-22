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
        if checkout.extract_first() and checkout.extract_first().strip().upper() == 'ADD TO CART':
            return False
        else:
            return True

    def _sku(self, sku_data, item, **kwargs):
        code = sku_data.extract_first()
        item['sku'] = code if code.isdigit() else ''

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
        color = ''
        desc = description.extract_first().strip()
        if "COLOR" in desc.upper():
            color = desc.upper().split(":")[-1]

        item['description'] = desc
        item["color"] = color
        
    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//del[@data-compare-at-price]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//span[@data-price]/text()').extract()[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//span[@data-price]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//span[@data-price]/text()').extract()[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="images-container"]//div[@class="thumb-container"]/img/@src').extract()
        images = []
        for img in imgs:
            img = 'https:' + img
            if img not in images:
                images.append(img)

        return images
        
    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//article//div[@class="product-image-container"]/a/@href').extract())
        return number
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
    name = 'baseblu'
    merchant = 'Base Blu'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//span[@class="l-search_result-paging-controls-loaded js-paging-controls-loaded"]/text()', _parser.page_num),
            items = '//article',
            designer = './/div[@class="manufacturer_name"]/text()',
            link = './/div[@class="product-image-container"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"btn-add-to-cart")]/span/text()', _parser.checkout)),
            ('images',('//div[contains(@class,"product-page__gallery-slide")]/a/@href',_parser.images)), 
            ('color','//span[@class="js_color-description h-hidden"]/text()'),
            ('sku',('//div[contains(@class,"product-page__wishlist")]/@data-wishlist-product-id',_parser.sku)),
            ('name', '//span[@class="product-page__title"]/text()'),
            ('description', ('//div[@class="product-page__card__content"]/text()',_parser.description)),
            ('designer','//span[@class="product-page__vendor"]/text()'),
            ('sizes',('//select[@id="group_1"]/option/text()',_parser.sizes)),
            ('prices', ('//div[@class="product-page__price"]', _parser.prices)),
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
            size_info_path = '//ul[@class="data-sheet"]/li/text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.baseblu.com/en/man/accessories/?resultsPerPage=20000",
                "https://www.baseblu.com/en/man/jewellery/?resultsPerPage=20000",
            ],
            b = [
                "https://www.baseblu.com/en/man/bags/?resultsPerPage=20000"
            ],
            c = [
                "https://www.baseblu.com/en/man/clothing/?resultsPerPage=20000",
            ],
            s = [
                "https://www.baseblu.com/en/man/footwear/?resultsPerPage=20000",
            ],

        ),
        f = dict(
            a = [
                "https://www.baseblu.com/en/woman/accessories/?resultsPerPage=20000",
                "https://www.baseblu.com/en/woman/jewellery/?resultsPerPage=20000",
            ],
            b = [
                "https://www.baseblu.com/en/woman/bags/?resultsPerPage=20000",
            ],
            c = [
                "https://www.baseblu.com/en/woman/clothing/?resultsPerPage=20000",
            ],
            s = [
                "https://www.baseblu.com/en/woman/footwear/?resultsPerPage=20000",
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
            currency = 'USD',
        ),
# Cant figure out how they are changing country
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            vat_rate = 1.085,
        ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # KR = dict(
            
        #     currency = 'KRW',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # SG = dict(
            
        #     currency = 'SGD',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # HK = dict(
           
        #     currency = 'HKD',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # GB = dict(
           
        #     currency = 'GBP',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # RU = dict(
           
        #     currency = 'RUB',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # CA = dict(
            
        #     currency = 'CAD',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # AU = dict(
           
        #     currency = 'AUD',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),
        # DE = dict(
           
        #     currency = 'EUR',
        #     currency_sign = u'\u20ac',
        # ),
        # NO = dict(

        #     currency = 'NOK',
        #     discurrency = "EUR",
        #     currency_sign = u'\u20ac',
        # ),    
        )

        


