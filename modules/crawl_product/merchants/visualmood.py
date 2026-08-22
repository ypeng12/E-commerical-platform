from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pagedata = data.extract_first()
        num = pagedata.split('product')[0].strip()
        return int(num)//21 + 1

    def _list_url(self, i, response_url, **kwargs):
        return response_url.replace('?page=','?page={}'.format(i))

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self,res,item,**kwargs):
        json_data = json.loads(res.extract_first().split('sizeChartsRelentless.product = ')[1].split('sizeChartsRelentless.productCollections')[0].rsplit(';',1)[0])
        item['tmp'] = json_data
        item['sku'] = json_data['variants'][0]['sku'][:-2]
        if " - " in json_data['title']:
            item['name'] = json_data['title'].split(' - ')[0].upper()
            item['color'] = json_data['title'].split(' - ')[1]
        else:
            item['name'] = json_data['title'].upper()
        item['designer'] = item['tmp']['vendor'].upper()

    def _description(self, res, item, **kwargs):
        description_li = res.extract()
        description = []
        for desc in description_li:
            if desc:
                description.append(desc)
        item['description'] = '\n'.join(description)

    def _images(self, res, item, **kwargs):
        images_data = item['tmp']['images']
        image_li = []
        for image in images_data:
            if 'https:' not in image_li:
                image_li.append('https:' + image)
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span[contains(@class,"product__price--compare")]/span/text()').extract_first()
        saleprice = prices.xpath('.//span[contains(@class,"product__price on-sale")]/span/text()').extract_first()
        if not saleprice and not saleprice:
            saleprice = prices.xpath('.//span[contains(@class,"product__price")]/span/text()').extract_first()
        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _sizes(self,res,item,**kwargs):
        size_data = item['tmp']['variants']
        size_li = []
        for size in  size_data:
            if size['available']:
                size_li.append(size['title'])
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        images_data = json.loads(response.xpath('//div[contains(@class,"product-image-main"]/div[@class="image-wrap"]/img/@data-photoswipe-src').extract())
        image_li = []
        for image in images_data:
            if image not in image_li:
                image_li.append(image)
        return image_li

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
    name = "visualmood"
    merchant = "Visual Mood"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[contains(@class,"collection-filter__item--count")]',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="grid-product__content"]',
            designer = './a/div/@class',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[contains(@class,"btn--full add-to-cart")]/span',_parser.checkout)),
            ('sku', ('//script[contains(text(),"var sizeChartsRelentless")]/text()', _parser.sku)),
            ('description', ('//div[contains(@class,"product-single__description")]/ul/li/span/text()', _parser.description)),
            ('images', ('//html', _parser.images)),
            ('price', ('//div[@class="product-single__meta"]', _parser.prices)),
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
            size_info_path = '//div[contains(@class,"product-single__description")]/ul/li/span/text()'
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.visualmood.com/collections/accessories?page='
            ],
            c = [
                'https://www.visualmood.com/collections/swimwear?page=',
                'https://www.visualmood.com/collections/yoga-clothes?page=',
                'https://www.visualmood.com/collections/skirts?page=',
            ],
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )