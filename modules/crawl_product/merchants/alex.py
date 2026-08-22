from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self,res,item,**kwargs):
        if "add to" in res.extract_first().lower():
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page = data.extract_first().split('/')[1].strip()
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _name(self,res,item,**kwargs):
        item["tmp"] = json.loads(res.extract_first())
        item['name'] = item['tmp']['name']
        item['designer'] = item['tmp']['brand']['name']
        item['color'] = item['tmp']['color'] if 'color' in item['tmp'] else ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _images(self,res,item,**kwargs):
        imgs = item['tmp']['image']
        images_li = []
        cover = None
        for img in imgs:
            images_li.append(img)
        item['images'] = images_li
        item['cover'] = item['images'][0]

    def _sizes(self,res,item,**kwargs):
        sizes = res.extract()
        size_li = []
        for size in sizes:
            size_li.append(size.strip()) 
        item['originsizes'] = size_li

    def _prices(self,res,item,**kwargs):
        listprice = res.xpath('//div[@class="product-details_price"]/span/text()').extract_first()
        saleprice = res.xpath('//div[@class="product-details_price"]/span/text()').extract_first()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="thumbnails row"]/img/@data-src-normal').extract()
        images_li = []
        for img in images:
            if "http" not in img:
                images_li.append("https://www.alexandalexa.com" + img.replace('small','large'))
        return images_li

_parser = Parser()

class Config(MerchantConfig):
    name = "alex"
    merchant = "Alexandalexa"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="current-page"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//article[@class="product"]',
            designer = './/p[@class="brand"]',
            link = './a/@href',
        ),
        product=OrderedDict([
            ('checkout',('//button[contains(@class,"product-form__btn")]/span/text() | //button[contains(@class,"product-details_add-to-cart-button")]/span/text()',_parser.checkout)),
            ('sku', '//div/input[@id="vs-product-id"]/@value'),
            ('name', ('//script[@type="application/ld+json"]/text()', _parser.name)),
            ('description',('//meta[@name="description"]/@content',_parser.description)),
            ('image',('//html',_parser.images)),
            ('sizes', ('//div[@data-id="size"]/a[not(contains(@class,"attribute-value--unavailable"))]/@data-id', _parser.sizes)),
            ('price',('//html',_parser.prices)),
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
            'https://www.alexandalexa.com/en/49/girls-accessories/{}?orderBy=Published'
            ],
            c = [
            'https://www.alexandalexa.com/en/68/girls-trousers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/58/girls-outfits-sets/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/51/girls-coats-jackets/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/52/dresses/{}?orderBy=Published'
            ],
            s = [
            'https://www.alexandalexa.com/en/59/girls-shoes-trainers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2352/girls-boots/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2280/girl-slippers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2594/girls-sport-footwear/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2355/girls-trainers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2354/girls-sandals-flip-flops/{}?orderBy=Published'
            ],
        ),
        b = dict(
            a = [
            'https://www.alexandalexa.com/en/80/boys-accessories/{}?orderBy=Published'
            ],
            c = [
            'https://www.alexandalexa.com/en/96/boys-trousers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/87/boys-outfits-sets/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/82/boys-coats-jackets/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/81/boys-jumpers-and-knitwear/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/81/boys-jumpers-and-knitwear/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/1076/boys-pyjamas/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/89/boy-shorts/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/90/boys-skiwear/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/94/boys-swimwear/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/94/boys-swimwear/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/69/girls-tees-and-tops/{}?orderBy=Published'
            ],
            s = [
            'https://www.alexandalexa.com/en/59/girls-shoes-trainers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2352/girls-boots/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2280/girl-slippers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2594/girls-sport-footwear/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2355/girls-trainers/{}?orderBy=Published',
            'https://www.alexandalexa.com/en/2354/girls-sandals-flip-flops/{}?orderBy=Published'
            ],
        ),
    )

    countries = dict(
        US=dict(
            currency = 'USD',
            # currency_sign = u'USD',
            cookies = {
            "scarab.visitor":"%226C1F59FFA69ACAB3%22"
            }
        ),
        GB=dict(
            currency = 'GBP',
            # currency_sign = u'£',
            cookies = {
            "scarab.visitor":"%226C1F59FFA69ACAB3%22"
            }
        ),
    )