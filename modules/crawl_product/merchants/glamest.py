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

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].split(':')[-1].strip().upper()

    def _designer(self, data, item, **kwargs):
        item['designer'] = data.extract_first().upper()

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            image = 'https:' + img
            if image in images:
                continue
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.extract()
        item['originsizes'] = []
        if len(sizes) != 0:
            for size in sizes:
                size = size.split('-')[0].upper().replace('SIZE','').replace('IN STOCK','').strip()
                if size !='':
                    item['originsizes'].append(size)

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span[@class="retailer"]/text()').extract()
        salePrice = prices.xpath('.//div[@class="g-price"]/text()').extract()
        if len(salePrice) == 0:
            item['originsaleprice'] = listprice[0]
            item['originlistprice'] = listprice[0]
        else:
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = listprice[0]

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('cm' in info.strip() or 'mm' in info.strip()):
                fits.append(info.replace('-','').strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@id="photo_thumbs"]/div[@class=" currentVariant"]/a/@data-medium').extract()
        img_li = []
        for img in images:
            if 'http' not in img:
                img = 'https:' + img
                img_li.append(img)
        return img_li

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[contains(@class,"product")]/div/a/@href').extract())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'glamest'
    merchant = "Glamest"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            items = '//div[contains(@class,"product")]',
            designer = './/p[@itemprop="brand"]/a/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add_cart"]', _parser.checkout)),
            ('sku', ('//div[@class="cartBlockInfo"]/span[@id="prod_code"]/text()', _parser.sku)),
            ('name', '//h3[@itemprop="name"]/text()'),
            ('designer', ('//h2[@itemprop="brand"]//text()',_parser.designer)),
            ('images', ('//div[@id="photo_thumbs"]/div[@class=" currentVariant"]/a/@data-medium', _parser.images)),
            ('color','//span[@class="colorHEX"]/@title'),
            ('description', ('//div[@class="description"]//text()',_parser.description)),
            ('sizes', ('//div[@id="sizes"]/div[@class="dropdown-list"]/ul[@class="currentVariant"]/li/span/text()', _parser.sizes)),
            ('prices', ('//div[@class="price"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="description"]//text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
        ),
        f = dict(
            a = [
                'https://www.glamest.com/catalog/accessories?per_page=0&page=1',
            ],
            b = [
                'https://www.glamest.com/catalog/bags?per_page=0&page=1',
            ],
            c = [
                'https://www.glamest.com/catalog/clothing?per_page=0&page=1',
            ],
            s = [
                'https://www.glamest.com/catalog/shoes?per_page=0&page=1',
            ],
        params = dict(
            ),
        )
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD'
        ),
         ##################### No Country Support Added, Don't Know what cookies are Doing it ##############

        )
        


