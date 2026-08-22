from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        count = data.split('productCount":')[-1].split(',',1)[0]
        num = int(count) / 12 + 1
        return num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + str((i-1) * 12)
        return url

    def _checkout(self, checkout, item, **kwargs):
        add_to_bag = checkout.xpath('.//span[@class="add-to-cart-button_text"]').extract()
        sold_out = checkout.xpath('.//span[@class="product-details_sold-out "]').extract()
        if not add_to_bag or sold_out:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract_first())
        item['tmp'] = data
        image = data['image'][0]
        item['sku'] = image.split('/')[-1].split('.jpg')[0][:-1]
        item['name'] = data['name']
        item['color'] = data['color']
        item['designer'] = "ALEXANDER WANG"

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []

        for size in sizes.extract():
            item['originsizes'].append(size.strip())

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['image']
        item['images'] = []
        cover = None
        for img in imgs:
            image = img.split('?')[0] + '?sw=600'
            item['images'].append(image)
        item['cover'] = item['images'][0] if item['images'] else ''

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('./span[@class="product-details_list-price"]/text()').extract()[0]
            saleprice = prices.xpath('./span[@class="product-details_sales-price"]/text()').extract()[0]
        except:
            listprice = prices.xpath('./span[@class="product-details_sales-price"]/text()').extract()[0]
            saleprice = prices.xpath('./span[@class="product-details_sales-price"]/text()').extract()[0]

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _description(self,desc, item, **kwargs):
        descs = desc.xpath('//div[@class="product-details-accordion_content-wrapper"]/text()').extract_first()
        description = [descs]
        details = desc.xpath('//div[@class="product-details-accordion_content-wrapper"]/ul[@class="product-details-accordion-list"]/li/text()').extract()
        for detail in details:
            description.append(detail.strip())
        item['description'] = '\n'.join(description)

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        imgs = data['image']
        images = []
        for img in imgs:
            image = img.split('?')[0] + '?sw=600'
            images.append(image)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info.strip() and info.strip() not in fits and ('Dimensions' in info.strip() or 'Model' in info.strip() or 'height' in info.strip() or 'cm' in info.strip() or 'Measures' in info.strip()):
                fits.append(info.strip())
        size_info = '/n'.join(fits)
        return size_info
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//html').extract_first().split('productCount":')[-1].split(',',1)[0].lower().split('items')[0].replace(' ','').strip())
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = "alxwang"
    merchant = "ALEXANDER WANG"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[contains(@class,"product-grid")]/li',
            designer = './/div/@data-brand',
            link = './/a[contains(@class,"product-tile-link")][1]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('images', ('//div[@class="product-details_images"]/picture/source/@data-srcset', _parser.images)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//div[@data-id="size"]/a[not(contains(@class,"unavailable"))]/@data-value', _parser.sizes)),
            ('prices', ('//div[@class="product-details_price"]', _parser.prices)),
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
            size_info_path = '//ul[@class="product-details-accordion-list"]/li/text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    list_urls = dict(
        f = dict(
            a = [
                "https://www.alexanderwang.com/us-en/search?cgid=women-jewelry&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-accessories&start=",
            ],
            b = [
                "https://www.alexanderwang.com/us-en/search?cgid=women-bags&start=",
            ],
            c = [
                "https://www.alexanderwang.com/us-en/search?cgid=women-tops&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-knitwear&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-bottoms&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-shirts&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-tshirts&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-sweaters&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-sweatshirts&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-pants&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-shorts&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-dresses&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-underwear&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-jackets&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=women-denim&start=",
            ],
            s = [
                "https://www.alexanderwang.com/us-en/search?cgid=women-shoes&start=",
            ],
        ),
        m = dict(
            a = [
                "https://www.alexanderwang.com/us-en/search?cgid=men-accessories&start=",
            ],
            b = [
               ],
            c = [
                "https://www.alexanderwang.com/us-en/search?cgid=men-tops&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=men-bottoms&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=men-sweaters&start=",
                "https://www.alexanderwang.com/us-en/search?cgid=men-jackets&start=",
            ],
            s = [
                "https://www.alexanderwang.com/us-en/search?cgid=men-shoes&start=",
            ],

        params = dict(
            # TODO:
            ),
        ),

    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '.com/us-en/',
            ),
        CN = dict(
            language = 'ZH',
            area = 'CN',
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = '.cn/cn-zh/',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '.com/gb-en/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            currency_sign = 'us$',
            country_url = '.com/ca-en/',
        ),
        JP = dict(
            area = 'CN',
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = '.com/jp-en/',
        ),
        KR = dict(
            area = 'CN',
            currency = 'KRW',
            country_url = '.com/kr-en/',
            discurrency = 'USD',
        ),
        SG = dict(
            discurrency = 'USD',
            area = 'EU',
            currency = 'SGD',
            currency_sign = 'us$',
            country_url = '.com/sg-en/',
        ),
        HK = dict(
            area = 'CN',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '.com/hk-en/',
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            currency_sign = 'A$',
            country_url = '.com/au-en/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '.com/de-en/',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '.com/no-en/',
        ),
        )



