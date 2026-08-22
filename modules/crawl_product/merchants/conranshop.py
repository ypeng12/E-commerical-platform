from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first().split('window.ometria.raw_data = ')[1].rsplit(';',1)[0])
        item['tmp'] = json_data
        if not json_data['data']['in_stock']:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        data = item['tmp']
        item['sku'] = data['data']['sku']

    def _name(self, res, item, **kwargs):
        data = json.loads(res.extract_first().strip())
        item['name'] = data['name']

        description = data['description']
        html = etree.HTML(description)
        descs = html.xpath('//text()')
        desc_li = []
        for desc in descs:
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)
        item['color'] = ''

    def _designer(self, res, item, **kwargs):
        json_datas = json.loads(res.xpath('.//script[@type="application/ld+json"][contains(text(),"brand")]/text()').extract_first())
        designer_name = res.xpath('.//span[@class="designer"]/text()').extract_first()
        if 'brand' in json_datas.keys():
            item['designer'] = json_datas['brand']
        else:
            item['designer'] = designer_name

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in images.extract():
            if image not in image_li:
                image_li.append(image)
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _prices(self, res, item, **kwargs):
        data = item['tmp']
        listprice = str(round(data['data']['price'],2))
        if 'special_price' in data['data'].keys():
            saleprice = str(round(data['data']['special_price'],2))
        else:
            saleprice = listprice

        item["originsaleprice"] = saleprice if saleprice else listprice
        item["originlistprice"] = listprice

    def _sizes(self,res,item,**kwargs):
        item['originsizes'] = ['IT']

    def _page_num(self, data, **kwargs):
        pages = int(data) / 60 + 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        return response_url + str(i)

_parser = Parser()


class Config(MerchantConfig):
    name = "conranshop"
    merchant = "The Conran Shop"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="toolbar-number"][3]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-item-info"]',
            designer = './a/span/span/img/@alt',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//script[contains(text(),"window.ometria = window.ometria")]/text()',_parser.checkout)),
            ('sku', ('//script[contains(text(),"window.ometria = window.ometria")]/text()', _parser.sku)),
            ('name', ('//script[@type="application/ld+json"][contains(text(),"brand")]/text()', _parser.name)),
            ('designer', ('//html', _parser.designer)),
            ('price', ('//html', _parser.prices)),
            ('images', ('//span[@class="alternate_image_urls"]/span/text()', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),

        ]),
        image=dict(
            image_path = '//span[@class="alternate_image_urls"]/span/text()'
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
        ),
    )

    list_urls = dict(
        u = dict(
            h = [
                'https://www.conranshop.co.uk/furniture.html/?page',
                'https://www.conranshop.co.uk/lighting.html/?page',
                'https://www.conranshop.co.uk/kitchen-and-dining.html/?page',
                'https://www.conranshop.co.uk/textiles.html/?page',
                'https://www.conranshop.co.uk/home-accessories.html/?page',
                'https://www.conranshop.co.uk/gifts.html/?page',
                'https://www.conranshop.co.uk/technology.html/?page',
            ],
            e = [
                'https://www.conranshop.co.uk/fashion-and-beauty.html/?page'
            ]
        ),
    )

    countries = dict(
        GB=dict(
            currency='GBP',       
        ),
    )