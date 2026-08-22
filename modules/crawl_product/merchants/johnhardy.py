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



    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = item["cover"].lower().split("_main")[0].split("/")[-1].upper()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img.split("?")[0]

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
     
            if "select" in size.lower():
                continue
            else:
                item['originsizes'].append(size.strip())

        if not sizes:
            sizes = ['IT']

        
    def _prices(self, prices, item, **kwargs):
        if  prices.xpath('.//span[@itemprop="highPrice"]/text()').extract():
            
            rangePrice = prices.xpath('./div/text()').extract()
            for r in rangePrice:
                if r.strip() != "":
                    rangePrice = r.strip()
                    break

            try:
                item['originsaleprice'] = rangePrice.strip().split("-")[0].split('"')[-1].strip()
                item['originlistprice'] = rangePrice.strip().split("-")[-1].split('"')[-1].strip()
            except:
                pass

        else:
            item['originsaleprice'] = prices.xpath('.//span[@itemprop="lowPrice"]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//span[@itemprop="lowPrice"]/text()').extract()[0].strip()


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//img[@class="productthumbnail"]/@data-lazy').extract()
        images = []
        for img in imgs:
            img = img.split("?")[0]
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="results-count"]/@data-results-max').extract_first().strip())
        return number
    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info 

_parser = Parser()



class Config(MerchantConfig):
    name = 'johnhardy'
    merchant = 'John Hardy'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = '//a[@class="last"]/text()',
            items = '//div[@class="product-tile"]',
            designer = './/div[@class="brand-name"]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add-to-cart"]', _parser.checkout)),
            ('images',('//img[@class="productthumbnail"]/@data-lazy',_parser.images)), 
            ('sku',('//html',_parser.sku)),
            ('color','//li[@id="slot1-primarymaterial"]/text()'),
            ('name', '//h1[@class="product-name"]/text()'),
            ('designer','//div[@class="product-brand"]/text()'),
            ('description', ('//div[@class="details-description"]//text()',_parser.description)),
            ('sizes',('//select[@id="variations-size-qty"]/option/text()',_parser.sizes)),
            ('prices', ('//div[@id="pdpMain"]//div[@class="product-price"]', _parser.prices)),
            

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
            size_info_path = '//ul[@class="mats"]//li[contains(@id,"dimension")]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.johnhardy.com/men/?sz=9999"
            ],

        ),
        f = dict(
            a = [
                "https://www.johnhardy.com/women/?sz=9999"
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
            cookies= {
                'GlobalE_Data':'%7B%22countryISO%22%3A%22US%22%2C%22cultureCode%22%3A%22en-US%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'
            }
        ),



        
        CN = dict(
            area = 'AS',
            currency = 'CNY',
            currency_sign = 'CN\xa5',
            cookies= {
                'GlobalE_Data':'%7B%22countryISO%22%3A%22CN%22%2C%22cultureCode%22%3A%22zh-CHS%22%2C%22currencyCode%22%3A%22CNY%22%2C%22apiVersion%22%3A%222.1.4%22%7D'
            }

        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',

            currency_sign = '\xa5',
            country_url = 'store.',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22JP%22%2C%22cultureCode%22%3A%22ja%22%2C%22currencyCode%22%3A%22JPY%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},


        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            currency_sign = '\u20a9',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22KR%22%2C%22cultureCode%22%3A%22ko-KR%22%2C%22currencyCode%22%3A%22KRW%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            currency_sign = 'S$',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22SG%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22SGD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            currency_sign = 'HK$',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22HK%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22HKD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22GB%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22GBP%22%2C%22apiVersion%22%3A%222.1.4%22%7D'}

        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = "USD",
            currency_sign = "$",

            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22RU%22%2C%22cultureCode%22%3A%22ru%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'}

        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            currency_sign = 'CA$',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22CA%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22CAD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            currency_sign = "AU$",
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22AU%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22AUD%22%2C%22apiVersion%22%3A%222.1.4%22%7D'}

        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22DE%22%2C%22cultureCode%22%3A%22de%22%2C%22currencyCode%22%3A%22EUR%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},

        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            currency_sign = 'kr',
            cookies = {'GlobalE_Data':'%7B%22countryISO%22%3A%22NO%22%2C%22cultureCode%22%3A%22nb-NO%22%2C%22currencyCode%22%3A%22NOK%22%2C%22apiVersion%22%3A%222.1.4%22%7D'},
        ),
# #      
        )

        


