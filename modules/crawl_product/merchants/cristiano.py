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

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first().split(' - ')[1].upper()

        item['designer'] = res.extract_first().split(' - ')[0]

    def _images(self, res, item, **kwargs):
        image_li = res.extract()
        images = []
        for image in image_li:
            if image not in images:
                images.append(image)
        item['images'] = images
        item['cover'] = images[0]

    def _prices(self, res, item, **kwargs):
        saleprice = res.xpath('.//span[@class="current-price"]/span[@class="product-price"]/text()').extract_first()
        listprice = res.xpath('.//span[@class="regular-price"]/text()').extract_first()
        item["originlistprice"] = listprice if listprice else saleprice
        item["originsaleprice"] = saleprice

    def _sizes(self,res,item,**kwargs):
        size_li = []
        for size in res.extract():
            if size.strip():
                size_li.append(size.strip())
        item["originsizes"] = size_li

    def _page_num(self, data, **kwargs):
        page = data.url.split('/en/')[1].split('-')[0]
        num = int(page//24 + 1)
        return 5

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

_parser = Parser()

class Config(MerchantConfig):
    name = "cristiano"
    merchant = "Cristiano Calzature"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="thumbnail-container"]',
            designer = './a/img/@alt',
            link = './a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//button[@data-button-action="add-to-cart"]',_parser.checkout)),
            ('sku','//button[@id="iqit-wishlist-product-btn"]/@data-id-product'),
            ('name', ('//div[@class="product_desc"]/p/strong/text()', _parser.name)),
            ('color', ('//div[@class="product-variants"]/div/ul/li/span[@class="color"]//text()')),
            ('description', ('//div[@class="product-description"]/div/p/text()')),
            ('images', ('//div[@class="swiper-slide"]/div[@class="thumb-container"]/img/@data-src | //div[contains(@class,"product-lmage-large")]/div/a/@href', _parser.images)),
            ('price', ('//html', _parser.prices)),
            ('sizes', ('//div[@class="product-variants"]/div/ul/li/span[@class="radio-label"]/text()', _parser.sizes)),
        ]),
        image=dict(
            image_path = '//div[@class="swiper-slide"]/div[@class="thumb-container"]/img/@data-src',
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.cristianocalzature.it/en/26-accessories?page={}',
                'https://www.cristianocalzature.it/en/612-hat?page={}',
                'https://www.cristianocalzature.it/en/546-jewelry?page={}',
                'https://www.cristianocalzature.it/en/530-sunglasses?page={}',
                'https://www.cristianocalzature.it/en/542-belt?page={}'
                'https://www.cristianocalzature.it/en/560-tech-accessories?page={}',
            ],
            b = [
                'https://www.cristianocalzature.it/en/467-backpack?page={}',
                'https://www.cristianocalzature.it/en/29-bags?page={}',
                'https://www.cristianocalzature.it/en/257-wallets?page={}',
            ],
            e = [
                'https://www.cristianocalzature.it/en/571-fragrance?page={}',

            ],
            c = [
                'https://www.cristianocalzature.it/en/339-dresses?page={}',
                'https://www.cristianocalzature.it/en/469-underwear?page={}',
            ],
            s = [
                'https://www.cristianocalzature.it/en/252-shoes?page={}'
            ]
        ),
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
                'https://us.herno.com/en/men/outerwear/?page={}',
                'https://us.herno.com/en/men/down-jackets/?page={}',
                'https://us.herno.com/en/men/knitwear/?page={}',
            ],
            s = [
                'https://us.herno.com/en/men/accessories/shoes/?page={}'
            ]
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',
            discurrency='EUR',
            cookies={
            'i18n-prefs':'USD',
            }
        ),
        EU=dict(
            currency='EUR',
        ),
    )