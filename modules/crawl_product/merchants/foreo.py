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
    def _parse_item_url(self, response, **kwargs):
        ajax_script = ''
        scripts = response.xpath('//script/text()').extract()
        for script in scripts:
            if 'collection_id' in script:
                ajax_script = script
                break
        ajax_dict = json.loads(ajax_script)
        ajax_url = 'https://www.foreo.com' + ajax_dict['foreo']['collection_id']        
        res = requests.get(ajax_url)
        prd_list = json.loads(res.text)
        for prd in prd_list:
            for variation in prd['variations']:
                yield variation['url'], 'FOREO'

    def _sku(self, data, item, **kwargs):
        color = data.xpath('.//div[@class="ecommerce__selected-variation"][1]/p/b/text()').extract_first()
        item['color'] = color.upper() if color else ''
        if not item['color']:
            item['sku'] = item['url'].split('=')[-1]
        else:
            item['sku'] = item['url'].split('=')[-1] + '_' + item['color']
    
    def _designer(self, data, item, **kwargs):
        item['designer'] = 'FOREO'
          
    def _images(self, images, item, **kwargs):        
        color_str = item['color'].split()[0] if item['color'] else ''        
        color_str2 = item['color'].split()[1] if len(item['color'].split())>1 else 'NOT_STR2'
        img_li = images.extract()
        images = []
        for img in img_li:
            img = img
            if img not in images and (color_str in img.upper() or color_str2 in img.upper()):
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originsaleprice'] = prices.xpath('.//div[@class="price__amount"]/text()').extract()[0]
            item['originlistprice'] = item['originsaleprice']            
        except:
            item['originsaleprice'] = prices.xpath('.//div[@class="price__amount price__amount--new"]/text()').extract_first()
            item['originlistprice'] = prices.xpath('.//div[@class="price__amount price__amount--old"]/text()').extract_first()


_parser = Parser()



class Config(MerchantConfig):
    name = 'foreo'
    merchant = "FOREO"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            # items = '//ul[@class="nav__sublist"]/li',
            # designer = './/span[@class="designer"]/text()',
            # link = './a/@href',
            ),
        product = OrderedDict([
            ('name', '//h1[@class="ecommerce__heading"]/div/text()'),
            ('designer', ('//h1/text()',_parser.designer)),            
            ('sku', ('//html', _parser.sku)),
            ('images', ('//div[@class="ecommerce__images"][1]/picture/img/@src', _parser.images)),
            # ('color','//span[@class="colorHEX"]/@title'),
            ('description', ('//div[@class="ecommerce__text"]/div//text()',_parser.description)), # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="price"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[contains(@class,"HTMLListColorSelector")]//ul/li/@data-ytos-color-model',
            
            ),
        image = dict(
            image_path = '//picture[@class="ecommerce__picture"]/img/@src',
            ),
        size_info = dict(
            ),
        )
    # parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        m = dict(
            e = [
                "https://www.foreo.com/shop/men/devices?p="
            ]
        ),
        f = dict(
            e = [
                'https://www.foreo.com/shop/skincare/devices?p=',
                'https://www.foreo.com/shop/oral-care/devices?p=',
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
        


