from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.utils import *
import re

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        datas = json.loads(res.extract_first())
        item['sku'] = datas[0]['productMasterID']

        item['name'] = datas[0]['productName']
        item['designer'] = datas[0]['productBrand'].upper()
        item['color'] = datas[0]['productColor']
        item['tmp'] = datas

    def _images(self, res, item, **kwargs):
        images = res.extract()
        imgs_li = []
        for img in images:
            if img not in imgs_li:
                imgs_li.append(img)
        item['images'] = imgs_li
        item['cover'] = imgs_li[0]

    def _prices(self, res, item, **kwargs):
        item['originsaleprice'] = str(item['tmp'][0]['productPrice'])
        item['originlistprice'] = str(item['tmp'][0]['productPrice'])

    def _sizes(self, res, item, **kwargs):
        item['originsizes'] = ['IT']

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="product-image js-container_main_image"]/div/img/@data-zoom-image').extract()
        imgs = []
        for img in images:
            if img not in imgs:
                imgs.append(img)
        return imgs

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('Lenght' in info or 'Width' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _page_num(self, data, **kwargs):
        pages = 10
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=','?page={}'.format(i))
        return url
        
_parser = Parser()

class Config(MerchantConfig):
    name = 'fornasetti'
    merchant = 'Fornasetti'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[contains(@class,"b-product_tile")]',
            designer = './@data-variant',
            link = './div[@class="b-product-hover_box js-product-hover_box"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@title="Add to Bag"]', _parser.checkout)),
            ('sku', ('//script[contains(@class,"js-gtm_product_variants_info")]/text()',_parser.sku)),
            ('description', '//div[@class="b-product_long_description"]/ul/li/text()'),
            ('images', ('//div[@class="product-image js-container_main_image"]/div/img/@data-zoom-image', _parser.images)),
            ('prices', ('//html', _parser.prices)),
            ('sizes', ('//html', _parser.sizes)),
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
            size_info_path = '//span[@class="b-product_fit_information-label"]/ul/li/text()',
            ),
        )

    list_urls = dict(
        u = dict(
            h = [
                'https://www.fornasetti.com/cn/en/accessories/discover-all/?page='
            ],
        ),
    )
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            ),
        )