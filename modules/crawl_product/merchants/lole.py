from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        code = res.extract_first().split('/products/')[-1].split('_1_')[0]
        item["sku"] = code

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first().upper()
        item['designer'] = 'LOLE'

    def _color(self,color,item,**kwargs):
        item["color"] = color.extract_first().strip()

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first().strip()

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./div[contains(@class,"text-lole-silver")]/text()').extract_first()
        saleprice = prices.xpath("./div/text()").extract_first()

        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _images(self, res, item, **kwargs):
        image_li = []
        for image in res.extract():
            for img in image.split(','):
                if img and img not in image_li and '_1000x.jpg' in img:
                    image_li.append(img.strip())
        item["images"] = image_li
        item["cover"] = image_li[0]

    def _sizes(self,res,item,**kwargs):
        sizes = res.extract()

        item["originsizes"] = [size.strip() for size in sizes if size]

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="relative"]/ul[@class="swiper-wrapper"]/li/img/@data-srcset').extract()

        image_li = []
        for image in res.extract():
            for img in image.split(','):
                if img and img not in image_li and '_1000x.jpg' in img:
                    image_li.append(img.strip())

        return image_li

    def _list_url(self, i, response_url, **kwargs):
        return response_url

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
    name = "lole"
    merchant = "Lole"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a[@class="last"]/text()',
            list_url = _parser.list_url,
            items = '//div[@class="product-list"]//article',
            designer = './text()',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[@data-cy="lole-product-add-to-cart"]',_parser.checkout)),
            ('sku', ('//div[@class="relative"]/ul[@class="swiper-wrapper"]/li/img/@data-srcset', _parser.sku)),
            ('name', ('//div[@class="yotpo yotpo-main-widget"]/@data-name', _parser.name)),
            ('color',('//p[contains(@class,"text-lole-gray")]/text()',_parser.color)),
            ('description','//div[@class="small-text"]/p/text()'),
            ('price', ('//div[@class="flex text-lg"]', _parser.prices)),
            ('images', ('//div[@class="relative"]/ul[@class="swiper-wrapper"]/li/img/@data-srcset', _parser.images)),
            ('sizes', ('//div/ul[@role="radiogroup"]/li[@role="radio"]/button[not(contains(@class,"disabled"))]/text()', _parser.sizes)),
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
            size_info_path = '//div[@class="mb-8 flex flex-col"]/p[@class="text-sm"]/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.lolelife.com/collections/accessories',
            ],
            b = [
                'https://www.lolelife.com/s/bestsellers-lily-bag',
            ],
            c = [
                'https://www.lolelife.com/collections/women',
            ],
        ),
        m = dict(
            a = [
                'https://www.lolelife.com/collections/accessories'
            ],
            c = [
                'https://www.lolelife.com/collections/men',
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )