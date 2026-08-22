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
        instock = checkout.xpath('//button[@title="Add to Cart"]')
        outstock = checkout.xpath('//button[@title="Out of stock"]')
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_data = int(data.split('(')[-1].split(' ')[0].strip())/24 +1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = i+1
        url = urljoin(response_url.split('?')[0], '?p=%s'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().upper()
        item['sku'] = sku

    def _images(self, script, item, **kwargs):
        img_dict = json.loads(script.extract_first())
        imgs = img_dict['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        images = []
        for img in imgs:
            images.append(img['img'])
        item['cover'] = images[0]
        item['images'] = images
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('.//div[@itemprop="description"]//text()').extract() + description.xpath('.//div[@class="product-detailed-description"]//text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []
        if item['category'] in ['a','b']:
            if not sizes:
                size_li.append('IT')
            else:
                size_li = sizes
        else:
            for size in sizes:
                if size.strip() not in size_li:
                    size_li.append(size.strip())
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        price = prices.extract_first()
        item['originlistprice'] = price
        item['originsaleprice'] = price
    def _color(self, color, item, **kwargs):
        try:
            item['color'] = color.extract_first().split('color:')[-1].split(',')[0].replace("'","").strip().upper()
        except:
            item['color'] = ''
        item['designer'] = 'GINETTE NY'

    def _parse_images(self, response, **kwargs):

        imgs = response.xpath('//script[contains(text(),"mage/gallery/gallery")]/text()').extract_first()
        img_dict = json.loads(imgs)
        imgs = img_dict['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        images = []
        for img in imgs:
            images.append(img['img'])
        

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="results-count"]/text()').extract_first().split('(')[-1].split(' ')[0].strip())
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'ginette'
    merchant = 'Ginette NY'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="results-count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@class="item product product-item"]',
            designer = './/html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="product-addtocart-button"]', _parser.checkout)),
            ('images',('//script[contains(text(),"mage/gallery/gallery")]/text()',_parser.images)), 
            ('sku',('//@data-product-sku',_parser.sku)),
            ('name', '//span[@itemprop="name"]/text()|//span[@data-ui-id="page-title-wrapper"]/text()'),
            ('color',('//script[contains(text(),"color:")]/text()',_parser.color)),
            ('description', ('//html',_parser.description)),
            ('prices', ('//div[@class="product-info-price"]//span[@data-price-type="finalPrice"]/@data-price-amount', _parser.prices)),
            ('sizes',('//div[@id="group_size"]//span/label/text()',_parser.sizes)),
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
                "https://www.ginette-ny.com/US/ginette-loves-men.html?p=1"
            ]

        ),
        f = dict(

            a = [
                'https://www.ginette-ny.com/US/ginette-for-her.html?p=1',
                "https://www.ginette-ny.com/US/little-ginette.html?p=1"
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
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            country_url = '/US/'
            
            ),

        GB = dict(
        	area = 'EU',
            discurrency = 'EUR',
            country_url = '/EU/'

        ),


        DE = dict(
            area = 'EU',
            currency = 'EUR',
            country_url = '/EU/'       

        ),

#      
        )

        


