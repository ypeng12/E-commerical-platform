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
        jsonDict = checkout.extract_first().split('product: {')[-1].split('onVariantSelected')[0].rsplit(",",1)[0]
        
        obj = json.loads('{'+checkout.extract_first().split('product: {')[-1].split('onVariantSelected')[0].rsplit(",",1)[0])
        
        if obj['available']:
            item['tmp'] = obj
            return False
        else:
            return True

    def _parse_multi_items(self, response, item, **kwargs):


        try:
            item['color'] = item['tmp']['productColor']
        except:
            item['color'] = ''
        item['designer'] = item['tmp']['vendor'].upper()
        price = item['tmp']
        item['name'] = item['tmp']['title']
        self.prices(price, item, **kwargs)
        variants = item['tmp']['variants']

        
        if variants:
            for v in variants:
                itm = deepcopy(item)
                
                itm['color'] = v['option1']
                if 'default' in itm['color'].lower():
                    itm['color'] = ''
                mainID= response.xpath('//div[@id="pdpMain"]/@data-pid').extract_first()
                itm['sku'] = v['sku']
                if not v['available']:
                    itm['error'] = "Out of Stock"
                    itm['originsizes'] = ''
                itm['images'] = []

                for img in item['tmp']['media']:
                    if 'all' in img['alt'].lower() or item['color'].lower() in img['alt'].lower():
                        try:
                            img = img['src']
                            itm['images'].append(img)
                        except:
                            pass
                try:
                    itm['cover'] = itm['images'][0]
                except:
                    itm['cover'] = ''
                itm['name'] = itm['name'] +' '+itm['color']
                itm['color'] = itm['color'].upper()
                yield itm
        else:
            item['color'] =item['color'].upper()
            item['cover'] = item['images'][0]
            yield item



    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + "?page="+str((i))
        return url
    def _page_num(self, data, **kwargs):
        page = 2
        return page

    def _sku(self, sku_data, item, **kwargs):
        obj = json.loads(sku_data.extract_first().strip())
        item['sku'] = obj["mpn"]


        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('.//div[@class="product__details__description"]/p/text()').extract() + description.xpath('.//div[@class="product__additional-features"]/p/text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        item['designer'] = 'ColoreScience'
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):


        try:
            item['originsaleprice'] = str(item['tmp']['price']/100)
            item['originlistprice'] =  str(item['tmp']['compare_at_price']/100)
        except:

            item['originsaleprice'] = str(item['tmp']['price']/100)
            item['originlistprice'] =  str(item['tmp']['price']/100)

        


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
    name = 'colorescience'
    merchant = 'Colorescience'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//a[@class="image-link"]',
            designer = './/div[contains(@class,"pro_list_manufacturer")]',
            link = './@href',
            ),
        product = OrderedDict([
        	('checkout', ("//script[contains(text(),'OptionSelectors')]/text()", _parser.checkout)),
            # ('images',('//div[@data-component-id]//div[@class="bg-area-placeholder"]/@style',_parser.images)), 
            # ('sku',('//main//script[@type="application/ld+json"]/text()',_parser.sku)),
            # ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//h1/text()'),
            ('sizes',('//html',_parser.sizes)),
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
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(
            e = [
                "https://www.colorescience.com/collections/total-eye-collection?p=",
                "https://www.colorescience.com/collections/uv-protectors?page=1",
                "https://www.colorescience.com/collections/treatments?page=1",
                "https://www.colorescience.com/collections/primers?page=1"
                "https://www.colorescience.com/collections/foundations?p=",
                "https://www.colorescience.com/collections/enhancers?p=",
                "https://www.colorescience.com/collections/pigmentation?p=",
                "https://www.colorescience.com/collections/redness?p=",
                "https://www.colorescience.com/collections/dark-circles?p=",
                "https://www.colorescience.com/collections/aging?p=",
                "https://www.colorescience.com/collections/sensitive?p=",
                "https://www.colorescience.com/collections/oily?p=",
                "https://www.colorescience.com/collections/dry?p=",
                "https://www.colorescience.com/collections/total-protection-collection?p=",
                "https://www.colorescience.com/collections/finishing-touch-protocol-collection?p=",
                "https://www.colorescience.com/collections/treatments?p="
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
        ),


       
        )

        


