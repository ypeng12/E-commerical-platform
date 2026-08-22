from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from copy import deepcopy
from lxml import etree
import requests
import json
import re

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):        
        if checkout:
            return False
        else:
            return True
        
    def _page_num(self, data, **kwargs):
        page_num = 20
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + str(i)
        return url

    def _designer(self, designer_data, item, **kwargs):
        item['designer'] = 'ROBERT GRAHAM'

    def _parse_multi_items(self, response, item, **kwargs):
        colors = response.xpath('//li[@class="HorizontalList__Item"]/label/span/text()').extract()
        colors = set(colors)

        scripts = response.xpath('//script/text()').extract()
        prd_script = ''
        for script in scripts:
            if '"product"' in script and '"options"' in script:
                prd_script = script
                break
        prd_dict = json.loads(prd_script)['product']      
        
        desc = prd_dict['description']
        details = etree.HTML(desc).xpath('//text()')
        desc_li = []              
        for desc in details:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.strip()
        item['name'] = prd_dict['title']

        item['originlistprice'] = str(int(prd_dict['compare_at_price']) / 100) if prd_dict['compare_at_price'] else prd_dict['compare_at_price']
        item['originsaleprice'] = str(int(prd_dict['price']) / 100) if prd_dict['price'] else prd_dict['price']
        self.prices(prd_dict, item, **kwargs)

        offers = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())[0]['offers']

        skus = []

        for color in colors:
            item_color = deepcopy(item)
            item_color['sku'] = str(prd_dict['id']) + '_' + color            
            skus.append(item_color['sku'])
            item_color['color'] = color

            osizes = []
            images = []
            for offer in offers:
                if 'InStock' in offer['availability'] and color in offer['name']:
                    osizes.append(offer['name'].split('/')[-1].strip())
            item_color['originsizes'] = osizes
            self.sizes(osizes, item_color, **kwargs)

            for size in prd_dict['variants']:
                if color in size['title'] and size['featured_image']['src'] not in images:
                    images.append(size['featured_image']['src'])

            item_color['cover'] = images[0]
            item_color['images'] = images

            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _parse_images(self, response, **kwargs):
        scripts = response.xpath('//script/text()').extract()
        prd_script = ''
        for script in scripts:
            if '"product"' in script and '"options"' in script:
                prd_script = script
                break
        prd_dict = json.loads(prd_script)['product'] 

        images = []

        color = kwargs['sku'].split('_')[-1].upper()
        for img in prd_dict['variants']:
            if color in img['title'] and img['featured_image']['src'] not in images:
                images.append(img['featured_image']['src'])

        return images 

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('approx' in info or ' x ' in info.lower() or '"' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = 'robertgraham'
    merchant = "Robert Graham"
    parse_multi_items = _parser.parse_multi_items

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pages"]/ol/li/a/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './div/a/@data-brand',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@class="ProductForm__AddToCart Button Button--primary Button--full"]', _parser.checkout)),
            ('designer', ('//html', _parser.designer)),
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
            size_info_path = '//ul[@class="product-details"]/li/span/text()',            
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'http://www.robertgraham.us/men/accessories/sunglasses.html?p=',
                'http://www.robertgraham.us/men/accessories/belts.html?p=',
                'http://www.robertgraham.us/men/accessories/hats-scarves.html?p=',
                'http://www.robertgraham.us/men/accessories/ties-pocket-squares.html?p=',
            ],
            b = [
                "http://www.robertgraham.us/men/accessories/bags-wallets.html?p="
            ],
            c = [
                "http://www.robertgraham.us/men/accessories/underwear-loungewear.html?p=",
                "http://www.robertgraham.us/men/the-formal-shop.html?p=",
                "http://www.robertgraham.us/men/dress-shirts.html?p=",
                "http://www.robertgraham.us/men/sweaters-hoodies.html?p=",
                "http://www.robertgraham.us/men/shorts-swim.html?p=",
                "http://www.robertgraham.us/men/jeans-pants.html?p=",
                "http://www.robertgraham.us/men/sport-coats-vests.html?p=",
                "http://www.robertgraham.us/men/polos-tees.html?p=",
                "http://www.robertgraham.us/men/short-sleeve-shirts.html?p=",
                "http://www.robertgraham.us/men/sport-shirts.html?p=",
                "http://www.robertgraham.us/men/accessories/socks.html?p=",
            ],
            s = [
                "http://www.robertgraham.us/men/accessories/shoes.html?p="
            ],
        ),
        f = dict(
            a = [
                'http://www.robertgraham.us/women/accessories.html?p=',
            ],
            c = [
                'http://www.robertgraham.us/women/tops.html?p=',
                'http://www.robertgraham.us/women/jackets.html?p=',
                'http://www.robertgraham.us/women/dresses.html?p=',
                'http://www.robertgraham.us/women/pants.html?p=',
            ],

        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
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
        RU = dict(
            currency = 'RUB',
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
    )

        


