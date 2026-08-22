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
        sku = sku_data.extract_first()
        item['sku'] = sku if sku.isdigit() else ''
        
    def _description(self, description, item, **kwargs):
        item['description'] = description.extract_first().replace('&nbsp;','').strip()

    def _sizes(self, sizes, item, **kwargs):
        orisizes = sizes.extract()
        osizes = []
        for osize in orisizes:
            if osize.strip():
                osizes.append(osize.strip())
        item['originsizes'] = osizes
        
    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('//del[@class="price__original"]/text()').extract_first()
        saleprice = prices.xpath('//span[@class="price__sales"]/text()').extract_first()
        item['originlistprice'] = listprice.strip()
        item['originsaleprice'] = saleprice.strip()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if 'http' not in img and '/images/' in img:
                image = 'https://www.nakedcph.com' + img
                images.append(image)
        item['images'] = images
        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-images"]//a/@href').extract()
        images = []
        for img in imgs:
            if 'http' not in img and '/images/' in img:
                image = 'https://www.nakedcph.com' + img
                images.append(image)

        return images
        

_parser = Parser()



class Config(MerchantConfig):
    name = 'naked'
    merchant = 'Naked'
    # url_split = False
    merchant_headers = {
        'User-Agent':'ModeSensNaked20201106',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="search-results-nav__info"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(text(),"Add to cart")]', _parser.checkout)),
            ('sku',('//meta[@itemprop="productID"]/@content',_parser.sku)),
            ('name', '//meta[@itemprop="name"]/@content'),
            ('designer', '//span[@class="product-property"]/a/text()'),
            ('color','//span[@class="product-property product-property-color"]/text()'),
            ('description', ('//meta[@itemprop="description"]/@content',_parser.description)),
            ('prices', ('//div[@class="remind-me-product-content"]', _parser.prices)),
            ('sizes',('//div[@class="dropdown-menu dropdown-select"]/a[not(contains(@class,"disabled"))]/text()',_parser.sizes)),
            ('images',('//div[@class="product-images"]//a/@href',_parser.images)), 
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            )
        )

    list_urls = dict(
        f = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ]
        )
    )


    countries = dict(
        US = dict(
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            )
        )

        


