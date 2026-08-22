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
        url = response_url.split('/page/')[0] + '/page/%s'%(i)
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
            if "1_" in img:
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        # if "Color:" in item['description']:
        #     item['color'] = item['description'].split("Color:")[-1].split()


    def _sku(self, sku_data, item, **kwargs):
        for sku in sku_data:
            if sku.xpath('./strong[contains(text(),"Product ID:")]'):
                item['sku'] = sku.xpath('./text()').extract_first().strip() +"_" +item["color"]
        item["color"] = item["color"].upper()
        item["designer"] = "Girlfriend Collective"
        item['designer'] = item['designer'].upper()
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract_first()
        json1 = (sizes.split("window.bvaccel = {")[-1].split("productOptionsWithValues")[0]).strip() + 'testing1'
        obj = json.loads(json1.split('handle: "')[-1].split("product:")[-1].split(",testing1")[0])
        # print obj["variants"]
        item['originsizes'] = []
        item['name'] = obj['title']
        item['tmp'] = obj
        for size in obj["variants"]:
            if size["available"]:
                item['originsizes'].append(size["title"].split('/')[-1])

        item['sku'] = obj['id']
        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = str(int(item['tmp']['price_max'])/100)
            item['originsaleprice'] = str(int(item['tmp']['price_min'])/100)
        except:

            item['originsaleprice'] = ""
            item['originlistprice'] =""

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-images__large-image-container "]/a/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images


    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@class="sub-collection__products"]//div[@class="title"]/a/@href').extract())
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'girlfriend'
    merchant = 'Girlfriend Collective'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//ul[@class="page-numbers"]//li[last()-1]//text()',_parser.page_num),
            # list_url = _parser.list_url,
            items = '//div[@class="sub-collection__products"]',
            designer = './/a[@class="tc-product-detail__brand"]/text()',
            link = './/div[@class="title"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="buynowcta"]', _parser.checkout)),
            ('name','//meta[property="og:title"]//@content'),
            ('images',('//div[@class="product-images__large-image-container "]/a/@href',_parser.images)),
            ('color','//div[@class="product-swatch-wrap active enabled"]//@data-color-text'), 
            ('sku',('//div[@class="product-single__description rte"]/p',_parser.sku)),
            ('description', ('//div[@class="product-details__details-content "]/p//text()',_parser.description)),
            ('sizes',('//script[@data-shop-api]/text()',_parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            

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
            # checknum_path = '//div[@class="sub-collection__products"]//div[@class="title"]/a/@href'
            ),
        )

    list_urls = dict(
        m = dict(


        ),
        f = dict(


            c = [
                "https://www.girlfriend.com/collections?view=two-col&i=",
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
            ),

        

        )

        


