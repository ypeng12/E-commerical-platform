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

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + "?page="+str((i))
        return url
    def _page_num(self, data, **kwargs):
        page = 99
        return page

    def _sku(self, sku_data, item, **kwargs):
        obj = json.loads(sku_data.extract_first().strip())
        item['sku'] = obj["mpn"]

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = "https:" + img.split("('")[-1].split("'")[0].replace('50x','800x')
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

        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//s[@data-compare-price]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//meta[@itemprop="price"]/@content').extract()[0].strip()
        except:

            item['originsaleprice'] = prices.xpath('.//meta[@itemprop="price"]/@content').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//meta[@itemprop="price"]/@content').extract()[0].strip()

        


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@data-component-id]//div[@class="bg-area-placeholder"]/@style').extract()

        images = []
        for img in imgs:
            img = "https:" + img.split("('")[-1].split("'")[0].replace('50x','800x')
            if img not in images:
                images.append(img)

        return images
        





_parser = Parser()



class Config(MerchantConfig):
    name = 'renskincare'
    merchant = 'RenSkincare'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="product_count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"product-grid-item")]',
            designer = './/div[contains(@class,"pro_list_manufacturer")]',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//button/@data-add-to-cart', _parser.checkout)),
            ('images',('//div[@data-component-id]//div[@class="bg-area-placeholder"]/@style',_parser.images)), 
            ('sku',('//main//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//h1/text()'),
            ('designer','//meta[@itemprop="brand"]/@content'),
            ('description', ('//meta[@itemprop="description"]/@content',_parser.description)),
            ('sizes',('//main//*[@name="properties[Size]"]/value',_parser.sizes)),
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
        )

    list_urls = dict(
        f = dict(
            e = [
                "https://usa.renskincare.com/collections/face?page=1",
                "https://usa.renskincare.com/collections/body?page=1",
                "https://usa.renskincare.com/collections/value-sets?page=1",
                "https://usa.renskincare.com/collections/gift?page=1"
            ],


        ),
        m = dict(
            a = [
                
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
            country_url = "//usa."
        ),



        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = "\u00A3",
            country_url = "//www."

        ),



   
        )

        


