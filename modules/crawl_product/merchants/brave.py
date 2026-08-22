from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self,checkout,item,**kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page = 5
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _sku(self,res,item,**kwargs):
        item["tmp"] = json.loads(res.extract_first())
        item['sku'] = item['tmp']['handle'].split('-')[-1].upper()
        item['name'] = item['tmp']['title'].upper()
        item['designer'] = item['tmp']['vendor']
        description = item['tmp']['description']

    def _images(self,res,item,**kwargs):
        imgs = item['tmp']['images']
        images_li = []
        cover = None
        for img in imgs:
            img = "https://" + img
            images_li.append(img)
        item['images'] = images_li
        item['cover'] = item['images'][0]

    def _sizes(self,res,item,**kwargs):
        sizes = item['tmp']['variants']
        size_li = []
        for size in sizes:
            if size['available']:
                size_li.append(size['title'])

        item['originsizes'] = size_li

    def _prices(self,res,item,**kwargs):
        listprice = res.xpath('./span[@id="ProductPrice"]/text()').extract_first()
        saleprice = res.xpath('.//span[@id="ComparePrice"]/text()').extract_first()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice if saleprice else listprice

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="product-single__media"]/img/@data-src-normal').extract()
        images_li = []
        for img in images:
            if "http" not in img:
                images_li.append("https://" + img.replace('_300x300',''))
        return images_li

_parser = Parser()

class Config(MerchantConfig):
    name = "brave"
    merchant = "Brave Kid"

    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = 'div[@data-section-id="template_collection"]/ul[@class="products-list"]/li[@class="product"]',
            designer = './a[@class="data-pid"]',
            link = './a/@href',
        ),
        product=OrderedDict([
            ('checkout',('//div[@class="product-single__add-to-cart"]/div/button[@name="add"]',_parser.checkout)),
            ('sku', ('//script[@id="ProductJson-template_product"]/text()', _parser.sku)),
            ('color', '//div[@class="product__color-wrapper"]/label/text()'),
            ('image',('//html',_parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('price',('//div[@class="price-container"]',_parser.prices)),
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
        blog = dict(
        ),
        checknum = dict(
            ),
    )

    list_urls = dict(
        g = dict(
            a = [
            'https://us.bravekid.com/collections/girls-hats-and-caps',
            'https://us.bravekid.com/collections/girls-belts',
            'https://us.bravekid.com/collections/girls-socks',
            'https://us.bravekid.com/collections/girls-fashion-accessories',
            ],
            b = [
            'https://us.bravekid.com/collections/girls-bags-and-backpacks?i={}'
            ],
            c = [
            'https://us.bravekid.com/collections/girls-tshirts?i={}',
            'https://us.bravekid.com/collections/girls-dresses?i={}',
            'https://us.bravekid.com/collections/girls-skirts-and-shorts?i={}',
            'https://us.bravekid.com/collections/girls-swimming-costumes?i={}',
            'https://us.bravekid.com/collections/girls-shirts?i={}',
            'https://us.bravekid.com/collections/girls-sweatshirts?i={}',
            'https://us.bravekid.com/collections/girls-jeans?i={}',
            'https://us.bravekid.com/collections/girls-trousers?i={}',
            'https://us.bravekid.com/collections/girls-tracksuits-dungarees?i={}',
            'https://us.bravekid.com/collections/girls-knitwear?i={}',
            'https://us.bravekid.com/collections/girls-jackets-down-jackets?i={}',
            ],
            s = [
            'https://us.bravekid.com/collections/girls-slides-and-sandals',
            'https://us.bravekid.com/collections/girls-gym-shoes',
            'https://us.bravekid.com/collections/girls-combat-boots-and-wellies',
            ],
        ),
        b = dict(
            a = [
            'https://us.bravekid.com/collections/boys-hats-and-caps?i={}',
            'https://us.bravekid.com/collections/boys-belts?i={}',
            'https://us.bravekid.com/collections/boys-socks?i={}',
            'https://us.bravekid.com/collections/boys-fashion-accessories?i={}'
            ],
            b = [
            'https://us.bravekid.com/collections/boys-bags-and-backpacks?i={}',
            ],
            c = [
            'https://us.bravekid.com/collections/boys-tshirts?i={}',
            'https://us.bravekid.com/collections/boys-trousers-shorts?i={}',
            'https://us.bravekid.com/collections/boys-swimming-costumes?i={}',
            'https://us.bravekid.com/collections/boys-shirts?i={}',
            'https://us.bravekid.com/collections/boys-sweatshirts?i={}',
            'https://us.bravekid.com/collections/boys-jeans?i={}',
            'https://us.bravekid.com/collections/boys-tracksuits?i={}',
            'https://us.bravekid.com/collections/boys-knitwear?i={}',
            'https://us.bravekid.com/collections/boys-underwear-pyjamas?i={}',
            'https://us.bravekid.com/collections/boys-jackets-and-down-jackets?i={}'
            ],
            s = [
            'https://us.bravekid.com/collections/boys-slides-sandals?i={}',
            'https://us.bravekid.com/collections/boys-gym-shoes?i={}',
            'https://us.bravekid.com/collections/boys-combat-boots-wellies?i={}',
            ],
        ),
    )

    countries = dict(
        US=dict(
            currency = 'USD',
        ),
        GB=dict(
            currency = 'GBP',
        ),
    )