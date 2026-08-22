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

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['name'] = json_data['name'].upper()
        item['designer'] = json_data['brand'].upper()

        item['description'] = json_data['description']

    def _prices(self, res, item, **kwargs):
        saleprice = res.xpath('./span[contains(@class,"on-sale")]/text()').extract_first()
        listprice = res.xpath('.//span[contains(@class,"product__price--compare")]/text()').extract_first()

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _parse_multi_items(self,response,item,**kwargs):
        colors = response.xpath('//div[@id="optionWrapColor"]//div[@class="variant-input"]/@data-value').extract()
        json_data = json.loads(response.xpath('//div[@aria-hidden="true"][contains(@id,"VariantsJson")]/text()').extract_first())
        sku_id = json_data[0]['featured_image']['product_id']
        for color in colors:
            item_color = deepcopy(item)
            item_color['color'] = color
            for data in json_data:
                if color == data['option2']:
                    item_color['sku'] = str(sku_id) + '_' + color.upper()
                    images_li = []
                    if data['featured_image']['src'] not in images_li:
                        images_li.append(data['featured_image']['src'])
                    item_color['images'] = images_li
                    item_color['cover'] = images_li[0]

                    osize = []
                    if data['available']:
                        osize.append(data['option1'])
                    item_color['originsizes'] = osize
                    self.sizes(osize, item_color, **kwargs)
                    yield item_color

    def _parse_images(self,response,**kwargs):
        image_datas = json.loads(response.xpath('//div[@aria-hidden="true"][contains(@id,"VariantsJson")]/text()').extract_first())
        images = []
        for image_data in image_datas:
            if kwargs['sku'].split('_')[-1] == image_data['option2']:
                images.append(image_data['featured_media']['src'])

        return images

    def _parse_num(self,pages,**kwargs):
        # pages = pages/24+1
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _parse_item_url(self,response,**kwargs):
        item_data = response.xpath('//json-adapter/@product-search').extract_first()
        item_data = json.loads(item_data)
        for url_items in item_data['products']:
            yield url_items['url'],'designer'

_parser = Parser()


class Config(MerchantConfig):
    name = "shopsimon"
    merchant = "SHOP SIMON"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
        ),
        product = OrderedDict([
            ('checkout', ('//button[@name="add"]/span[@data-btn-text="Add to bag"]/text()', _parser.checkout)),
            ('name', ('//script[@type="application/ld+json"]/text()', _parser.name)),
            ('prices', ('//div[@class="pdp-price-wrap"]', _parser.prices)),
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
               "https://shoppremiumoutlets.com/pages/jewelry-collection",
               "https://shoppremiumoutlets.com/collections/women?RootCategory=women-accessories&page={}"
            ],
            b = [
                "https://shoppremiumoutlets.com/collections/women?RootCategory=women-handbags&page={}",
            ],
            c = [
                "https://shoppremiumoutlets.com/collections/women?RootCategory=women-clothing&page={}"
            ],
            s = [
                "https://shoppremiumoutlets.com/collections/women?RootCategory=women-shoes&page={}"
            ],
        ),
        m = dict(
            a = [
                "https://shoppremiumoutlets.com/collections/men?RootCategory=men-accessories&page={}"
            ],
            c = [
                "https://shoppremiumoutlets.com/collections/men?RootCategory=men-clothing&page={}"
            ],
            s = [
                "https://shoppremiumoutlets.com/collections/men?RootCategory=men-shoes&page={}"
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
    )