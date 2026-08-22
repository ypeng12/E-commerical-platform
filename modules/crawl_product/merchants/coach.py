# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils import utils
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = int(data.replace('of','').strip())
        return pages

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*24
        url = urljoin(response_url.split('?')[0], '?sz=24&start=%s'%num)
        return url

    def _checkout(self, checkout, item, **kwargs):
        data = json.loads(checkout.extract()[-1])
        if 'offers' not in data:
            return True
        checkout = data['offers'][0]['availability']
        if 'InStock' in checkout:
            item['error'] = 'ignore' # just checkout
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        data = data.extract_first()
        if data and '_a0' in data:
            item['sku'] = data.split('?')[0].split('/')[-1].split('_a0')[0].strip().upper()
            item['designer'] = 'COACH'
        else:
            item['sku'] = ''

    def _name(self, data, item, **kwargs):
        for data in data.extract():
            if 'description' in data:
                break
        data = json.loads(data)[0]
        item["tmp"] = data
        item['name'] = data['name']
        item['color'] = data['color']
        item['description'] = data['description']

    def _images(self, images, item, **kwargs):
        item['images'] = images.extract()
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        orisizes = sizes.extract()
        item['originsizes'] = orisizes if orisizes else ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//span[@class="strike-through list"]/@data-unformatted').extract()[0].strip()
            saleprice = prices.xpath('.//span[@class="pdp sales"]/text()').extract()[0].strip()
        except:
            listprice = prices.xpath('.//span[@class="pdp list"]/text()').extract()[0].strip()
            saleprice = listprice
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_size_info(self, response, size_info, **kwargs):
        size_infos = response.xpath(size_info['size_info_path']).extract()
        fit = []
        for i in size_infos:
            if '"' in i:
                fit.append(i.strip())
        size_info = '\n'.join(fit)

        return size_info

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="element-wrapper"]/div/img/@src').extract()
        return images
    
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//input[@id="result-count"]/@value').extract_first().strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "coach"
    merchant = "COACH"
    # url_split = False


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="products-view visible-xs row"]//span[contains(text(),"of")]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="search-result-content row"]/div//div[@class="product-image"]',
            designer = './/h5[@class="brand-name function-bold"]/text()',
            link = './a[@itemprop="url"]/@href',
            ),
        product = OrderedDict([
            ('checkout',('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('sku', ('//meta[@property="og:image"]/@content', _parser.sku)),
            ('name', ('//script[@type="application/ld+json"]/text()', _parser.name)),
            ('prices', ('//div[@class="product-information"]//div[@class="price"]', _parser.prices)),
            ('images',('//div[@class="element-wrapper"]/div/img/@src',_parser.images)),
            ('sizes',('//select[@id="control-select-size"]/option[contains(@value,"coach")]/@data-attr-value',_parser.sizes)),
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
            size_info_path = '//div[@class="pdp-info__details-content"]/ul/li/text()',
            ),
        blog = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.coach.com/shop/women-accessories",
                ],
            b = [
                "https://www.coach.com/shop/women-handbags",
                "https://www.coach.com/shop/women-wallets",
                ],
            c = [
                "https://www.coach.com/shop/women-clothing",
            ],
            s = [
                "https://www.coach.com/shop/women-shoes",
            ]
        ),
        m = dict(
            a = [
                "https://www.coach.com/shop/men-accessories",
            ],
            b = [
                "https://www.coach.com/shop/men-bags",
                "https://www.coach.com/shop/men-wallets"
            ],
            c = [
                "https://www.coach.com/shop/men-clothing",
            ],
            s = [
                "https://www.coach.com/shop/men-shoes",
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
            country_url = 'www.coach.com',
            ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'uk.coach.com',
        ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            discurrency = 'USD',
            country_url = 'ca.coach.com',
        ),
        DE = dict(
            language = 'DE',
            area = 'DE',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'de.coach.com',
        )
        )
