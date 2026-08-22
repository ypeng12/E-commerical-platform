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
        if checkout:
            return False
        else:
            return True
    def _page_num(self, data, **kwargs):
        page_num = int(data)
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('/page/1/','/page/%s'%(i))
        return url

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
        # if "Color:" in item['description']:
        #     item['color'] = item['description'].split("Color:")[-1].split()


    def _sku(self, sku_data, item, **kwargs):

        item['sku'] = sku_data.extract_first().strip()
        item["color"] = item["color"].upper()
        item['designer'] = item['designer'].upper()
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            if 'choose' not in size.strip().lower():
                item['originsizes'].append(size.strip().split('-')[0])

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//del//span[@class="woocommerce-Price-amount amount"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//ins//span[@class="woocommerce-Price-amount amount"]/text()').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//span[@class="woocommerce-Price-amount amount"]/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[@class="woocommerce-Price-amount amount"]/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"product-single__media-image")]/a/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images
        

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="woocommerce-result-count sec-FilterTotal"]/text()').extract_first().strip().lower().split("of")[-1].split("pieces")[0].replace(',',''))
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'minox'
    merchant = 'Minox Boutique'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//ul[@class="page-numbers"]//li[last()-1]//text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="crd-Product"]',
            designer = './/h4[@class="crd-Product_Vendor"]/a/text()',
            link = './/h3//a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@name="add-to-cart"]', _parser.checkout)),
            ('name','//h1[@class="product_title entry-title"]/text()'),
            ('designer','//h4[@class="crd-Product_Vendor"]/a/text()'),
            ('images',('//div[@class="sec-Product_ThumbnailWrap"]/img/@src',_parser.images)),
            ('color','//select[@id="pa_color"]/option[@selected="selected"]/text()'), 
            ('sku',('//p[@id="ProductPrice"]//@data-product-id',_parser.sku)),
            ('description', ('//div[@data-tab-title="Description"]//text()',_parser.description)),
            ('sizes',('//select[@id="size"]/option/text()',_parser.sizes)),
            ('prices', ('//p[@id="ProductPrice"]', _parser.prices)),
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
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=men&product_cat=home-collection&currency=USD&i="
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=men&product_cat=scarves&currency=USD&i="

            ],
            b = [
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=men&product_cat=backpacks&currency=USD&i=",
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=men&product_cat=purses-wallets&currency=USD&i="
            ],
            c = [
                "https://minoxboutique.co.uk/product-category/clothing//page/1?product_tag=men&currency=USD&i=",

            ],
            s = [
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=men&product_cat=footwear&currency=USD&i="
            ],


        ),
        f = dict(
            a = [
                "https://minoxboutique.co.uk/product-category/home-collection/page/1?product_tag=women&currency=USD&i=",
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=women&product_cat=hats&currency=USD&i=",
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=women&product_cat=scarves&currency=USD&i="
                ],
            b = [
                "https://minoxboutique.co.uk/product-category/accessories/backpacks/page/1/?product_tag=women&currency=USD&i=",
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=women&product_cat=handbags&currency=USD&i=",
                "https://minoxboutique.co.uk/shop/page/1/?product_tag=women&product_cat=purses-wallets&currency=USD&i="
            ],

            c = [
                "https://minoxboutique.co.uk/product-category/clothing/page/1/?product_tag=women&currency=USD&i=",
            ],
            s = [
                "https://minoxboutique.co.uk/product-category/footwear/page/1/?product_tag=women&currency=USD&i="
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
            country_url = "&currency=USD",
            ),

        
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        ),
        CN = dict(
            currency = 'CNY',
            country_url = "&currency=CNY",
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        ),
        GB = dict(
            currency = 'GBP',
            country_url = "&currency=GBP",
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            country_url = "&currency=GBP",
        )
        )

        


