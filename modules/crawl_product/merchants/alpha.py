from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        if res.extract_first():
            return False
        else:
            return True

    def _name(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first())
        item['name'] = json_data['name'].upper()
        item['designer'] = json_data['brand']['name'].upper()

        description = json_data['description']

    def _prices(self, res, item, **kwargs):
        originsaleprice = res.xpath('./div/span[contains(@class,"price-item--regular")]/text()').extract_first()
        originlistprice = res.xpath('./div[@class="price__sale"]/span/s/text()').extract_first()

        item['originsaleprice'] = originsaleprice
        item['originlistprice'] = originlistprice if originlistprice.strip() else originsaleprice

    def _parse_multi_items(self,response,item,**kwargs):
        color_datas = response.xpath('//div[@class="product-v2--color-swatch"]/p/span/text()').extract()
        json_data = json.loads(response.xpath('//script[@type="application/json"][contains(@id,"ProductJson")]/text()').extract_first())
        for i in json_data['tags']:
            if "style" in i:
                sku_id = i.split('style: ')[-1]
            else:
                sku_id = response.url.split('/products/')[-1].split('-')[0].upper()
                if len(sku_id) != 10:
                    return False
        for color in color_datas:
            item_color = deepcopy(item)
            item_color['color'] = color
            item_color['sku'] = sku_id + '_' + color.upper()
            sizes_li = []
            img_li = []
            for variant in json_data['variants']:
                if variant['available'] and color.upper() == variant['option1'].upper():
                    sizes_li.append(variant['option2'])
                    if variant['featured_image']['src']: 
                        img_li.append(variant['featured_image']['src'])

            item_color['images'] = img_li
            item_color['cover'] = img_li[0]

            item_color['originsizes'] = sizes_li
            self.sizes(sizes_li, item_color, **kwargs)
            yield item_color

    def _parse_images(self,response,**kwargs):
        color_datas = response.xpath('//div[@class="product-v2--color-swatch"]/p/span/text()').extract()
        json_data = json.loads(response.xpath('//script[@type="application/json"][contains(@id,"ProductJson")]/text()').extract_first())
        for color in color_datas:
            img_li = []
            for variant in json_data['variants']:
                if color.upper() == variant['option1'].upper():
                    if variant['featured_image']['src']: 
                        img_li.append(variant['featured_image']['src'])

            return img_li


_parser = Parser()


class Config(MerchantConfig):
    name = "alpha"
    merchant = "Alpha Industries"

    path = dict(
        base = dict(
        ),
        plist = dict(
            items = '//div[contains(@class,"card-wrapper-collections")]/div',
            designer = './a/@aria-label',
            link = './a/@href',
        ),
        product = OrderedDict([
            ('checkout', ('//div[@id="btn-add_to_bag"]//button[@id="AddToCart-product-template"]', _parser.checkout)),
            ('name', ('//script[@type="application/ld+json"]/text()', _parser.name)),
            ('prices', ('//div[@class="price__container"]', _parser.prices)),
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
               "https://www.alphaindustries.com/collections/accessories-hats",
               "https://www.alphaindustries.com/collections/keychains-lanyard-wallets"
                ],
            b = [
                "https://www.alphaindustries.com/collections/accessories-bags",
                ],
            c = [
                "https://www.alphaindustries.com/collections/womens-shop-all",
                "https://www.alphaindustries.com/collections/socks"
            ],
            s = [
                "https://www.ganni.com/us/shoes/?start=0&sz=1?"
            ],
        ),
        m = dict(
            a = [
                "https://www.alphaindustries.com/collections/belts"
            ],
            c = [
                "https://www.alphaindustries.com/collections/mens-shop-all-outerwear"
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US=dict(
            language = 'EN',
            currency = 'USD',
        ),
        GB=dict(
            area = 'GB',
            currency = 'GBP',
        )
    )