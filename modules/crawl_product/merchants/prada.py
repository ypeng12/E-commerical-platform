from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        item['tmp'] = json.loads(checkout.extract_first())[0]
        if 'InStock' not in item['tmp']['offers']['availability']:
            return True
        else:
            return False

    def _designer(self, res, item, **kwargs):
        item['designer'] = item['tmp']['brand']['name'].upper()

    def _description(self, desc, item, **kwargs):
        item['description'] = item['tmp']['description']

    def _prices(self, prices, item, **kwargs):
        item["originsaleprice"] = item['tmp']['offers']['price']
        item["originlistprice"] = item['tmp']['offers']['price']

    def _images(self, res, item, **kwargs):
        image_li = []
        for image in item['tmp']['image']:
            if image not in image_li:
                image_li.append(image)
        item["images"] = image_li
        item["cover"] = image_li[0]

    def _sizes(self,res,item,**kwargs):
        size_li = []
        sizes_data = json.loads(res.extract_first())
        for data in sizes_data:
            size_li.append(data['label'])
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        img_li = json.loads(response.extract_first())[0]
        images = []
        for img in img_li['image']:
            if 'http' not in img:
                img = img.replace('//', 'https://')
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

    def _page_num(self, products, **kwargs):
        pages = int(products) // 20,
        return int(pages[0])

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('page=1', 'page=%s'%i)
        return url

_parser = Parser()


class Config(MerchantConfig):
    name = "prada"
    merchant = "Prada"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[contains(@class,"js-total-count")]/@data-total-count', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="productQB__wrapperOut"]',
            designer = './a/@aria-hidden',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//script[@id="jsonldCategoryProductBox"]/text()',_parser.checkout)),
            ('sku', '//div[@id="mainPdpContent"]/@data-product-id'),
            ('name', '//div[@class="info-card-component__basic-info"]/h1[@class="info-card-component__basic-info-name"]/text()'),
            ('designer', ('//html', _parser.designer)),
            ('color', '//button[@class="info-card-component__button-select"]/span[@class="info-card-component__button-title"]/text()'),
            ('description',('//html', _parser.description)),
            ('price', ('//html', _parser.prices)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//div[@id="mainPdpContent"]/@data-sizes', _parser.sizes)),
        ]),
        image=dict(
            method = _parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-description__container"]/div/ul/li/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.prada.com/us/en/women/accessories.html?page=1'
            ],
            b = [
                'https://www.prada.com/us/en/women/bags.html?page=1'  
            ],
            c = [
                'https://www.prada.com/us/en/women/ready_to_wear.html?page=1',
            ],
            s = [
                'https://www.prada.com/us/en/women/shoes.html?page=1'
            ]
        ),
        m = dict(
            a = [
                'https://www.prada.com/us/en/men/accessories.html?page=1'
            ],
            b = [
                'https://www.prada.com/us/en/men/bags.html?page=1'  
            ],
            c = [
                'https://www.prada.com/us/en/men/ready_to_wear.html?page=1',
            ],
            s = [
                'https://www.prada.com/us/en/men/shoes.html?page=1'
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )