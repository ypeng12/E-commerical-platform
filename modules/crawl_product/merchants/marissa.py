from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        code = data.extract_first()
        item['sku'] = code if code.isdigit() else ''

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        osizes = sizes.extract()
        for osize in osizes:
            item['originsizes'].append(osize)
        if not item['originsizes'] and item['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('./s/text()').extract()[0]
            saleprice = prices.xpath('./span[@class="price-field"]/text()').extract()[0]
        except:
            listprice = prices.xpath('./span[@class="price-field"]/text()').extract()[0]
            saleprice = prices.xpath('./span[@class="price-field"]/text()').extract()[0]
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            image = 'https:' + img if 'http' not in img else img
            item['images'].append(image)
        item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-photos pdp-carousel"]/div/img/@src').extract()
        images = []
        for img in imgs:
            image = 'https:' + img if 'http' not in img else img
            images.append(image)
        return images

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[@class="product-view"]/div[@class="feature-products wrapper"]/div[@id="feature-slider"]//a[@class="product-image"]/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return
        item['cover'] = response.xpath('//img[@itemprop="image"]/@src').extract_first()
        purl = response.url
        item['main_prd'] = purl
        item['products']= [str(x) for x in outfits]
        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        print(infos)
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('&nbsp',' '))
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "marissa"
    merchant = "Marissa Collections"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@class="pagination"]//span[@class="page"][last()]/a/text()',
            items = '//div[@class="collection-grid"]/div',
            designer = './/h2[@class="product-vendor"]/a/text()',
            link = './/div[@class="primary-img"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//button[@name="add"]', _parser.checkout)),
            ('sku', ('//div/@data-product-id',_parser.sku)),
            ('name', '//*[@class="product-title"]/text()'),
            ('color', '//input[contains(@id,"swatch-0")]/@value'),
            ('designer', '//h1[@class="product-vendor"]/text()'),
            ('images', ('//div[@class="product-photos pdp-carousel"]/div/img/@src', _parser.images)),
            ('description', '//dl[@class="extra-info"]/dd[1]/p/text()'),
            ('sizes', ('//div[@data-option-index="1"]/div[not(contains(@class,"soldout"))]/@data-value', _parser.sizes)),
            ('prices', ('//div[@class="price-container"]', _parser.prices)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=114977,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//dl[@class="extra-info"]/dd[1]/p/text()',

            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://marissacollections.com/collections/womens-accessories-sunglasses",
                "https://marissacollections.com/collections/womens-accessories-belts?page=",
                "https://marissacollections.com/collections/womens-accessories-scarves-shawls?page=",
                "https://marissacollections.com/collections/womens-accessories-hats-and-headbands?page=",
                "https://marissacollections.com/collections/womens-accessories-watches?page=",
                "https://marissacollections.com/collections/womens-accessories-gloves?page=",
                "https://marissacollections.com/collections/home-decor?page=",
            ],
            b = [
                "https://marissacollections.com/collections/womens-handbags?page="
            ],
            c = [
                "https://marissacollections.com/collections/womens-clothing?page=",
                "https://marissacollections.com/collections/womens-accessories-shapewear?page="
            ],
            s = [
                "https://marissacollections.com/collections/womens-shoes?page="
            ],
            e = [
                "https://marissacollections.com/collections/beauty?page=",
            ],
        ),
        m = dict(
            a = [
                "https://marissacollections.com/collections/mens-accessories-sunglasses?page=",
                "https://marissacollections.com/collections/mens-accessories-belts?page=",
                "https://marissacollections.com/collections/mens-accessories-scarves-and-shawls?page=",
                "https://marissacollections.com/collections/mens-accessories-hats?page=",
                "https://marissacollections.com/collections/mens-accessories-watches?page=",
                "https://marissacollections.com/collections/mens-accessories-jewelry?page=",
                "https://marissacollections.com/collections/mens-accessories-ties-and-pocket-squares?page="
            ],
            b = [
                "https://marissacollections.com/collections/mens-accessories-handbags?page="
               ],
            c = [
                "https://marissacollections.com/collections/mens-coats?page=",
                "https://marissacollections.com/collections/mens-jackets?page=",
                "https://marissacollections.com/collections/mens-blazers?page=",
                "https://marissacollections.com/collections/mens-vests?page=",
                "https://marissacollections.com/collections/mens-shirts?page=",
                "https://marissacollections.com/collections/mens-cardigans?page=",
                "https://marissacollections.com/collections/mens-pants-and-denim?page=",
                "https://marissacollections.com/collections/mens-shorts?page=",
                "https://marissacollections.com/collections/mens-suits?page=",
                "https://marissacollections.com/collections/mens-polos?page=",
                "https://marissacollections.com/collections/mens-swimwear?page=",
                "https://marissacollections.com/collections/mens-knitwear?page=",
                "https://marissacollections.com/collections/mens-t-shirts?page=",
                "https://marissacollections.com/collections/mens-formal-shirts?page="
            ],
            s = [
                "https://marissacollections.com/collections/mens-shoes?page="
            ],
        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        RU = dict(
            discurrency = 'USD',
            currency = 'RUB',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        )
        )

        


