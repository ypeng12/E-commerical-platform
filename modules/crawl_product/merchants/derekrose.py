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
        item['sku'] = data.extract_first().split(':')[-1].upper().strip()

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            img = img.replace('/100x133/','/')
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        item['designer'] = "DEREK ROSE"
        description1 = description.xpath(".//span[@itemprop='description']//text()").extract() + description.xpath("//div[contains(@class,'product-details__description-copy--alpha')]//text()").extract() + description.xpath(".//h2[@class='product-details__obj']/text()").extract()
        description1 = description1 +description.xpath("//div[contains(@class,'product-details__description-copy--alpha')]//text()").extract()
        desc_li = []
        for desc in description1:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.extract()
        size_li = []
        for size in sizes:
            size_li.append(size.strip())
        item['originsizes'] = size_li
        if item['category'] in ['a','b'] and not size_li:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.extract()
        listprice = prices.extract()

        item['originsaleprice'] = saleprice[0].strip()
        item['originlistprice'] = listprice[0].strip()

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[@class="swiper-wrapper"]//div/img/@src').extract()
        images = []
        for img in img_li:
            img.replace('/100x133/','/')
            if img not in images:
                images.append(img)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//a[@class="products-list__link"]/@href').extract())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'derekrose'
    merchant = "Derek Rose"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//a[@class="products-list__link"]',
            designer = './/h3[@class="list-product-brand"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[contains(@id,"product-addtocart-button")]', _parser.checkout)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('color',"//h2[@class='product-details__obj']/text()"),
            ('images', ('//div[@class="swiper-wrapper"]//div/img/@src', _parser.images)),
            ('sku', ('//p[@class="product-details__sku"]/text()', _parser.sku)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//div[@id="options"]//span[@class="product-details__option-content"]/text()', _parser.sizes)),
            ('prices', ('//div[@id="product-zoom-target-wrapper"]//span[@class="price"]/text()', _parser.prices))
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
            a = [
                "https://www.derek-rose.com/us/men/clothing/accessories.html?limit=all&a=",
            ],
            b = [
            ],
            c = [
                "https://www.derek-rose.com/us/men/clothing.html?limit=all&a=",
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
	            "https://www.derek-rose.com/us/women/clothing/womens-accessories.html?limit=all&a="
            ],
            b = [
            ],
            c = [
                'https://www.derek-rose.com/us/women/clothing.html?limit=all&a=',
            ],
            s = [
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
            country_url='derek-rose.com/us/'
        ),
        CN = dict(
            area = 'EU',
            currency = 'CNY',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'GBP',
            country_url='derek-rose.com/',
            currency_sign = '£'
        ),

        )
        


