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
            return True
        else:
            return False



    def _parse_multi_items(self, response, item, **kwargs):
        
        try:

            for size1 in item["tmp"]["variants"]:
                print(size1)
                if "size" in size1:
                    size = item["tmp"]["variants"][size1]
                    # item["originsizes"] = []
                    itm = deepcopy(item)
                    
                    
                    price = size["pricing"]
                    self.prices(price, itm, **kwargs)

                    sizes2 = [size1.split("-")[-1]]

                    self.sizes(sizes2, itm, **kwargs)

                    item['sku'] = size["id"]
                    itm["name"] = itm["name"] +" - "+size1.split("-")[-1]
                    
                     
                    yield itm  
                else:
                    yield item
                    return               
        except:
            yield item
            return
        if len(item["tmp"]["variants"]) == 0:
            yield item
            return   

    def _images(self, images, item, **kwargs):
        rangePrice = ""
        if  images.xpath('.//script/text()').extract():
            for r in images.xpath('.//script/text()').extract():
                if "pdpdata" in r.strip():
                    rangePrice = r.strip()
                    break
            json1 = rangePrice.split("pdpdata = ")[-1].split(";")[0]

            obj = json.loads(json1)
            
        try:
            item["tmp"] = obj[0]
            obj = obj[0]
        except:
            item["tmp"] = obj

        imgs = obj["images"]["hiRes"]
        item["sku"] = obj["ID"].upper()
        item["designer"] = "CL\\u00c9 DE PEAU BEAUT\\u00c9"
        if item["color"]:
            item["color"] = item["color"].strip().upper()

        # imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img["url"].strip()

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
            if not desc or ".row" in desc or "[]" in desc or "margin" in desc or ".product" in desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):

        try:
            sizes = sizes.extract()
        except:
            pass

        item['originsizes'] = []
        for size in sizes:
            if size.strip() != "":
                item['originsizes'].append(size.strip())

        if len(item['originsizes']) == 0:
            item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):

        try:
            item['originsaleprice'] = str(prices["minprice"])
            item['originlistprice'] = str(prices["standard"])
        except:
            try:
                
                item['originsaleprice'] = prices.xpath('.//span[@class="price-sales"]/text()').extract()[0].strip()
                item['originlistprice'] =  prices.xpath('.//span[@class="price-sales"]/text()').extract()[0].strip()

            except:
                item['originsaleprice'] = ""
                item['originlistprice'] = ""



        

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@class="product-tile bv-redesign"]//ul[@class="swatch-list"]//a/@href|//div[@class="product-tile bv-redesign"]//a[@class="thumb-link"]/@href').extract())
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'cledepeaubeaute'
    merchant = "Cl\u00e9 de Peau beaut\u00e9"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = '//a[@class="last"]/text()',
            items = '//div[@class="product-tile bv-redesign"]',
            designer = './/div[@class="brand-name"]',
            link = './/ul[@class="swatch-list"]//a/@href|.//a[@class="thumb-link"]/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="add-to-cart"]/@disabled | //*[@id="add-all-to-cart"]/@disabled', _parser.checkout)),
            ('color','//option[@selected="selected"]/@value'),
            ('images',('//html',_parser.images)), 
            ('name', '//h1[@class="product-name"]/text()'),
            
            ('description', ('//section[contains(@id,"contentzone1")]//div//text()',_parser.description)),
            ('sizes',('//ul[@id="pdp-swatches"]//li/text()',_parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            

            ]),
        look = dict(
            ),
        swatch = dict(


            ),
        image = dict(
            ),
        size_info = dict(
         
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(
            e = [
                "https://www.cledepeaubeaute.com/makeup/?sz=9999",
                "https://www.cledepeaubeaute.com/skincare/?sz=9999",
                "https://www.cledepeaubeaute.com/gifts-and-sets/?sz=9999"
            ],

        ),
        m = dict(
            a = [
                ""
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
            area = 'US',
            currency = 'USD',

        ),



        ##Have different website for different countrues
        # CN = dict(
        #     area = 'AS',
        #     currency = 'CNY',
        #     currency_sign = u'CN\xa5',
        #     cookies= {
        #         'GlobalE_Data':'%7B%22countryISO%22%3A%22CN%22%2C%22cultureCode%22%3A%22zh-CHS%22%2C%22currencyCode%22%3A%22CNY%22%2C%22apiVersion%22%3A%222.1.4%22%7D'
        #     }

        # ),
        # JP = dict(
        #     area = 'EU',
        #     currency = 'JPY',

        #     currency_sign = u'\xa5',
        #     country_url = 'store.',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22JP%22%2C%22cultureCode%22%3A%22ja%22%2C%22currencyCode%22%3A%22JPY%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},


        # ),
        # KR = dict(
        #     area = 'EU',
        #     currency = 'KRW',
        #     currency_sign = u'\u20a9',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22KR%22%2C%22cultureCode%22%3A%22ko-KR%22%2C%22currencyCode%22%3A%22KRW%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        # ),
        # SG = dict(
        #     area = 'EU',
        #     currency = 'SGD',
        #     currency_sign = u'S$',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22SG%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22SGD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        # ),
        # HK = dict(
        #     area = 'EU',
        #     currency = 'HKD',
        #     currency_sign = 'HK$',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22HK%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22HKD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        # ),
        # GB = dict(
        #     area = 'EU',
        #     currency = 'GBP',
        #     currency_sign = u'\xa3',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22GB%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22GBP%22%2C%22apiVersion%22%3A%222.1.4%22%7D'}

        # ),
        # RU = dict(
        #     area = 'EU',
        #     currency = 'RUB',
        #     discurrency = "USD",
        #     currency_sign = u"$",

        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22RU%22%2C%22cultureCode%22%3A%22ru%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'}

        # ),
        # CA = dict(
        #     area = 'EU',
        #     currency = 'CAD',
        #     currency_sign = u'CA$',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22CA%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22CAD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        # ),
        # AU = dict(
        #     area = 'EU',
        #     currency = 'AUD',
        #     currency_sign = "AU$",
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22AU%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22AUD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'}

        # ),
        # DE = dict(
        #     area = 'EU',
        #     currency = 'EUR',
        #     currency_sign = u'\u20ac',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22DE%22%2C%22cultureCode%22%3A%22de%22%2C%22currencyCode%22%3A%22EUR%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        # ),
        # NO = dict(
        #     area = 'EU',
        #     currency = 'NOK',
        #     currency_sign = u'kr',
        #     cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22NO%22%2C%22cultureCode%22%3A%22nb-NO%22%2C%22currencyCode%22%3A%22NOK%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},
        # ),
# #      
        )

        


