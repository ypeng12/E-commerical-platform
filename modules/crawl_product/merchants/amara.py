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
        data = json.loads(res.extract_first())
        item['sku'] = data['sku']

    def _name(self, res, item, **kwargs):
        data = json.loads(res.extract_first())
        item['name'] = data['name'].split(' - ')[0]
        item['designer'] = data['brand']['name'].upper()
        description = data['description']
        html = etree.HTML(description)
        item['description'] = html.xpath('//text()')
        item['color'] = data['name'].split(' - ')[1]

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first().strip()

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in images.extract():
            if image not in image_li:
                image_li.append(image)
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./span/span/text()').extract_first()
        saleprice = prices.xpath('./span/span[@class="price price-discounted"]/text()').extract_first()

        item["originsaleprice"] = saleprice if saleprice else listprice
        item["originlistprice"] = listprice

    def _sizes(self,res,item,**kwargs):
        sizes_json = res.extract()
        sizes_li = []
        if sizes_json:
            for size in sizes_json:
                if "out of stock" not in size.lower():
                    sizes_li.append(size)
        else:
            sizes_li.append('IT')
        item['originsizes'] = sizes_li


    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[contains(@class,"main-product-image-carousel__image")]/a/@href').extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return images_li

    def _list_url(self, i, response_url, **kwargs):
        return response_url + str(i)

_parser = Parser()


class Config(MerchantConfig):
    name = "amara"
    merchant = "Amara"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//ul[@class="pagination js-pager-page"]/li[6]/a/text()',
            list_url = _parser.list_url,
            items = '//div[@class="product-container"]',
            designer = './a/@data-ga-brand',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[contains(@class,"product-description__add-quantity-form-submit")]/text()',_parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('name', ('//script[@type="application/ld+json"]/text()', _parser.name)),
            ('price', ('//div[@class="item-reviews__block-reviews"]/div', _parser.prices)),
            ('images', ('//div[contains(@class,"main-product-image-carousel__image")]/a/@href', _parser.images)),
            ('sizes', ('//select[@id="appbundle_product_add_type_variations"]/option/text()', _parser.sizes)),

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
            c = [
                'https://www.amara.com/shop/nightwear/filters/gender/womens/page/',
            ]
        ),
        m = dict(
            c = [
                'https://www.amara.com/shop/nightwear/filters/gender/mens/page/'
            ]
        ),
        u = dict(
            h = [
                'https://www.amara.com/shop/home-accessories/page/',
                'https://www.amara.com/shop/dining/page/',
                'https://www.amara.com/shop/kitchenware/page/',
                'https://www.amara.com/shop/bedroom/page/',
                'https://www.amara.com/shop/bathroom/page/',
                'https://www.amara.com/shop/furniture/page/',
                'https://www.amara.com/shop/outdoors/page/'
            ],
        ),
        k = dict(
            a = [
                'https://www.amara.com/shop/kids/page/'
            ]
        )
    )

    countries = dict(
        GB=dict(
            currency='GBP',       
        ),
    )