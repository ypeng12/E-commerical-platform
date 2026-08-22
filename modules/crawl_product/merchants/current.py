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

    def _page_num(self, data, **kwargs):
        page_num = 10
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        item['sku'] = item["cover"].split("/")[-1].split("_")[0].strip().upper()

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'CURRENT ELLIOTT'
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            img = img
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@class="wear desktop"]/div/text()').extract() + description.xpath('.//div[@id="prod_details"]//div[@class="detail"]/div//text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        
        sizes = sizes_data.extract()

        item['originsizes'] = []
        if len(sizes) != 0:

            for size in sizes:
                size = size.strip()
                if size !='' and size not in item['originsizes']:
                    item['originsizes'].append(size)

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[contains(@id,"old-price")]/text()').extract()
        listPrice = prices.xpath('.//span[contains(@id,"product-price")]/span[2]/text()').extract()
        if len(listPrice) == 0:
            salePrice = prices.xpath('//span[contains(@id,"product-price")]//span[2]/text()').extract()
            item['originsaleprice'] = salePrice[0].replace('\xa0','')
            item['originlistprice'] = salePrice[0].replace('\xa0','')
        else:
            item['originsaleprice'] = salePrice[0].replace('\xa0','')
            item['originlistprice'] = listPrice[0].replace('\xa0','')

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//li[@class="product-image"]/img/@src').extract()
        images = []
        for img in img_li:
            img = img
            if img not in images:
                images.append(img)
        return images

_parser = Parser()



class Config(MerchantConfig):
    name = 'current'
    merchant = "CURRENT/ELLIOTT"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num =('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            items = '//div[contains(@class,"item-wrapper")]',
            designer = './/span[@class="designer"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@class="button btn-cart"]', _parser.checkout)),
            ('name', '//div[@class="product-name"]/h1/span/text()'),
            ('designer', ('//h1/text()',_parser.designer)),
            ('images', ('//li[@class="product-image"]/img/@src', _parser.images)),
            ('sku', ('//meta[@itemprop="productId"]/@content', _parser.sku)),
            ('color','//div[@id="product-color-options-container"]//span/text()'),
            ('description', ('//html',_parser.description)), # TODO:
            ('prices', ('//div[@class="price-box"]', _parser.prices)),
            ('sizes', ('//label[@class="label-radio-configurable"]/text()', _parser.sizes)),
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
            c = [
                "https://www.currentelliott.com/women/denim?p=",
                "https://www.currentelliott.com/women?p=",
                "https://www.currentelliott.com/permanent-collection?p=",
                "https://www.currentelliott.com/sale-2?p=",
            ],


        params = dict(
            # TODO:
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),

        )
        


