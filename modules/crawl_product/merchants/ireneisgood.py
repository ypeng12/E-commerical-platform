from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first())
        item['sku'] = json_data['id']
        item['tmp'] = json_data

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['title']
        item['designer'] = 'IRENEISGOOD'
        description = item['tmp']['description']
        item['description'] = (etree.HTML(description)).xpath('//text()')
        item['color'] = item['tmp']['tags'][0].upper()

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in item['tmp']['images']:
            if "https" not in image:
                image_li.append("https:" + image)
        item["images"] = image_li
        item['cover'] = "https:" + item['tmp']['featured_image']

    def _prices(self, prices, item, **kwargs):
        listprice = str(item['tmp']['compare_at_price'])[:-2] + '.' + str(item['tmp']['compare_at_price'])[-2:]
        saleprice = str(item['tmp']['price'])[:-2] + '.' + str(item['tmp']['price'])[-2:]
        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _sizes(self,res,item,**kwargs):
        sizes = item['tmp']['variants']
        sizes_li = []
        for size in sizes:
            if size['available']:
                sizes_li.append(size['option1'])
        item["originsizes"] = sizes_li

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath("//script[@id="ProductJson-product-template"]/text()").extract_first())
        image_li = []
        for image in data['images']:
            if "https:" not in image:
                image_li.append("https:" + image)
        return images_li

    def _page_num(self, data, **kwargs):
        page_num = data.split('of')[1]
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "ireneisgood"
    merchant = "IRENEISGOOD"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="pagination__text"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="grid-view-item product-card"]',
            designer = './a/span/text()',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[@aria-label="Add to cart"]/span',_parser.checkout)),
            ('sku', ('//script[@id="ProductJson-product-template"]/text()', _parser.sku)),
            ('name', ('//html', _parser.name)),
            ('images', ('//html', _parser.images)),
            ('price', ('//html', _parser.prices)),
            ('sizes', ('//html', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="care"]/div[@class="accordion-body"]/p/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.ireneisgood.com/collections/accessories/Accessories?page={}'
            ],
            c = [
                'https://www.ireneisgood.com/collections/outerwear?page={}',
                'https://www.ireneisgood.com/collections/knitwear?page={}',
                'https://www.ireneisgood.com/collections/tops?page={}',
                'https://www.ireneisgood.com/collections/bottoms?page={}',
            ],
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',  
            cookies= {
            'cart_currency':'USD',
            } 
        ),
        GB=dict(
            currency='GBP',  
            cookies= {
            'cart_currency':'GBP',
            } 
        ),
        EU=dict(
            currency='EUR',  
            cookies= {
            'cart_currency':'EUR',
            } 
        ),
    )