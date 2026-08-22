from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        sold_out = res.extract_first()
        if "add to cart" in sold_out.lower():
            return False
        else:
            return True

    def _name(self,res,item,**kwargs):
        data = json.loads(res.extract_first())
        item['name'] = data['@graph'][1]['name']
        item['description'] = data['@graph'][1]['description']
        item['designer'] = 'LATTELIER'
        item['tmp'] = data['@graph'][1]['description']

    def _parse_multi_items(self,response,item,**kwargs):
        colors = response.xpath('//select[@data-attribute_name="attribute_pa_color"]/option[not(contains(text(),"Choose"))]/text()').extract()
        sizes_data = json.loads(response.xpath('//form[contains(@class,"variations_form")]/@data-product_variations').extract_first())
        for color_data in colors:
            item_color = deepcopy(item)
            item_color['color'] = color_data.upper()
            sizes_li = []
            images_li = []
            for data in sizes_data:
                if color_data.lower().replace('/','-') == data['attributes']['attribute_pa_color']:
                    if data['is_in_stock']:
                        osize = data['attributes']['attribute_pa_size'].upper()
                        sizes_li.append(osize)
                        item_color['sku'] = data['sku'].split(osize)[0] if data['sku'].endswith(osize) else ''
                        images_data = data['variation_gallery_images']
                        for image in images_data: images_li.append(image['url'])

            item_color['images'] = list(set(images_li))
            item_color['cover'] = images_li[0]
            item_color['originsizes'] = sizes_li
            listprices = sizes_data[0]['display_regular_price']
            saleprices = sizes_data[0]['display_price']
            item_color['originsaleprice'] = str(listprices)
            item_color['originlistprice'] = str(saleprices)
            self.sizes(osize, item_color, **kwargs)
            self.prices(listprices, item_color, **kwargs)
            yield item_color

    def _parse_num(self,pages,**kwargs):
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('&sz=1', '&sz=%s'%i)
        return url

    def _parse_item_url(self,response,**kwargs):
        item_data = response.xpath('//json-adapter/@product-search').extract_first()
        item_data = json.loads(item_data)
        for url_items in item_data['products']:
            yield url_items['url'],'designer'

_parser = Parser()


class Config(MerchantConfig):
    name = "lattelier"
    merchant = "Lattelier"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
        ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"add_to_cart")]/text()', _parser.checkout)),
            ('name', ('//script[@type="application/ld+json"][contains(text(),"offers")]/text()', _parser.name)),
            ]),
        image = dict(
            method = _parser.parse_images,
        ),
        look = dict(
        ),
        swatch = dict(
        ),        
    )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
               "https://lattelierstore.com/product-category/accessories/jewelry/"
                ],
            b = [
                "https://lattelierstore.com/product-category/accessories/bags/",
                ],
            c = [
                "https://lattelierstore.com/product-category/clothing/"
            ],
            s = [
                "https://lattelierstore.com/product-category/accessories/shoes/"
            ],
        ),
        
        m = dict(
            a = [
                "https://lattelierstore.com/product-category/accessories-men/shoes-men/"
            ],
            c = [
                "https://lattelierstore.com/product-category/clothing-men/"
            ],
        ),

        k = dict(
            a = [
                "https://lattelierstore.com/product-category/gifts/",
                ],
            c = [
               "https://lattelierstore.com/product-category/clothing-kid/"
                ],
        ),
    )

    countries = dict(
        US=dict(
            language = 'EN',
            currency = 'USD',
            country_url = '/us/',
        ),
        GB=dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/en-gb/',
        )
    )