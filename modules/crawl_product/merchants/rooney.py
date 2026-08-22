from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json

class Parser(MerchantParser):
    def _sizes(self,res,item,**kwargs):
        size_text = res.extract()
        sizes = []
        for size in size_text:
            size = size.strip()
            if size and size not in sizes and "Sold Out" not in size:
                sizes.append(size)
        item["originsizes"] = sizes

    def _sku(self,res,item,**kwargs):
        sku = res.extract()[-1]
        results = json.loads(sku)
        images = []
        for image in results["images"]:
            if "https" not in image:
                img = "https:" + image
                images.append(img)
        item["images"] = images
        item["cover"] = "https:" + results["featured_image"]
        item["name"] = results["title"]
        item["designer"] = results["vendor"]
        item["sku"] = results["id"]
        item["originlistprice"] = results["price"]
        item["originsaleprice"] = results["price_max"]
        description = results["description"]
        if description:
            desc = description.split(' data-mce-fragment="1">')[-1].split("Composition")[0]
            item["description"] = desc

    def _color(self,res,item,**kwargs):
        color = res.extract_first()
        item["color"] = color.strip().strip("Color: ")
        
    def _parse_images(self, response, **kwargs):
        images = response.xpath('//script[@type="application/json"]/text()').extract()[-1]
        results = json.loads(images)
        images_li = []
        for image in results["images"]:
            if "https" not in image:
                img = "https:" + image
                images_li.append(img)
        return images_li

_parser = Parser()


class Config(MerchantConfig):
    name = "ronney"
    merchant = "Rooney Shop"

    path = dict(
        product=OrderedDict([
            ('sku', ('//script[@type="application/json"]/text()', _parser.sku)),
            ('color',('//div[@class="product-description rte"]/text()',_parser.color)),
            ('sizes', ('//select[@data-index="option2"]//text()', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),

    )
    countries = dict(
        CA=dict(
            currency='US',
            discurrency = 'CAD',
            currency_sign = 'CAD$'
        ),
        US=dict(
            currency = 'CAD',
            discurrency = 'US',
            currency_sign = '$',
        ),
    )