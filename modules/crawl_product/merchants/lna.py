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
        scripts_data = data.extract()
        for script in scripts_data:
            if "var meta = {" in script:
                script_str = script
                break
        script_str = script_str.split("var meta = ")[-1].split(";")[0]
        json_dict = json.loads(script_str)

        item['designer'] = 'LNA'
        item['sku'] = json_dict['product']['variants'][0]['sku'].strip().upper()
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip().replace('  ','')
            if desc.strip() == '' or desc.strip() == ' ':
                continue

            desc_li.append(desc.strip())

        description = '\n'.join(desc_li)

        item['description'] = description.strip()

    def _sizes(self, sizes_data, item, **kwargs):

        sizes = sizes_data.extract()

        item['originsizes'] = []
        if len(sizes) != 0:

            for size in sizes:
                size = size.strip()
                if size !='':
                    item['originsizes'].append(size)

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']
        item["color"] = item["color"].split(":")[-1]
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="product-price on-sale"]/text()').extract()
        listPrice = prices.xpath('.//span[@class="product-compare-price"]/text()').extract()
        if len(listPrice) == 0:
            salePrice = prices.xpath('.//div[@class="product-single__price"]/span/text()').extract()
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = salePrice[0]
        else:
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = listPrice[0]


   

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[contains(@class,"product-gallery__main")]/div//img/@data-src').extract()
        images = []
        for img in img_li:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)
        return images


_parser = Parser()



class Config(MerchantConfig):
    name = 'lna'
    merchant = "LNA"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//div[@class="pager"]/p[@class="amount"]/text()',_parser.page_num),
            items = '//a[@class="grid-view-item__link grid-view-item__image-container product-card__link"]',
            designer = './/div[@class="product-impression-data hide"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@name="add"]', _parser.checkout)),
            ('name', '//h1/text()'),
            ('color','//div[@class="color-swatches__wrapper"]/label/text()'),
            ('images', ('//div[contains(@class,"product-gallery__main")]/div//img/@data-src', _parser.images)),
            ('sku', ('//script/text()', _parser.sku)),
            ('description', ('//div[@class="pdp-accordion__tab rte"]//text()',_parser.description)), # TODO:
            ('sizes', ('//div[contains(@class,"swatch--size")]//div[contains(@class,"available")]/@data-value', _parser.sizes)),
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
        )

    list_urls = dict(
        f = dict(

            c = [
                'https://www.lnaclothing.com/collections/shop-all?p=',
            ],


        ),
        m = dict(

            c = [
                'https://www.lnaclothing.com/collections/mens-tees?p=',
            ],



        params = dict(
            # page = 1,
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',

            ),

        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD', 
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),

        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        )
        


