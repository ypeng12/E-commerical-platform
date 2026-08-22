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


    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
            if not cover and "-1.jpg" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip().replace('\n','')
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        
          


    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = sku_data.extract()[0].strip()
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            if 'out' in size.lower():
                continue

            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = prices.xpath('.//span[@class="regular-price"]/text()').extract()[0].replace('"','')
            item['originsaleprice'] = prices.xpath('.//span[@class="price has-discount"]/text()').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//span[@class="price"]/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[@class="price"]/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//ul[@class="product-images-cover"]/li/a/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https://" + img
            if img not in images:
                images.append(img)

        return images
        

    def _color(self, response, item,**kwargs):
        colors = (response.extract())
        item['color'] = ''
        for c in colors:
            c = c.replace('\t','').replace('\n','')
            if c.replace(' ','') == '':
                continue
            item['color'] = c.strip().replace('\n','').replace('\t','')

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath("//article/a/@href").extract())
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'officine'
    merchant = 'Officine Generale'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//div[@class="result-count"]/text()',_parser.page_num),

            items = '//article',
            designer = './/div[@class="item-title"]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//div[@id="add-to-cart"]', _parser.checkout)),
            ('name','//h1[@itemprop="name"]/text()'),
            ('designer','//meta[@itemprop="brand"]/@content'),
            ('images',('//ul[@class="product-images-cover"]/li/a/@href',_parser.images)),
            ('color',('//*[@id="axproductsgroups_product"]//option[@selected]//text()',_parser.color)),
            ('sku',('//meta[@itemprop="productID"]/@content',_parser.sku)),
            ('description', ('//meta[@itemprop="description"]/@content',_parser.description)),
            ('sizes',('//select[@id="group_4"]/option/@title',_parser.sizes)),
            ('prices', ('//div[@class="product-prices"]', _parser.prices)),
            

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
                "https://us.officinegenerale.com/en/459-accessories?p="
            ],

            c = [
                "https://us.officinegenerale.com/en/449-outerwear?p=",
                "https://us.officinegenerale.com/en/450-shirts?p=",
                "https://us.officinegenerale.com/en/451-jackets?p=",
                "https://us.officinegenerale.com/en/452-pants?p=",
                "https://us.officinegenerale.com/en/453-suits?p=",
                "https://us.officinegenerale.com/en/454-leathers?p=",
                "https://us.officinegenerale.com/en/455-t-shirts-sweats?p=",
                "https://us.officinegenerale.com/en/456-knitwear?p=",
                "https://us.officinegenerale.com/en/457-denim?p=",
            ],
            s = [
                "https://us.officinegenerale.com/en/458-shoes?p="
            ],

        ),
        f = dict(

            a = [
                "https://us.officinegenerale.com/en/459-accessories?p="
            ],
            c = [
                "https://us.officinegenerale.com/en/460-outerwear?p=",
                "https://us.officinegenerale.com/en/505-suits?p=",
                "https://us.officinegenerale.com/en/461-knitwear?p=",
                "https://us.officinegenerale.com/en/462-dresses?p=",
                "https://us.officinegenerale.com/en/463-jackets?p=",
                "https://us.officinegenerale.com/en/464-pants?p=",
                "https://us.officinegenerale.com/en/465-shirts?p=",
                "https://us.officinegenerale.com/en/466-leathers?p=",
                "https://us.officinegenerale.com/en/467-denim?p=",
                "https://us.officinegenerale.com/en/468-skirts?p="
            ],
            s = [
                "https://us.officinegenerale.com/en/470-shoes?p="
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
            country_url = 'us.',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'EUR',
            country_url = 'www.',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'EUR',
            country_url = 'www.',

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'EUR',
            country_url = 'www.',

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            country_url = 'www.',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'EUR',
            country_url = 'www.',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'EUR',
            country_url = 'uk.',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            country_url = 'www.',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            country_url = 'www.',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = 'www.',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = 'www.',
        ),
       
        )

        


