from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True
        
    def _page_num(self, data, **kwargs):
        page_num = 10
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?p=1', '?p=%s'%i)
        return url

    def _sku(self, res, item, **kwargs):
        sku = res.extract_first().split('Product Number:')[-1].rsplit('_', 1)[0].strip()

        item['sku'] = sku
        item['designer'] = 'JOIE'
          
    def _images(self, scripts, item, **kwargs):
        json_datas = json.loads(scripts.extract_first().split('var afterpay_product =')[-1].split('var afterpay_product_variant')[0].rsplit(';', 1)[0].strip())
        item['tmp'] = json_datas
        images_li = []
        for img in json_datas['images']:
            image = "https:" + img
            if image not in images_li:
                images_li.append(image)
        item['images'] = images_li
        item['cover'] = images_li[0]

    def _sizes(self, scripts, item, **kwargs):
        size_data = item['tmp']
        size_li = []
        for size in size_data['variants']:
            if size['available']:
                size_li.append(size['option2'])
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//div[@class="price__regular"]/span[contains(@class,"price-item--regular")]/text()').extract_first()
        saleprice = prices.xpath('.//div[@class="price__sale"]/span[contains(@class,"price-item--sale")]/text()').extract_first()

        item['originlistprice'] = listprice.strip()
        item['originsaleprice'] = saleprice.strip()

    def _parse_images(self, response, **kwargs):
        images = []
        json_datas = response.xpath('//script[@type="text/javascript"][contains(text(),"afterpay_product")]/text()').extract_first()
        datas = json.loads(json_datas.split('var afterpay_product =')[-1].split('var afterpay_product_variant')[0].rsplit(';', 1)[0].strip())
        for img in datas['images']:
            img = "https:" + img
            if img not in images:
                images.append(img)

        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="toolbar-number"]/text()').extract_first().strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'joie'
    merchant = 'Joie'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="paging-current-page"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-item-info"]',
            designer = './div/a/@data-brand',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@title="Add to Bag"] | //button[@name="add"]/span', _parser.checkout)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('sku', ('//p[contains(@class,"variant-sku")]/text()', _parser.sku)),
            ('description', '//div[contains(@class,"product__description")]/p/text()'),
            ('color', '//variant-radios//input[@name="Color"]/@value'),
            ('images', ('//script[@type="text/javascript"][contains(text(),"afterpay_product")]/text()', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[contains(@class,"price--show-badge")]', _parser.prices))
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
            ),
        )

    list_urls = dict(
        m = dict(
        ),
        f = dict(
            c = [
                'https://www.joie.com/joie?p=1'
            ],
            s = [
                'https://www.joie.com/shoes?p=1'
            ],


        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),
        )

        


