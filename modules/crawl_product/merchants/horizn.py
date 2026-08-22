from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import json


class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        for p in res.extract():
            a = json.loads(p.split(";")[1].split("(")[1].rsplit(")")[0])
            sold_out = a["page"]["soldOut"]
            return sold_out

    def _images(self, res, item, **kwargs):
        image_li = []
        for image in res.extract():
            if image not in image_li:
                image_li.append(image.replace("38", "500"))
        item["images"] = image_li
        item["cover"] = image_li[0]

    def _prices(self, res, item, **kwargs):
        for price in res.extract():
            products = (json.loads(price.split(";")[1].split("(")[1].rsplit(")")[0]))["page"]["products"]
            for product in products:
                if product:
                    item["originsaleprice"] = product["price"]
                    item['originlistprice'] = product["price"]
                else:
                    item["originsaleprice"] = ""
                    item['originlistprice'] = ""

    def _sku(self, res, item, **kwargs):
        item["sku"] = res.extract_first()

    def _color(self, res, item, **kwargs):
        color = res.extract_first()
        colors = re.findall('"contentGroup".*', color)
        a = colors[0].split(":")[1].strip(",")
        item['color'] = a.rsplit(",")[-1][:-1].strip('"').upper()

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract()

    def _designer(self, designer, item, **kwargs):
        item['designer'] = 'HORIZN STUDIOS'

    def _sizes(self, res, item, **kwargs):
        osizes = res.extract()
        osizes_li = []
        for size in osizes:
            osizes_li.append(size)
        real_size = []
        price = re.search(item['originsaleprice'], str(osizes_li))
        for pr in osizes_li:
            if item["originsaleprice"] in pr:
                siz = (osizes_li[osizes_li.index(pr) - 1]).strip(";")
                real_size.append(siz)
        item["originsizes"] = set(real_size)

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="product-gallery__thumbnails"]//img/@src').extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image.replace("38", "500"))
        return images

_parser = Parser()

class Config(MerchantConfig):
    name = "horizn"
    merchant = "Horizn Studios"
    merchant_headers = {'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'}

    path = dict(
        product=OrderedDict([
            ('checkout', ('//script[contains(text(),"window.dataLayer.push({")]/text()', _parser.checkout)),
            ('sku', ('//div[@class="yotpo bottomLine"]/@data-product-id', _parser.sku)),
            ('designer', ('//html', _parser.designer)),
            ('name', '//span[@class="breadcrumbs__current"]/text()'),
            ('color', ('//script[contains(text(),"window.dataLayer.push({")]/text()', _parser.color)),
            ('description',
             ("//div[@class='product-details__row product-details__row--spaced']//li/text()", _parser.description)),
            ('price', ('//script[contains(text(),"window.dataLayer.push({")]/text()', _parser.prices)),
            ('images', ('//div[@class="product-gallery__thumbnails"]//img/@src', _parser.images)),
            ('sizes', ('//span[@class="switch__text-item"]/text()', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),

    )

    countries = dict(
        US=dict(
            language='EN',
            area='US',
            currency='USD',
        ),
        GB=dict(
            currency='GBP',
        ),
        DE=dict(
            currency='EUR',
            duscurrency='GBP'
        ),
    )