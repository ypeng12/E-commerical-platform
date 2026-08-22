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

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'VALEXTRA'

    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img.split('?')[0].replace('.spin','-01.jpg')
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []
        if not sizes:
            size_li.append('IT')
        else:
            size_li = sizes
        item['originsizes'] = size_li

    def _prices(self, data, item, **kwargs):
        price = data.extract_first()
        item['originlistprice'] = price
        item['originsaleprice'] = price
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

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="Sirv"]/div/@data-src | //div[@class="product-image-gallery"]/img/@src').extract()

        images = []
        for img in imgs:
            image = img.split('?')[0].replace('.spin','-01.jpg')
            images.append(image)
        return images
      
_parser = Parser()


class Config(MerchantConfig):
    name = 'valextra'
    merchant = 'Valextra'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@class="pages"]//li[last()-1]//text()',
            items = '//div[@class="category-products "]/ul/li',
            designer = './/div[@class="sc-dyGzUR kCMbOt sc-hBbWxd cqWPzI"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@title="Add to Cart"]', _parser.checkout)),
            ('sku', '//span[@itemprop="sku"]/text()'),
            ('name', '//meta[@property="og:title"]/@content'),
            ('designer', ('//html',_parser.designer)),
            ('images', ('//div[@class="Sirv"]/div/@data-src | //div[@class="product-image-gallery"]/img/@src', _parser.images)),
            ('color','//span[@itemprop="color"]/text()'),
            ('description', ('//meta[@name="twitter:description"]/@content',_parser.description)),
            ('sizes', ('//ul[@class="size-list product-variation-list gl_clear-fix"]/li/a[not(contains(@title,"Check availability in our stores"))]/text()', _parser.sizes)),
            ('prices', ('//span[@itemprop="price"]/@content', _parser.prices))
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
        )



    list_urls = dict(
        f = dict(
            a = [
                'https://www.valextra.com/en-us/women/accessories-add-ons/?p='
            ],
            b = [
                'https://www.valextra.com/en-us/women/new-in/new-bags/?p=',
                'https://www.valextra.com/en-us/women/top-handles-handbags/?p=',
                'https://www.valextra.com/en-us/women/shoulder-bags/?p=',
                'https://www.valextra.com/en-us/women/totes/?p=',
                'https://www.valextra.com/en-us/women/clutches/?p=',
                'https://www.valextra.com/en-us/women/mini/?p=',
            ],
            c = [
            ],
            s = [
            ],
        ),
        m = dict(
            a = [
            ],
            b = [
                'https://www.valextra.com/en-us/men/briefcases/?p=',
                'https://www.valextra.com/en-us/men/document-holders-portfolios-pouches/?p=',
                'https://www.valextra.com/en-us/men/shoulder-bags/?p=',
            ],
            c = [
            ],
            s = [
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
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/en-us/',
            currency_sign = '$',
            ),
        # CN = dict(
        #     currency = 'CNY',
        #     country_url = '/eu/en/',
        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     country_url = '.jp/',
        #     translate = [
        #         ('women/new-in/new-bags/','products/list.php?category_id=13'),
        #         ('women/top-handles-handbags/','products/list.php?category_id=59'),
        #         ('women/shoulder-bags/','products/list.php?category_id=57'),
        #         ('women/totes/','products/list.php?category_id=16'),
        #         ('women/clutches/','products/list.php?category_id=17'),
        #         ('women/mini/','products/list.php?category_id=58'),
        #         ('women/accessories-add-ons/','products/list.php?category_id=60'),
        #         ('men/briefcases/','products/list.php?category_id=22'),
        #         ('men/document-holders-portfolios-pouches/','products/list.php?category_id=39'),
        #         ('men/shoulder-bags/','products/list.php?category_id=23'),

        #     ]
        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     country_url = '/eu/en/',
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     country_url = '/eu/en/',
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     country_url = '/eu/en/',
        # ),
        GB = dict(
            currency = 'GBP',
            country_url = '/en-gb/',
        ),
        # RU = dict(
        #     currency = 'RUB',
        #     country_url = '/eu/en/',
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     country_url = '/eu/en/',
        # ),
        AU = dict(
            discurrency = 'USD',
            currency = 'AUD',
            country_url = '/en-au/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/en-eu/',
        ),
        # NO = dict(
        #     area = 'NOK',
        #     country_url = '/eu/en/',
        # ),

        )

        


