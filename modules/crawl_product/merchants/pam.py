from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from urllib.parse import urljoin
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "instock" in checkout.extract_first().lower():
            return False
        else:
            return True

    def _sku(self,res,item,**kwargs):
        data = json.loads(res.extract_first().split('var __st=')[1].rsplit(';',1)[0])
        item['sku'] = data['rid']

    def _description(self, res, item, **kwargs):
        desc_li = []
        for desc in res.extract():
            if desc.strip():
                desc_li.append(desc)
        item['description'] = "\n".join(desc_li)

    def _images(self, res, item, **kwargs):
        images_li = []
        for image in res.extract():
            image = "https:" + image
            if image not in images_li:
                images_li.append(image)
        item['images'] = images_li
        item['cover'] = images_li[0]

    def _prices(self, res, item, **kwargs):
        saleprice = res.xpath('./span[@class="product-price" ]/span/text()').extract_first()
        listprice = res.xpath('./span[@class="was"]/span/text()').extract_first()
        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _sizes(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first().split('var productObj = ')[1].split('// MERGE : Overwrite pa')[0].rsplit(';',1)[0])
        memo = ""
        if "final_sale" in json_data['tags']:
            memo = ':f'
        size_li = []
        for size in json_data['variants']:
            if size['available']:
                size_li.append(size['option2'] + memo)
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[contains(@class,"product-main-image")]/a[@rel="product-images"]/img/@data-zoom-src').extract()
        images_li = []
        for img in images:
            image = "https:" + img
            images_li.appen(image)
        return images_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

    def _page_num(self, data, **kwargs):
        return 5

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

_parser = Parser()

class Config(MerchantConfig):
    name = "pam"
    merchant = "Pam & Gela"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            items = '//div[@class="bc-sf-filter-product-bottom"]',
            designer = './a/text()',
            link = './a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//div[@class="nosto_product"]/span[@class="availability"]/text()',_parser.checkout)),
            ('sku', ('//script[@id="__st"]/text()', _parser.sku)),
            ('name', '//div[@class="product-desction-wrapper"]/div[@id="product-description"]/h1/text()'),
            ('color', '//div[@data-option-name="Color"]/div/h6[@class="current-option"]/text()'),
            ('designer', '//div[@class="nosto_product"]/span[@class="brand"]/text()'),
            ('description', ('//div[@class="nosto_product"]/span[@class="description"]/ul/li/text()', _parser.description)),
            ('images', ('//div[contains(@class,"product-main-image")]/a[@rel="product-images"]/img/@data-zoom-src', _parser.images)),
            ('price', ('//div[@id="product-price--mobile"]', _parser.prices)),
            ('sizes', ('//script[@class="product-json"]/text()', _parser.sizes)),
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
            size_info_path = '//div[@class="size-chart-desc"]/ul/li/text()',
            ),
    )

    list_urls = dict(
        f = dict(
            c = [
                'https://www.pamandgela.com/collections/clothing?page={}',
            ]
        ),

    )

    countries = dict(
        US=dict(
            currency='USD',
        ),
    )