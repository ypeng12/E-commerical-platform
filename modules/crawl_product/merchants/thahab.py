from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from lxml import etree
import requests
import json
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "Sold Out" in checkout.extract_first():
            return True
        else:
            return False

    def _page_num(self, data, **kwargs):
        page_num = int(data)
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('/page/')[0] + '/page/%s'%(i)
        return url

    def _name(self, res, item, **kwargs):
        name_json = json.loads(res.extract_first())
        item['tmp'] = name_json['product']
        item['name'] = item['tmp']['title'].upper()
        item['designer'] = item['tmp']['vendor'].upper()

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['images']
        images = []
        for img in imgs:
            if 'https' not in img:
                images.append("https:" + img)

        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        # if "Color:" in item['description']:
        #     item['color'] = item['description'].split("Color:")[-1].split()


    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = json.loads(sku_data.extract_first())['productId']
        item["color"] = item["color"].upper()
        item['designer'] = item['designer'].upper()
        

    def _sizes(self, res, item, **kwargs):
        sizes_json = json.loads(res.extract_first())
        sizes = sizes_json['offers']
        size_li = []
        for size in sizes:
            if 'InStock' in size['availability']:
                size_li.append(size['name'].split('/')[1])
        item['originsizes'] = size_li

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, res, item, **kwargs):
        prices_json = item['tmp']
        listprice = str(prices_json['compare_at_price_max'])
        saleprice = str(prices_json['price'])
        item['originsaleprice'] = saleprice[0:-2] + '.' + saleprice[-2:]
        item['originlistprice'] = listprice[0:-2] + '.' + listprice[-2:] if listprice != '0' else item['originsaleprice']

    def _parse_images(self, response, **kwargs):
        imgs_data = json.loads(response.xpath('//script[@data-product-json]/text()').extract_first())
        images = []
        imgs = imgs_data['product']['images']
        for img in imgs:
            if "https:" not in images:
                images.append("https:" + img)

        return images
        

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="woocommerce-result-count sidebar"]/text()').extract_first().strip().lower().split("of")[-1].split("results")[0].replace(',',''))
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'thahab'
    merchant = 'THAHAB'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//ul[@class="page-numbers"]//li[last()-1]//text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="tc-product-detail"]',
            designer = './/a[@class="tc-product-detail__brand"]/text()',
            link = './/h3//a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"ProductForm__AddToCart")]', _parser.checkout)),
            ('name',('//script[@data-product-json]/text()',_parser.name)),
            ('images',('//div[@class="Product__SlideshowNavScroller"]//a/img/@src',_parser.images)),
            ('color','//span[@class="ProductForm__Label"]/span[@class="ProductForm__SelectedValue"]/text()'),
            ('sku',('//div[@id="shopify-section-recently-viewed-products"]/section/@data-section-settings',_parser.sku)),
            ('description', ('//div[@class="Product_Description_Tab"]/ul/li/text()',_parser.description)),
            ('sizes',('//script[@type="application/ld+json"][contains(text(),"offers")]/text()',_parser.sizes)),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://thahab.com/product-category/men/accessories-men/page/1"

            ],
            b = [
                "https://thahab.com/product-category/men/bags-men/page/1"
            ],
            c = [
                "https://thahab.com/product-category/men/clothing-men/page/1",

            ],
            s = [
                "https://thahab.com/product-category/men/shoes-men/page/1"
            ],
            e  = [
                "https://thahab.com/product-category/men/grooming/page/1"
            ],

        ),
        f = dict(
            a = [
                "https://thahab.com/product-category/jewelry/page/1",
                "https://thahab.com/product-category/women/accessories/page/1"
                ],
            b = [
                "https://thahab.com/product-category/bags/page/1"
            ],

            c = [
                "https://thahab.com/product-category/women/clothing/page/1",
            ],
            s = [
                "https://thahab.com/product-category/shoes/page/1"
            ],
            e = [
                "https://thahab.com/product-category/women/beauty/page/1"
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
            ),

        
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        CN = dict(
            currency = 'CNY',
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
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
        )
        )

        


