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

    def _page_num(self, url, **kwargs):
        page_num = 10
        return int(page_num)
  
    def _sku(self, sku_data, item, **kwargs):
        script = sku_data.extract_first()
        data = json.loads(script.split('__st=')[-1][:-1])
        item['sku'] = str(data['rid']) + '_' + item['color'].upper()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            img = img.split("?")[0].replace('cdn.shopify.com','cdn.shopifycdn.net')
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        item['images'] = images
        item['cover'] = item['images'][0] if item['images'] else ''
        
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
        # sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            if size.xpath('.//span[@class="availability"]/text()').extract_first() == "InStock":
                
                if size.xpath('.//span[@class="custom_fields"]/span[@class="COLOR"]/text()').extract_first() == item["color"]:
                    try:
                        s = item["tmp"]
                    except:
                        item["tmp"] = size

                    size = size.xpath('.//span[@class="custom_fields"]/span[@class="SIZE"]/text()').extract_first()
                    item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        item["designer"] = "NILI LOTAN"

    def _prices(self, prices, item, **kwargs):
        prices  = item['tmp']

        try:
            item['originlistprice'] = item['tmp'].xpath('.//span[@class="list_price"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-shop-album-mobile product-shop-album active"]/div/a/@href').extract()
        images = []
        for img in imgs:
            img = img.split("?")[0].replace('cdn.shopify.com','cdn.shopifycdn.net')
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()



class Config(MerchantConfig):
    name = 'nili'
    merchant = 'Nili Lotan'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="l-search_result-paging-controls-loaded js-paging-controls-loaded"]/text()', _parser.page_num),
            items = '//a[@class="product-card-link"]',
            designer = './div/span/@data-product-brand',
            link = './@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="TryNowBuy"]|//*[@id="TryNowBuyMobile"]|//button[@class="product-shop-add-to-cart js-product-shop-select-size btn btn-solid"]|//button[contains(@class,"pdp-add-to-cart")]', _parser.checkout)),
            ('name','//h2[@class="product-shop-title"]/text()'),
            ('images',('//div[@class="product-shop-album-mobile product-shop-album active"]/div/a/@href',_parser.images)),
            ('color','//div[@class="product-shop-album-mobile product-shop-album active"]/@data-product-color'),
            ('description', ('//div[@class="product-info-content tab-content active"]//p/text()',_parser.description)),
            ('sizes',('//span[@class="nosto_sku"]',_parser.sizes)),
            ('prices', ('//div[@class="b-product_container-price"]', _parser.prices)),
            ('sku',('//script[@id="__st"]/text()',_parser.sku)),
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
        m = dict(
        ),
        f = dict(
            a = [
                "https://www.nililotan.com/collections/accessories?page=",
            ],
            c = [

                "https://www.nililotan.com/collections/dresses?page=",
                "https://www.nililotan.com/collections/tops?page=",
                "https://www.nililotan.com/collections/tees?page=",
                "https://www.nililotan.com/collections/pants?page=",
                "https://www.nililotan.com/collections/sweats?page=",
                "https://www.nililotan.com/collections/outerwear?page=",
                "https://www.nililotan.com/collections/jackets?page=",
                "https://www.nililotan.com/collections/sweaters?page=",
            ],
        params = dict(
            # TODO:

            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
         US = dict(
            currency = 'USD',
            currency_sign = '$',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22US%22%2C%22cultureCode%22%3A%22zh-CHS%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
            ),
# AS soon JS stops, it shift back to USD cookies are okay here
        # CN = dict(
        #     currency = 'CNY',
        #     # discurrency = 'GBP',
        #     currency_sign = u'CN\xa5',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22CN%22%2C%22currencyCode%22%3A%22CNY%22%2C%22cultureCode%22%3A%22en-GB%22%7D"
        #     }
        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     # discurrency = 'GBP',
        #     currency_sign = u'\xa5',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22JP%22%2C%22cultureCode%22%3A%22ja%22%2C%22currencyCode%22%3A%22JPY%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     # discurrency = 'GBP',
        #     currency_sign = u'\u20a9',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22KR%22%2C%22cultureCode%22%3A%22ja%22%2C%22currencyCode%22%3A%22KRW%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     # discurrency = 'GBP',
        #     currency_sign = 'S$',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22SG%22%2C%22cultureCode%22%3A%22ko-KR%22%2C%22currencyCode%22%3A%22SGD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     # discurrency = 'GBP',
        #     currency_sign = 'HK$',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22HK%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22HKD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # GB = dict(
        #     currency = 'GBP',
        #     currency_sign = u'\xa3',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22GB%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22GBP%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # RU = dict(
        #     # discurrency = 'GBP',
        #     currency = 'RUB',
        #     currency_sign = 'RUB',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22RU%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22RUB%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     # discurrency = 'GBP',
        #     currency_sign = 'CA$',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22CA%22%2C%22cultureCode%22%3A%22ru%22%2C%22currencyCode%22%3A%22CAD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     # discurrency = 'GBP',
        #     currency_sign = 'AU$',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22AU%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22AUD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     # discurrency = 'GBP',
        #     currency_sign = u'\u20ac',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22DE%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22EUR%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     # discurrency = 'GBP',
        #     currency_sign = 'Nkr',
        #     cookies = {
        #     "GlobalE_Data":"%7B%22countryISO%22%3A%22NO%22%2C%22cultureCode%22%3A%22de%22%2C%22currencyCode%22%3A%22NOK%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
        #     }
        # ),
        )

        


