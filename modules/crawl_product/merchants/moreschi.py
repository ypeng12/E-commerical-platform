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
        pages = 100
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?p=1','?p='+str(i))
        return url

    def _sku(self, data, item, **kwargs):
        sku = data.extract()[0].replace(' ','_').strip()
        item['sku'] = sku.upper()

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        img_li = []
        for img in images:
            if "http" not in img:
                img = "https:" + img
            if img not in img_li:
                img_li.append(img)
        item['images'] = img_li

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

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        sizes1 = sizes.extract()

        for s in sizes1:
            s = s.split("|")[0].strip()
            item['originsizes'].append(s.strip())
        
        if len(item['originsizes']) == 0 and kwargs['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="ProductMeta__Price Price Text--subdued u-h4"]/span/text()').extract()
        # listPrice = prices.xpath('.//span[@class="old-price"]/span/text()').extract()
        item['originsaleprice'] = ''.join(salePrice[-1].strip().replace('.','').replace(',','.').split()) if salePrice else ''
        item['originlistprice'] = item['originsaleprice']







_parser = Parser()



class Config(MerchantConfig):
    name = 'moreschi'
    merchant = 'Moreschi'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@id="resultsCount"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/meta[@itemprop="brand"]/@content',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-action="add-to-cart"]', _parser.checkout)),
            ('color','//button[contains(@aria-controls,"color")]//span[@class="ProductForm__SelectedValue"]/text()'),
            ('sku', ('//span[@class="ProductMeta__SkuNumber"]/text()',_parser.sku)),
            ('name', '//h1/text()'),
            ('designer', '//meta[@property="og:site_name"]/@content'),
            ('images', ('//div[@class="Product__Slideshow Product__Slideshow--zoomable Carousel"]/div//noscript/img/@src', _parser.images)),
            ('description', ('//div[@class="description"]/div//text()',_parser.description)),
            ('sizes', ('//select[@name="id"]/option/text()', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(

            ),
        image = dict(
            image_path = '//div[@class="Product__Slideshow Product__Slideshow--zoomable Carousel"]/div//noscript/img/@src'
            ),
        size_info = dict(

            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.moreschi.it/en_wr/shop-online/men/piccola-pelletteria?p=1"
            ],
            b = [
                "https://www.moreschi.it/en_wr/shop-online/men/bags?p=1"
            ],
            c = [
                "https://www.moreschi.it/en_wr/shop-online/men/leather-jackets?p=1"
            ],
            s = [
                "https://www.moreschi.it/en_wr/shop-online/men/shoes?p=1"
            ],
        ),
        f = dict(
            a = [
                "https://www.moreschi.it/en_wr/shop-online/women/accessories?p=1"
            ],
            b = [
                "https://www.moreschi.it/en_wr/shop-online/women/bags?p=1",

            ],
            c = [
                "https://www.moreschi.it/en_wr/shop-online/women/leather-jackets?p=1"
            ],
            s = [
                'https://www.moreschi.it/en_wr/shop-online/women/shoes?p=1'
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
            # currency_sign = u'\u20ac',
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
        


