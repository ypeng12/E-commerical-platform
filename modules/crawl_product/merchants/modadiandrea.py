from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = (int(data.split('of')[-1].split('item')[0].strip())/12) +1
        return pages
    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?p')[0] + '?p='+str(i)
        return url
    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []

        if not sizes:
            size_li.append('IT')
        else:
            for s in sizes:
                if 'SOLD' not in s.upper():
                    size_li.append(s.replace(',','.'))

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//div[@class="current-price"]//span[@itemprop="price"]/text()').extract()
        listPrice = prices.xpath('.//div[@class="product-discount"]/span[@class="regular-price"]/text()').extract()
        item['originsaleprice'] = salePrice[0] if salePrice else ''
        item['originlistprice'] = listPrice[0] if listPrice else salePrice[0]
        item['color'] = item['color'].upper()

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
        if "color:" in description.lower():
            item['color'] = description.lower().split('color:')[-1].split('\n')[0]
        else:
            item['color'] = ''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//li[@class="thumb-container"]/a/@href').extract()

        images = []
        for img in imgs:
            image = img
            images.append(image)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//nav[@class="pagination"]/div[2]/text()').extract_first().strip().split('of')[-1].split('item')[0].strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'modadiandrea'
    merchant = 'ModaDiAndrea'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//nav[@class="pagination"]/div[2]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-meta"]',
            designer = './/span[@class="marquevig"]',
            link = './/h3[@itemprop="name"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-button-action="add-to-cart"]', _parser.checkout)),
            ('sku', '//*[@name="id_product"]/@value'),
            ('name', '//h2[@itemprop="name"]/text()'),
            ('designer','//span[@class="marqueproduct"]/text()'),
            ('images', ('//li[@class="thumb-container"]/a/@href', _parser.images)),
            ('color','//span[@itemprop="color"]/text()'),
            ('description', ('//div[@class="description-short"]//text()',_parser.description)),
            ('sizes', ('//select[@id="group_4"]/option[not(@disabled)]/text()', _parser.sizes)),
            ('prices', ('//div[@class="product-prices"]', _parser.prices))
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
            ),
        designer = dict(

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )



    list_urls = dict(
        f = dict(
            a = [
                'https://www.modadiandrea.com/en/43-women-accessories?p=1'
            ],
            b = [
                'https://www.modadiandrea.com/en/42-women-bags?p=1',
            ],

            s = [
                "https://www.modadiandrea.com/en/40-women-shoes?p=1"
            ],
        ),
        m = dict(
            a = [
                "https://www.modadiandrea.com/en/39-men-accessories?p=1"
            ],
            b = [
                'https://www.modadiandrea.com/en/38-mens-bags?p=1',
            ],
            c = [
                "https://www.modadiandrea.com/en/37-men-clothes?p=1"
            ],
            s = [
                "https://www.modadiandrea.com/en/36-men-shoes?p=1"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/en-us/',
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            # discurrency = 'EUR',
            currency_sign = "\u20AC",

            ),
        
        CN = dict(
            currency = 'CNY',
            discurrency = 'EUR',

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'EUR',

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'EUR',

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',

        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'EUR',

        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'EUR',

        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',

        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'EUR',

        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',

        ),
        DE = dict(
            currency = 'EUR',


        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',

        ),

        )

        


