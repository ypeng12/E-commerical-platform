from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from utils.utils import *
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = 10
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _sku(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first().split('var __st=')[-1].rsplit(';', 1)[0])
        item['sku'] = json_data['rid']

    def _description(self, desc, item, **kwargs):
        description = []
        for des in desc.extract():
            if des.strip():
                description.append(des.strip())
        item['description'] = '\n'.join(description)

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes_data, item, **kwargs):
        if len(sizes) != 0:
            for size in sizes:
                if size['variantId'] in sizes_stocks_ids:
                    item['originsizes'].append(size['size'].split('-')[0].strip()+memo)
                if item['color'] == '':
                    item['color'] = size['colour'].upper()
        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT'+memo]

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[contains(@class,"price-item--regular")]/text()').extract_first()
        listprice = prices.xpath('.//div[@class="price__sale"]/span/s/text()').extract_first()

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _get_review_url(self, response, **kwargs):
        review_urls = response.xpath('//div[@class="pagination"]/div/a/@href').extract()
        if review_urls:

            urls = []
            for review_url in review_urls:
                if review_url not in urls:
                    urls.append(review_url)
                    review_url = urljoin(response.url, review_url)
                    yield review_url
        else:
            yield response.url

    def _reviews(self, response, **kwargs):
        for quote in response.xpath("//div[@id='judgeme_product_reviews']//div[@class='jdgm-rev-widg__reviews']/div"):
            review = {}

            review['user'] = quote.xpath(".//span[@class='jdgm-rev__author']").extract_first().strip()
            review['title'] = quote.xpath(".//b[@class='jdgm-rev__title']").extract_first().strip()
            review['content'] = quote.xpath(".//div[@class='jdgm-rev__body']/p/text()").extract_first().strip()
            review['score'] = float(quote.xpath(".//span[@class='jdgm-rev__rating']/@data-score").extract_first().strip().split('stars_')[-1].split('_1-0.png')[0])
            review['review_time'] = quote.xpath(".//span[contains(@class,'jdgm-spinner')]/@data-content").extract_first().replace('UTC', '').strip()

            yield review

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[contains(@class,"product__media")]/img/@src').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)

        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//*[@id="product-count"]/text()').extract_first().split(' ')[0].replace(',',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "Luosophy"
    merchant = 'Luosophy'
    mid = 0

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num =  _parser.page_num,
            list_url = _parser.list_url,
            items = '//ul[@id="product-container"]/li',
            designer = './/div[@class="brand"]/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//div[@class="product-form__buttons"]/button[@name="add"]/span', _parser.checkout)),
            ('sku',('//script[@id="__st"]/text()', _parser.sku)),
            ('name', '//div[@id="product-title"]/text()'),
            ('color', '//fieldset[contains(@class,"product-form__input")]/label/text()'),
            ('designer', '//div[contains(@class,"product__info-wrapper")]/div/p/text()'),
            ('description', ('//div[contains(@class,"product__description")]/text()',_parser.description)),
            ('images', ('//div[contains(@class,"product__media")]/img/@src', _parser.images)),
            ('sizes', ('//fieldset[contains(@class,"product-form__input")]/label[contains(@for,"__main-2")]/text()', _parser.sizes)),
            ('prices', ('//div[@class="price__container"]', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        reviews = dict(
            get_review_url = _parser.get_review_url,
            method = _parser.reviews,
            ),
        image = dict(
            method = _parser.parse_images,
            current_path='//script[@type="sui-state"]/text()'
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
                'https://www.luosophy.com/collections/women?page={}&pf_pt_category=Accessories+%2F+Belts',
                'https://www.luosophy.com/collections/women?pf_pt_category=Accessories+%2F+Bracelets',
                'https://www.luosophy.com/collections/women?pf_pt_category=Accessories+%2F+Gloves',
                'https://www.luosophy.com/collections/women?pf_pt_category=Accessories+%2F+Hats',
                'https://www.luosophy.com/collections/women?pf_pt_category=Accessories+%2F+Miscellaneous',
                'https://www.luosophy.com/collections/women?pf_pt_category=Accessories+%2F+Sunglasses',
            ],
            b = [
                'https://www.luosophy.com/collections/women?pf_pt_category=Accessories+%2F+Wallets',
                'https://www.luosophy.com/collections/women?pf_pt_category=Handbags+%2F+Belt+Bags',
                'https://www.luosophy.com/collections/women?pf_pt_category=Handbags+%2F+Backpacks'
            ],
            c = [
                'https://www.luosophy.com/collections/women?page={}pf_pt_category=Accessories+%2F+Hosiery',
                'https://www.luosophy.com/collections/women?pf_pt_category=Bottoms+%2F+Leggings',
                'https://www.luosophy.com/collections/women?pf_pt_category=Bottoms+%2F+Pants',
                'https://www.luosophy.com/collections/women?pf_pt_category=Dresses+%2F+Cocktail+Dresses',
            ],
        ),
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],

        params = dict(
            page = 1,
            ),
        ),

        country_url_base = 'www.',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            currency_sign = '$',
        ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            currency_sign = u'\uffe5',
            
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = u'HK$',
        ),
        )
