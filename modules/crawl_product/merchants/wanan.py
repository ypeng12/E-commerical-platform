from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract()
        if not checkout:
            return True
        else:
            return False

    def _sku(self, res, item, **kwargs):
        data = json.loads(res.extract_first())
        item['tmp'] = data

        if item['country'] == 'US':
            sku = ''
            if 'code:' in data['description']:
                sku = data['description'].split('code:')[1].split('\n')[0].strip()
                item['color'] = data['description'].split('Colours:')[1].split('\n')[0]
                item['sku'] = sku
            if not sku and 'sku' in data.keys():
                item['sku'] = data['sku'].rsplit('-')[1]
        elif item['country'] == 'EU':
            item['sku'] = data['sku'].rsplit('-',1)[0]
            if 'Colori:' in data['description']:
                item['color'] = data['description'].split('Colori:')[1].split('\n')[0]
            else:
                item['color'] = ''

        if 'sku' in kwargs and item['sku'] != kwargs['sku']:
            item['sku'] = kwargs['sku']

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp']['name'].upper()
        item['designer'] = item['tmp']['brand']
        item['description'] = item['tmp']['description'].replace('\n\n','\n').strip('\n')

    def _images(self, res, item, **kwargs):
        image_li = []
        for image in res.extract():
            if image not in image_li and 'https' not in image:
                image_li.append('https:' + image)
        if not image_li:
            image_li.append(item['tmp']['image']['image'])
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('.//span[@class="product__price product__price--compare"]/span/text() | .//span[@class="product__price product__price--compare"]/text()').extract_first()
        if listprice:
            saleprice = res.xpath('.//span[@class="product__price on-sale"]/span/text() | .//span[@class="product__price on-sale"]/text()').extract_first()
        else:
            saleprice = res.xpath('.//span[@class="product__price"]//text()').extract_first()
        item["originlistprice"] = listprice if listprice else saleprice
        item["originsaleprice"] = saleprice

    def _sizes(self, res, item, **kwargs):
        size_li = []
        for size in res.extract():
            size_li.append(size)
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="product__thumb-item"]/div[@class="image-wrap"]/a/@href').extract()
        image_li = []
        for image in images:
            if image not in image_li and "https" not in image:
                image_li.append("https:" + image)
        if not image_li:
            data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
            image_li.append(data['image']['image'])
        return image_li

    def _page_num(self, data, **kwargs):
        pages = 3
        return pages

    def _list_url(self, i, response_url, **kwargs):
        return response_url + i

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "wanan"
    merchant = "Wanan Luxury"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination"]',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="grid-product__content"]',
            designer = './/div[@class="grid-product__vendor"]/text()',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//button[contains(@class,"add-to-cart")]/span/text()',_parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('name', ('//div[@class="product__inner container-full--medium-up"]/h2/text()', _parser.name)),
            ('images', ('//div[@class="product__thumb-item"]/div[@class="image-wrap"]/a/@href', _parser.images)),
            ('price', ('//html', _parser.prices)),
            ('sizes', ('//div[@class="variant-input"]/label[not(contains(@class,"disabled"))]/text()', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="care"]/div[@class="accordion-body"]/p/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.wananluxury.com/collections/accessori/Donna?page=',
                'https://www.wananluxury.com/collections/gioielli/Donna?page='
            ],
            b = [
                'https://www.wananluxury.com/collections/borse/Donna?page='
            ],
            c = [
                'https://www.wananluxury.com/collections/abbigliamento-donna?page=',
            ],
            s = [
                'https://www.wananluxury.com/collections/scarpe/Uomo?page='
            ]
        ),
        m = dict(
            a = [
                'https://www.wananluxury.com/collections/accessori/Uomo?page=',
                'https://www.wananluxury.com/collections/gioielli/Uomo?page='
            ],
            b = [
                'https://www.wananluxury.com/collections/borse/Uomo?page='
            ],
            c = [
                'https://www.wananluxury.com/collections/abbigliamento-uomo?page=',
            ],
            s = [
                'https://www.wananluxury.com/collections/scarpe/Uomo?page='
            ]
        ),

        country_url_base = 'wananluxury.com',
    )

    countries = dict(
        US=dict(
            currency='USD',
            country_url='us.wananluxury.com'       
        ),
        EU=dict(
            area = 'EU',
            currency='EUR',
            country_url='wananluxury.com'
        ),
    )