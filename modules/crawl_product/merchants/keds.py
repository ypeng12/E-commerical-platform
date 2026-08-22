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
        pages = int(data.strip().lower().split('prod')[0].strip())/24
        return pages+1

    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = (response_url+'?sz=24&start=0&format=page-element').replace('&start=0','&start='+str(24*i))
        return url

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].split(':')[-1].upper().strip()

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            img = img
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        item['designer'] = "KEDS"
        description = description.extract()
        
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        color = item['color']
        sizes = sizes_data.extract()[0].strip()
        sizes = json.loads(sizes)
        size_li = []
        try:
            for v in sizes["variations"]:
                v = sizes["variations"][v]
                if v['isAvailable'] and v['color']==color:
                    size_li.append(str(v["sizeDisplayValue"])+':'+str(v["widthDisplayValue"]))
            item['originsizes'] = size_li
        except:
            item['originsizes'] = size_li
            if item['category'] in ['a','b'] and size_li==[]:
                item['originsizes'] = ['IT']
        for c in sizes['color']['values']:
            if c['ID'] == item['color']:
                item['color'] = c['displayValue']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="price-sales promo-price bfx-sale-price"]/text()').extract()
        regularPrice = prices.xpath('.//span[@class="price-standard bfx-list-price"]/text()').extract()
        if len(salePrice) == 0:
            salePrice = prices.xpath('.//span[@class="price-sales bfx-sale-price"]/text()').extract_first()  
            item['originlistprice'] = salePrice.strip()
            item['originsaleprice'] = salePrice.strip()        
        else:
            try:
                item['originlistprice'] = regularPrice[0].strip()
                item['originsaleprice'] = salePrice[0].strip().upper().replace('SALE','').strip()
            except:
                item['error'] = "price can't ba processed"

    def _parse_images(self, response, **kwargs):
        img_li = images.xpath('//div[@class="main-product-slider"]/ul/li/a/@href').extract()
        images = []
        for img in img_li:
            img = img
            if img not in images:
                images.append(img)
        return images
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//h3[@class="product-result-count"]/text()').extract_first().strip().lower().split('prod')[0].strip())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'keds'
    merchant = "Keds"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//h3[@class="product-result-count"]', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-tile"]',
            designer = './/h3[@class="list-product-brand"]/text()',
            link = './/li[@class="small-product-item"]/a/@href|.//meta[@itemprop="url"]/@content|.//li[@class="small-product-item"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add-to-cart"]', _parser.checkout)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('color',"//h1[@itemprop='name']/@data-stock-number"),
            # ('sku', ('//div[@class="b-product_master_id"]/text()', _parser.sku)),
            ('description', ('//div[@id="pdp-drawer-description-content"]//text()',_parser.description)), # TODO:
            ('sizes', ('//div[contains(@id,"productDimensionsAndVariations")]/text()', _parser.sizes)),
            ('images', ('//div[@class="main-product-slider"]/ul/li/a/@href', _parser.images)),
            ('prices', ('//html', _parser.prices))
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

        ),
        f = dict(
            a = [
                "https://www.keds.com/en/womens-accessories/?prefn1=itemStyle&prefv1=Hats"
            ],
            b = [
                "https://www.keds.com/en/womens-accessories/?prefn1=itemStyle&prefv1=Bags"
            ],
            c = [
                "https://www.keds.com/en/womens-accessories/?prefn1=itemStyle&prefv1=Socks"
            ],
            s = [
                "https://www.keds.com/en/women-styles-viewallkeds/"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )
# preferredCountry
# preferredLanguage

    countries = dict(
        US = dict(
            area = 'EU',
            language = 'EN', 
            currency = 'USD',
            cookies = {'preferredCountry':'US'},
            ),
            ## Have Different Website for differnet Countries
        # CN = dict(
        #     area = 'EU',
        #     currency = 'CNY',
        #     discurrency = 'EUR',
        #     cookies = {
        #     'preferredCountry':'CN'
        #     },
        # ),
        # JP = dict(
        #     area = 'EU',
        #     currency = 'JPY',
        #     cookies = {
        #     'preferredCountry':'JP'
        #     },
        # ),
        # KR = dict(
        #     area = 'EU',
        #     currency = 'KRW',
        #     cookies = {
        #     'preferredCountry':'KR'
        #     },
        # ),
        # SG = dict(
        #     area = 'EU',
        #     currency = 'SGD',
        #     discurrency = 'EUR',
        #     cookies = {
        #     'preferredCountry':'SG'
        #     },
        # ),
        # HK = dict(
        #     area = 'EU',
        #     currency = 'HKD',
        #     discurrency = 'EUR',
        #     cookies = {
        #     'preferredCountry':'HK'
        #     },
        # ),
        # GB = dict(
        #     area = 'EU',
        #     currency = 'GBP',
        #     country_url ="&Country=GB&",
        #     cookies = {
        #     'preferredCountry':'GB'
        #     },
        # ),
        # RU = dict(
        #     area = 'EU',
        #     currency = 'RUB',
        #     discurrency = 'EUR',
        #     cookies = {
        #     'preferredCountry':'RU'
        #     },
        # ),
        # CA = dict(
        #     area = 'EU',
        #     currency = 'CAD',
        #     discurrency = 'USD',
        #     cookies = {
        #     'preferredCountry':'CA'
        #     },
        # ),
        # AU = dict(
        #     area = 'EU',
        #     currency = 'AUD',
        #     discurrency = 'EUR',
        #     cookies = {
        #     'preferredCountry':'AU'
        #     },
        # ),
        # DE = dict(
        #     area = 'EU',
        #     currency = 'EUR',
        #     cookies = {
        #     'preferredCountry':'DE'
        #     },
        # ),
        # NO = dict(
        #     area = 'EU',
        #     currency = 'NOK',
        #     cookies = {
        #     'preferredCountry':'NO'
        #     },
        # ),


        )
        


