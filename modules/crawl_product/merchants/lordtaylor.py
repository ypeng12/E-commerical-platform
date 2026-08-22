from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        data = json.loads(res.extract_first().strip())
        item['tmp'] = data
        if "InStock" in data['offers']['availability']:
            return False
        else:
            return True

    def _name(self,res,item,**kwargs):
        item['name'] = item['tmp']['name']
        item['designer'] = item['tmp']['brand']

        description = item['tmp']['description'].strip()

    def _prices(self, res, item, **kwargs):
        originsaleprice = res.xpath('.//span[contains(@class,"product__price on-sale")]/text() |.//span[@class="list_price"]/text()').extract_first()
        originlistprice = res.xpath('.//span[contains(@class,"product__price--compare")]/text() | .//div[@class="nosto_product"]/span[@class="price"]/text()').extract_first()
        item['originsaleprice'] = originsaleprice if originsaleprice else originlistprice
        item['originlistprice'] = originlistprice if originlistprice else originsaleprice

    def _parse_multi_items(self,response,item,**kwargs):
        color_num = json.loads(response.xpath('//script[@type="application/json"][contains(text(),"variants")]/text()').extract_first())
        json_color = color_num['options']
        color_datas = [col['values'] for col in json_color if col['name'] == 'Color'][0]
        if len(color_datas) == 1:
            item['sku'] = str(color_num['id']) + '_' + color_datas[0].upper().replace(' &  ',',')
            item['color'] = color_datas[0]
            item['images'] = ["https:" + images for images in color_num['images']][:4]
            item['cover'] = "https:" + color_num['featured_image']
            originsizes = []
            for size in color_num['variants']:
                if size['available']:
                    if size['option2']:
                        originsizes.append(size['option2'])
                    else:
                        originsizes.append('IT')
            item['originsizes'] = originsizes
            self.sizes(item['originsizes'], item, **kwargs)
            yield item
        else:
            for color_data in color_datas:
                sku = color_num['id']
                item_color = deepcopy(item)
                item_color['color'] = color_data
                item_color['sku'] = str(sku) + '_' + color_data.upper()
                image_li = []
                osize = []
                for data in color_num['variants']:
                    option = data['option1'] + "~~" + data['option2']
                    if data['available'] and color_data in option.split("~~"):
                        image_li.append(data['featured_image']['src'])
                        if 'preview_image' in data['featured_media'].keys():
                            image_li.append(data['featured_media']['preview_image']['src'])
                        osize.append(data['option2'])
                images = []
                for image in image_li:
                    if image not in images:
                        images.append(image)
                item_color['images'] = images
                if images:
                    item_color['cover'] = images[0]
                item_color['originsizes'] = osize
                self.sizes(osize, item_color, **kwargs)
                yield item_color

    def _parse_images(self,response,**kwargs):
        color_num = json.loads(response.xpath('//script[@type="application/json"][contains(text(),"variants")]/text()').extract_first())
        json_color = color_num['options']
        color_datas = [col['values'] for col in json_color if col['name'] == 'Color'][0]
        if len(color_datas) == 1:
            images = ["https:" + images for images in color_num['images']][:4]
            return images
        else:
            for color_data in color_datas:
                image_li = []
                for data in color_num['variants']:
                    option = data['option1'] + "~~" + data['option2']
                    if color_data in option.split("~~"):
                        try:
                            image_li.append(data['featured_image']['src'])
                            image_li.append(data['featured_media']['preview_image']['src'])
                        except:
                            image_li.append(data['featured_image']['src'])
                images = []
                for image in image_li:
                    if image not in images:
                        images.append(image)
                return images

    def _parse_item_url(self,response,**kwargs):
        item_datas = response.xpath('//html').extract_first()
        item_data = item_datas.split('ElevarGtmSuite.handlers.cartReconcile(cartData);')[1].split('items: [')[1].split(',]')[0]
        for url_items in item_data['products']:
            yield url_items,'designer'

_parser = Parser()


class Config(MerchantConfig):
    name = "lordtaylor"
    merchant = "Lord & Taylor"

    path = dict(
        base = dict(
        ),
        plist = dict(
            parse_item_url = _parser.parse_item_url,
        ),
        product = OrderedDict([
            ('checkout', ('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('name', ('//html', _parser.name)),
            ('prices', ('//html', _parser.prices)),
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
               "https://lordandtaylor.com/collections/all-jewelry"
                ],
            c = [
                "https://lordandtaylor.com/collections/womens-dresses"
            ],
            s = [
               "https://lordandtaylor.com/collections/womens-shoes"
            ],
        ),
        m = dict(
            a = [
                "https://lordandtaylor.com/collections/mens-accessories"
            ],
            c = [
                "https://lordandtaylor.com/collections/all-mens"
            ],
            s = [
               "https://lordandtaylor.com/collections/all-shoes"
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
        )
    )