from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser,parseProdLink
from utils.cfg import *
import time
from lxml import etree
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first():
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['sku'] = json_data['product']['id']
        item['name'] = json_data['product']['title']
        item['color'] = json_data['product']['variants'][0]['option1']
        description = json_data['product']['description']
        html = etree.HTML(description)
        desc = html.xpath('//text()')
        item['description'] = '\n'.join(desc)
        item['designer'] = json_data['product']['vendor']
        item['tmp'] = json_data

    def _prices(self, res, item, **kwargs):
        item['originlistprice'] = str(item['tmp']['product']['price'])[:-2]
        item['originsaleprice'] = str(item['tmp']['product']['price_max'])[:-2]

    def _sizes(self, res, item, **kwargs):
        size_data = item['tmp']['product']['variants']
        osizes = []
        for osize in size_data:
            if osize['available']:
                size = osize['option2']
                osizes.append(size)

        item['originsizes'] = osizes

    def _images(self, res, item, **kwargs):
        imgs = item['tmp']['product']['images']
        images_li = []
        for img in imgs:
            img = "https:" + img
            if img not in images_li:
                images_li.append(img)

        item['images'] = images_li
        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        imgs_data = json.loads(response.xpath('//script[@data-product-json]/text()').extract_first())
        images = []
        for img in imgs_data['product']['images']:
            img = "https:" + img
            images.append(img)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        datas = response.xpath(size_info['size_info_path']).extract()
        infos = []
        for data in datas:
            if data.strip() and data.strip() not in infos:
                infos.append(data.strip())

        return infos 

    def _page_num(self, data, **kwargs):
        page_num = data // 60
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

_parser = Parser()


class Config(MerchantConfig):
    name = "noblemars"
    merchant = 'Noblemars'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="number-articles"]/span/span[@class="nb-value"]/text()',
            list_url = _parser.list_url,
            items = '//div[contains(@class,"ProductItem__Info")]',
            designer = './p/text()',
            link = './h2/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//button[@data-action="add-to-cart"]/span', _parser.checkout)),
            ('sku', ('//script[@data-product-json]/text()', _parser.sku)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//html', _parser.sizes)),
            ('images',('//html', _parser.images)),
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
            size_info_path = '//div[@class="accordion-body"]/ul[contains(@class,"card-body")]/li/span//text()',
            ),
        blog = dict(
            ),
        checknum = dict(
            ),

        )

    list_urls = dict(
        f = dict(
            a = [
                'https://noblemars.com/collections/womens-jewelry?page={}',
            ],
            b = [
                'https://noblemars.com/collections/womens-bags?page={}'
            ],
            c = [
                'https://noblemars.com/collections/womens-ready-to-wear?page={}'
            ],
            s = [
                'https://noblemars.com/collections/womens-shoes?page={}'
            ],
        ),
        m = dict(
            a = [
                'https://noblemars.com/collections/mens-jewelry?page={}'
            ],
            b = [
                'https://noblemars.com/collections/mens-bags?page={}'
            ],
            c = [
                'https://noblemars.com/collections/mens-ready-to-wear?page={}'
            ],
            s = [
                'https://noblemars.com/collections/mens-shoes?page={}'
            ],

        params = dict(
            page = 1,
            ),
        ),

        country_url_base = '/us/',
    )

    countries = dict(
        US = dict(
            currency = 'USD',
        ),

        )
