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
        if checkout:
            return False
        else:
            return True

    def _parse_multi_items(self, response, item, **kwargs):
        item['originsaleprice'] = response.xpath('//div[@class="css-utbdeb"]/text()').extract_first()
        item['originlistprice'] = response.xpath('//div[@class="css-utbdeb"]/text()').extract_first()
        item['color'] = ''
        item['designer'] = "66 NORTH"
        json1 = response.xpath('//script[@id="__NEXT_DATA__"]/text()').extract_first()
        obj = json.loads(json1)
        products = obj["props"]["pageProps"]["productPage"]["product"]
        variants = products['variants']
        allVarients = []
        colorCode_b = []
        colors_b = []
        for v in variants:
            try:
                colors_b.append(v['colorName']['en'])
            except:
                colors_b.append(v['colorTerm']['key'])
            colorCode_b.append(v['colorCode'])
            for c in v["availability"]["channels"]:
                if v["availability"]["channels"][c]["isOnStock"] and v["sku"] not in allVarients:
                    allVarients.append(v["sku"])

        colorCodeindex = []
        colorsindex = []
        colorcode_tup = zip(colors_b,colorCode_b)
        for col_tup in set(colorcode_tup):
            colorsindex.append(col_tup[0])
            colorCodeindex.append(col_tup[1])

        for index in range(len(colorsindex)):
            color = colorsindex[index]
            itm = deepcopy(item)
            itm["color"] = color.split("--")[0].upper()
            colorCode = colorCodeindex[index]
            size_li = []
            for aV in allVarients:
                if colorCode in aV:
                    sizes = aV.split('-')[-1]
                    size_li.append(sizes)
            itm["images"] = []
            for v in variants:
                if colorCode in str(v["sku"]):
                    itm["sku"] = '-'.join(str(v["sku"]).split('-')[0:-1])
                    imgs = v['images']
                    for i in imgs:
                        if i["url"] not in itm["images"]:
                            itm["images"].append(i["url"])
                    
            itm["cover"] = itm["images"][0]
            self.sizes(size_li, itm)
            yield itm
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        if item['originsizes'] == []:
            item['originsizes'] = ""

    def _parse_images(self, response, **kwargs):
        json1 = response.xpath('//script[@id="__NEXT_DATA__"]/text()').extract_first()
        obj = json.loads(json1)
        products = obj["props"]["pageProps"]["productPage"]["product"]
        variants = products['variants']
        images = []
        for v in variants:
            if kwargs['sku'] in str(v["sku"]):
                imgs = v['images']
                for i in imgs:
                    if i["url"] not in images:
                        images.append(i["url"])
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = '66north'
    merchant = '66 North'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="css-chz01h"]',
            designer = './/div[@class="grid-product__meta"]/div[@class="grid-product__vendor"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('name','//h5[@class="css-1jhqey8"]/text()'),
            ('description', ('//div[@class="css-1av4dem"]//text()',_parser.description)),
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
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        m = dict(
            a = [
                "https://www.66north.com/us/men-accessories?i="
            ],
            c = [
                "https://www.66north.com/us/men-jackets-and-coats?i=",
                "https://www.66north.com/us/men-tops-and-vests?i=",
                "https://www.66north.com/us/men-bottoms?i=",
            ],

        ),
        f = dict(
            a = [
                "https://www.66north.com/us/women-accessories?i=",
                ],
            c = [
                "https://www.66north.com/us/women-jackets-and-coats?i=",
                "https://www.66north.com/us/women-tops-and-vests?i=",
                "https://www.66north.com/us/women-bottoms?i="
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
            country_url = '.com/',

            ),

        )

        


