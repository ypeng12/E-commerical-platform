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
    def _checkout(self, checkout, item, **kwargs):
        obj = json.loads(checkout.extract()[0])
        
        if obj["available"]:
            item["tmp"]=obj
            return False
        else:
            return True

    def _parse_multi_items(self, response, item, **kwargs):
        variants = item["tmp"]["variants"]
        colors = []
        size = []
        checkset = []
        for v in variants:
            try:
                position = str(v["featured_media"]["position"])
            except:
                position = "1"
            if v["available"]:
                size.append(v["title"])
            if v["option1"] not in checkset:
                checkset.append(v["option1"])
                colors.append(v["option1"]+"_x1"+position+"_x2"+v["sku"])

        for c in colors:
            item_color = deepcopy(item)
            item_color["color"] = c.split("_x1")[0]
            item_color["sku"] = "-".join(c.split("_x2")[-1].split("-")[0:1]) + '_' + item_color["color"]
            position = int(c.split("_x1")[-1].split("_x2")[0])
            sizes = []
            for s in size:
                if item_color["color"] in s:
                    sizes.append(s.split("/")[-1])
            self.sizes(sizes, item_color, **kwargs)
            item_color['images'] = []
            for i in item["tmp"]["images"][position-1:position+3]:
                if "http" not in i:
                    i = "http:" + i
                if i not in item_color['images']:
                    item_color['images'].append(i)
            item_color["cover"] = "https:" + item["tmp"]["images"][position-1] if "https" not in item["tmp"]["images"][position-1] else item["tmp"]["images"][position-1]
            prices= 0
            self.prices(prices, item_color, **kwargs)
            yield item_color

    def _sku(self, sku_data, item, **kwargs):
        sku = item["tmp"]["id"]
        item['sku'] =  sku
        item["name"] = item["tmp"]["title"]
        # item["color"] = item["tmp"]["option1"]


    def _images(self, images, item, **kwargs):
        # imgs = item["tmp"]["featured_image"]["preview_image"]["src"]
        # print images
        images = []
        cover = imgs
        img = imgs
        for x in range(1,3):

            src = img.split(".jpg")[0].split("-")[-1]
            img = img.replace(src,str(int(src)+x))

            if img not in images:
                images.append(img)


        item['images'] = images
        # item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):
        if sizes == []:
            item['originsizes'] = ''
        else:
            item['originsizes'] = sizes
        item["designer"] = "GCDS"

    def _prices(self, prices, item, **kwargs):

        item['originlistprice'] = str(item["tmp"]["price_max"]/100)
        item['originsaleprice'] = str(item["tmp"]["price_min"]/100)


    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//a[@class="product-info-link"]/@href').extract())
        return number

    def _parse_images(self,response,**kwargs):
        images_json = json.loads(response.xpath('//div[@id="product-block"]/@data-product').extract_first())
        image_datas = images_json["images"]
        images = []
        for image_data in image_datas:
            if kwargs['sku'] in image_data['image']['url']:
                images.append(image_data['image']['url'])
        return images



_parser = Parser()



class Config(MerchantConfig):
    name = 'gcds'
    merchant = 'GCDS'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//span[@class="l-search_result-paging-controls-loaded js-paging-controls-loaded"]/text()', _parser.page_num),
            # list_url = _parser.list_url,
            items = '//a[@class="product-info-link"]',
            designer = './div/span/@data-product-brand',
            link = './@href',
            ),
        product = OrderedDict([
        	('checkout', ('//div[@id="product-block"]/@data-product', _parser.checkout)),
            # ('images',('//img[@class="js-producttile_image b-product_image  js-zoomy"]/@src',_parser.images)), 
            # ('color','//span[@class="js_color-description h-hidden"]/text()'),
            # ('sku',('//html',_parser.sku)),
            ('description', ('//meta[@name="description"]/@content',_parser.description)),
            # ('sizes',('//li[@class="b-swatches_size-item emptyswatch"]/a/@title',_parser.sizes)),
            ('prices', ('//div[@class="b-product_container-price"]', _parser.prices)),
            

            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method=_parser.parse_images,
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
                "https://gcds.it/collections/calzini?p=",
                "https://gcds.it/collections/belts?p=",
                "https://gcds.it/collections/hats?p=",
                "https://gcds.it/collections/gadgets?p=",
                "https://gcds.it/collections/masks?p=",
                "https://gcds.it/collections/sunglasses?p=",

            ],
            b = [
                "https://gcds.it/collections/bags?p="
            ],

            c = [
                "https://gcds.it/collections/clothing-m-all?p="
            ],
            s = [
                "https://gcds.it/collections/shoes?p=",
            ],
            e = [
                "https://gcds.it/collections/beauty?p="
            ],


        ),
        f = dict(
            a = [
                "https://gcds.it/collections/jewelry?p=",
                "https://gcds.it/collections/innerwear?p=",
                "https://gcds.it/collections/belts?p=",
                "https://gcds.it/collections/hats?p=",
                "https://gcds.it/collections/gadgets?p=",
                "https://gcds.it/collections/masks?p=",
                "https://gcds.it/collections/sunglasses?p=",
            ],
            b = [
                "https://gcds.it/collections/bags?p=",
            ],
            c = [

                "https://gcds.it/collections/clothing?p=",
            ],
            s = [
                "https://gcds.it/collections/shoes-w-all?p=",
            ],
            e = [
                "https://gcds.it/collections/beauty?p=",
            ],




        params = dict(
            # TODO:

            ),
        ),

        # country_url_base = '/en-us/',
    )

    parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            thousand_sign = ".",
            cookies = {'preferredCountry':'US'},
            

        ),

# ships but cant find the rate

        # CN = dict(
        #     area = "EU",
        #     currency = 'CNY',
        #     thousand_sign = '.',
        #     currency_sign = u'\xa5',
        #     cookies = {'preferredCountry':'CN'},

        # ),
        # KR = dict(
        #     area = "EU",
        #     currency = 'KRW',
        #     discurrency = "EUR",
        #     cookies = {'preferredCountry':'KR'},
        #     currency_sign = u'\u20ac',
        #     thousand_sign = ".",

        # ),
        # SG = dict(
        #     area = "EU",
        #     currency = 'SGD',
        #     discurrency = "EUR",
        #     cookies = {'preferredCountry':'SG'},
        #     currency_sign = u'\u20ac',
        #     thousand_sign = ".",
        # ),
        # HK = dict(
        #     area = "EU",
        #     currency = 'HKD',
        #     cookies = {'preferredCountry':'HK'},
        #     currency_sign = u'HK$',
        #     thousand_sign = ".",
        # ),
        # GB = dict(
        #     area = "EU",
        #     currency = 'GBP',
        #     cookies = {'preferredCountry':'GB'},
        #     currency_sign = u'\xa3',
        #     thousand_sign = ".",

            
        # ),
        # RU = dict(
        #     area = "EU",
        #     currency = 'RUB',
        #     discurrency = "EUR",
        #     cookies = {'preferredCountry':'RU'},
        #     currency_sign = u'\u20ac',
        #     thousand_sign = ".",
        # ),
        # CA = dict(
        #     area = "EU",
        #     currency = 'CAD',
        #     discurrency = "EUR",
        #     cookies = {'preferredCountry':'CA'},
        #     currency_sign = u'\u20ac',
        #     thousand_sign = ".",
        # ),
        # AU = dict(
        #     area = "EU",
        #     currency = 'AUD',
        #     discurrency = "EUR",
        #     cookies = {'preferredCountry':'AU'},
        #     currency_sign = u'\u20ac',
        #     thousand_sign = ".",
        # ),
        # DE = dict(
        #     area = "EU",
        #     currency = 'EUR',
        #     cookies = {'preferredCountry':'DE'},
        #     currency_sign = u'\u20ac',
        #     thousand_sign = ".",
        # ),
        # NO = dict(

        #     currency = 'NOK',
        #     area = "EU",
        #     cookies = {'preferredCountry':'NO'},
        #     currency_sign = u'\u20ac',
        #     thousand_sign = ".",
        # ),    
        )

        


