from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first().split('/allImages/')[-1].split('-A')[0]
        if 'sku' in kwargs and item['sku'] != kwargs['sku']:
            item['sku'] = kwargs['sku']
        item['designer'] = "IRO"

    def _page_num(self, pages, **kwargs):
        return 1

    def _list_url(self, i, response_url, **kwargs):
        url = response_url 
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            if 'http' not in img:
                continue
            image = img.replace('?sw=1200&sh=1500&sm=fit','?sw=400&sh=500&sm=fit')
            item['images'].append(image)
        item['cover'] = item['images'][0] if item['images'] else ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _prices(self, prices, item, **kwargs):
        try:
            saleprice = prices.xpath('./span[contains(@class,"Product-priceSales")]/text()').extract()[0]
            listprice = prices.xpath('./span[@class="Product-priceStandard"]/text()').extract()[0]
        except:
            saleprice = prices.xpath('./span[contains(@class,"Product-priceSales")]/text()').extract()[0]
            listprice = saleprice
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        originsizes_ = sizes.extract()
        for size in originsizes_:
            item['originsizes'].append(size.strip())
        if kwargs['category'] in ['a','b'] and len(item['originsizes'])==0:
            item['originsizes'].append('IT')

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('cm' in info.strip().lower() or 'model' in info.strip().lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        images = []
        imgs = response.xpath('//div[@class="js-sliderProduct"]/div/img/@src').extract()
        for img in imgs:
            if 'http' not in img:
                continue
            image = img.replace('?sw=1200&sh=1500&sm=fit','?sw=400&sh=500&sm=fit')
            images.append(image)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[contains(@class,"ProductTile-name")]/a/@href').extract())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'iro'
    merchant = 'IRO'

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"ProductTile-name")]',
            designer = './/span[@class="brand high-level-description"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//button[@id="add-to-cart"]', _parser.checkout)),
            ('sku',('//img[@class="js-openPicture"]/@src',_parser.sku)),
            ('name', "//h1[@class='Product-name']/text()"),
            ('color',"//ul[@class='Product-options Product-options--color']/li[@class='selectable selected']/a/span/text()"),
            ('description', ("//h2[@class='Product-ShortDescription-Content']//text()",_parser.description)),
            ('prices', ('//div[@class="Product"]//div[@class="Product-price"]', _parser.prices)),
            ('images',('//div[@class="js-sliderProduct"]/div/img/@src',_parser.images)),
            ('sizes',("//ul[@class='Product-options Product-options--size']/li[contains(@class,'selectable')]/a/span/text()",_parser.sizes)),
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
            size_info_path = '//div[@class="Product-collapse-content"]/text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    list_urls = dict(
        f = dict(
            a = [
                "https://www.iroparis.com/us/c/women/accessories/?format=page-element&sz=60&all=",
            ],
            b = [
            ],
            c = [
                "https://www.iroparis.com/us/c/women/coats-jackets/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/women/sweaters/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/women/dresses/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/women/shirts-tops/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/women/t-shirts/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/women/denim/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/women/trousers/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/women/skirts-shorts/?format=page-element&sz=60&all=",
            ],
            s = [
                "https://www.iroparis.com/us/c/women/shoes/?format=page-element&sz=60&all=",
            ],
        ),
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
                "https://www.iroparis.com/us/c/men/coats-jackets/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/men/sweaters/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/men/shirts/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/men/t-shirts/?format=page-element&sz=60&all=",
                "https://www.iroparis.com/us/c/men/denim-pants/?format=page-element&sz=60&all=",
            ],
            s = [
                "https://www.iroparis.com/us/c/men/shoes/?format=page-element&sz=60&all=",
            ],

        params = dict(
            ),
        ),

        country_url_base = '/us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/us/',
            ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/uk/',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/eu/',
            thousand_sign = '',
        ),
        )

        


