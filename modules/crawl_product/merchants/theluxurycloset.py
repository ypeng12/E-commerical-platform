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
        pages = (int(data.strip())*2)+1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('/page/1','/page/'+str(i))
        return url

    def _sku(self, data, item, **kwargs):
        sku = data.extract()[0].replace(' ','_').strip()
        item['sku'] = sku if sku.isdigit() else ''
        item['condition'] = 'p'

    def _color(self, data, item, **kwargs):
        color = json.loads(data.xpath('//input[contains(@id,"product-tag")]/@value').extract()[0])
        item['color'] = color["variant"]
        item['designer'] = color['brand']

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = images[0]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip().replace('(','').replace(')','').strip()
            if not desc:
                continue
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)
        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        osizes = sizes.extract()

        for osize in osizes:
            item['originsizes'].append(osize.split('Size:')[-1].strip())
        
        if not item['originsizes'] and kwargs['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//div[@class="now-price price-box"]//span/@original-price').extract()
        listPrice = prices.xpath('.//div[@class="old-price price-box "]//span/@original-price').extract()
        item['originsaleprice'] = salePrice[0].strip() if salePrice else ''
        item['originlistprice'] = listPrice[0].strip() if listPrice else ''

_parser = Parser()



class Config(MerchantConfig):
    name = 'theluxurycloset'
    merchant = 'The Luxury Closet'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="middle_number"]/@data-page', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"product-card")]',
            designer = './/meta[@itemprop="brand"]/@content',
            link = './/a[@class="product_link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[contains(@class,"addToCartDesktop")]', _parser.checkout)),
            ('sku', ('//input[@id="product_id"]/@value',_parser.sku)),
            ('color',('//html', _parser.color)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('sizes', ('//label[@class="item-size"]/text()', _parser.sizes)),
            ('images', ('//ul[@class="product-slides"]//a/@data-src', _parser.images)),
            ('description', ('//div[@class="item-detail"]//text()',_parser.description)),
            ('prices', ('//div[@class="product_prices cf"]', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//ul[@class="product-slides"]//a/@data-src'
            ),
        size_info = dict(
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://theluxurycloset.com/category/men/men-watches/page/1",
                "https://theluxurycloset.com/category/men/men-accessories/page/1",
            ],
            c = [
                "https://theluxurycloset.com/category/men/mens-clothes/page/1"
            ],
            b = [
                "https://theluxurycloset.com/category/men/men-bags/page/1"
            ],

            s = [
                "https://theluxurycloset.com/category/men/men-shoes/page/1"
            ],
        ),
        f = dict(
            a = [
                "https://theluxurycloset.com/category/women/womens-watches/page/1",
                "https://theluxurycloset.com/category/women/fine-jewelry/page/1",
                "https://theluxurycloset.com/category/women/women-accessories/page/1",
            ],
            b = [
                "https://theluxurycloset.com/category/women/womens-handbags/page/1",
            ],
            c = [
                "https://theluxurycloset.com/category/women/womens-clothes/page/1",
            ],
            s = [
                'https://theluxurycloset.com/category/women/womens-shoes/page/1'
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            currency_sign = '$',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict( 
            currency = 'KRW',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        DE = dict(
            language = 'DE',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',  
        )

        )
        


