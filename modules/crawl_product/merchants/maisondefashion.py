from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
import json
from lxml import etree
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first().lower() == 'add to cart':
            return False
        else:
            return True

    def _page_num(self, url, **kwargs):
        page_num = url.split('p=')[-1]
        return int(page_num)

    def _sku(self, res, item, **kwargs):
        sku = res.extract_first()
        item['sku'] = sku if sku.isdigit() else ''

    def _designer(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        item['designer'] = json_data['vendor']
        
    def _description(self, desc, item, **kwargs):
        html = etree.HTML(item['tmp']['description'])
        detail = html.xpath('//text()')

        item['description'] = "\n".join(detail).replace('\n','')

    def _sizes(self, res, item, **kwargs):
        variants = item['tmp']['variants']
        sizes_li = []
        for variant in variants:
            if variant['available']:
                sizes_li.append(variant['option1'])

        item['originsizes'] = sizes_li
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('./dl[@class="price__regular"]/dd/span[@data-regular-price]/span/text()').extract_first()
        listprice = prices.xpath('./dl[@class="price__sale"]/dd/span[@data-regular-price]/span/text()').extract_first()

        item['originlistprice'] = listprice if listprice != '£0.00' else saleprice
        item['originsaleprice'] = saleprice

    def _images(self, images, item, **kwargs):
        images = item['tmp']['images']
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
            if img not in imgs:
                imgs.append(img)
        item['cover'] = imgs[0]
        item['images'] = imgs


    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@id="thumb-slider-wrapper"]//div[contains(@class,"product-single__thumbnail")]/img/@src').extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
                imgs.append(img)
        img_li = []
        for img in imgs:
            if img not in img_li:
                img_li.append(img)     
        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="amount amount-has-pages"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('products',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'maisondefashion'
    merchant = 'Maison de Fashion'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="last"]/a/@href',_parser.page_num),
            items = '//li[@class="item" or @class="item last"]',
            designer = './/div[@class="product-designer"]/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product-add"]/input/@value', _parser.checkout)),
            ('sku', ('//div[@data-section-type="product-recommendations"]/@data-product-id', _parser.sku)),
            ('name', '//div[@class="product__section--header"]/h1/text()'),    # TODO: path & function
            ('designer', ('//script[@type="application/json"][@class="product-json"]/text()', _parser.designer)),
            ('images', ('//div[@class="swiper-slide"]/img[@class="product__gallery__carousel__image"]/@src', _parser.images)),
            ('description', ('//html',_parser.description)), # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="price__pricing-group"]', _parser.prices))
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="fit-advisor"]/ul/li/text()',
            ),
        designer = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://maisondefashion.com/collections/mens-designer-belts?usf_sort=-date',
                'https://maisondefashion.com/collections/mens-designer-hats',
                'https://maisondefashion.com/collections/mens-designer-caps?usf_sort=bestselling'
            ],
            b = [
                'https://maisondefashion.com/collections/mens-designer-bags'
            ],
            c = [
                'https://maisondefashion.com/collections/mens-designer-t-shirts?usf_sort=-date&usf_take=200',
                'https://maisondefashion.com/collections/mens-designer-polo-shirts?usf_sort=-date&usf_take=200',
                'https://maisondefashion.com/collections/jackets-coats?usf_sort=-date&usf_take=200',
                'https://maisondefashion.com/collections/mens-designer-sweatshirts?usf_sort=-date&usf_take=200',
                'https://maisondefashion.com/collections/mens-designer-shirts&usf_take=200',
                'https://maisondefashion.com/collections/mens-designer-trousers?usf_sort=-date&usf_take=200'
            ],
            s = [
                'https://maisondefashion.com/collections/mens-designer-shoes?usf_sort=-date'
            ],
        ),
        f = dict(
            a = [
                'https://maisondefashion.com/collections/womens-belts?usf_sort=bestselling',
                'https://maisondefashion.com/collections/women-s-jewellery?usf_sort=bestselling',
                'https://maisondefashion.com/collections/womens-masks?usf_sort=bestselling'
            ],
            b = [
                'https://maisondefashion.com/collections/womens-designer-bags?usf_sort=-date'
            ],
            c = [
                'https://maisondefashion.com/collections/womans-tops?usf_sort=bestselling',
                'https://maisondefashion.com/collections/womans-bottoms',
                'https://maisondefashion.com/collections/womans-shorts?usf_sort=bestselling'
            ],
            s = [
                'https://maisondefashion.com/collections/womens-boots?usf_sort=bestselling',
                'https://maisondefashion.com/collections/womens-sneakers?usf_sort=bestselling'
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        GB = dict(
            area = 'US',
            currency = 'GBP',
            currency_sign = '\u00a3',
        ),
        )

        


