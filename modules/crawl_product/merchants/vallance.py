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
        json_Data = checkout.extract_first().split('=')[-1].strip().split(';')[0]
        obj = json.loads(json_Data)
        
        if obj["product_attributes"]:
            item['tmp'] = obj["product_attributes"]
            return False
        else:
            return True

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + "?page="+str((i))
        return url
    def _page_num(self, data, **kwargs):
        page = 20
        return page

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().strip()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
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
        sizes1 = item['tmp']['available_variant_values']
        item['originsizes'] = []
        for size in sizes1:
            s = sizes.xpath("//button[@data-option-value='"+str(size)+"']/span[@class='p-product-view__sizes-value']/text()").extract_first().split(',')[0].strip().strip().replace('-','').strip()
            item['originsizes'].append(s)

        if not sizes1:
            item['originsizes'] = ['']

        
    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = str(item['tmp']['price']['non_sale_price_with_tax']['value'])
            item['originsaleprice'] = str(item['tmp']['price']['sale_price_with_tax']['value'])
        except:

            item['originsaleprice'] = str(item['tmp']['price']['with_tax']['value'])
            item['originlistprice'] =str(item['tmp']['price']['with_tax']['value'])

        


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//a[@class="productView-thumbnail-link"]/@href').extract()

        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
        





_parser = Parser()



class Config(MerchantConfig):
    name = 'vallance'
    merchant = 'Rebecca Vallance'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="product_count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//article',
            designer = './@data-product-brand',
            link = './/figure[@class="c-card__figure"]/a/@href',
            ),
        product = OrderedDict([
        	('checkout', ("//script[contains(text(),'BCData')]/text()", _parser.checkout)),
            ('images',('//a[@class="productView-thumbnail-link"]/@href',_parser.images)), 
            ('sku',('//div[@class="storeAvailabilityModal-form-product-sku"]/text()',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//h1/text()'),
            ('designer','//div/@data-product-brand'),
            ('description', ('//li[@id="tab-description"]//p/text()',_parser.description)),
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

    list_urls = dict(
        f = dict(
            c = [
                "https://www.rebeccavallance.com/e-boutique/shop-all/?page=1",
                "https://www.rebeccavallance.com/bridal/all-bridal/?page=1",
                "https://www.rebeccavallance.com/sportif/all-sportif/?page=1",
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
            discurrency = 'AUD',
        ),



        CN = dict(
            currency = 'CNY',
            duscurrency = "AUD"
        ),
        JP = dict(
            currency = 'JPY',
            duscurrency = "AUD"
        ),
        KR = dict(

            currency = 'KRW',
            duscurrency = "AUD",
            
        ),
        SG = dict(
            currency = 'SGD',
            duscurrency = "AUD",
        ),
        HK = dict(
            currency = 'HKD',
            duscurrency = "AUD",
        ),
        GB = dict(
            currency = 'GBP',
            duscurrency = "AUD",
        ),
        RU = dict(
            currency = 'RUB',
            duscurrency = "AUD",
        ),

        AU = dict(
            currency = 'AUD',
            
        ),
        DE = dict(
            currency = 'EUR',
            duscurrency = "AUD",
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            duscurrency = "AUD",
        ), 



   
        )

        


