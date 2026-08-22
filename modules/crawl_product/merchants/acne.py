from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False
        
    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _name(self, name_data, item, **kwargs):
        item['name'] = name_data.extract_first().split(' - ')[0].strip()
        item['designer'] = 'ACNE STUDIOS'
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if 'http' not in img:
                image = urljoin('https://www.acnestudios.com/', img)
            else:
                image = img
            images.append(image.replace('1500x','750x'))
        item['cover'] = images[0]
        item['images'] = images

    def _color(self, data, item, **kwargs):
        title = data.extract_first()
        if title and ' - ' in title:
            item['color'] = title.split(' - ')[-1].strip().upper()
        else:
            item['color'] = ''

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

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        osizes = sizes_data.extract()
        sizes = []
        for osize in osizes:
            if 'out' in osize.lower() or osize.strip() in sizes:
                continue
            sizes.append(osize.strip())

        if item['category'] in ['a','b'] and not sizes:
            sizes = ['IT']

        item['originsizes'] = sizes

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="pdp-gallery__images"]//img/@data-src').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                image = urljoin('https://www.acnestudios.com/', img)
            else:
                image = img
            images.append(image.replace('1500x','750x'))
        return images

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[contains(@id,"shown-with")]//ul//a[@class="shownwithlink"]/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        cover = response.xpath('//a[@id="product-image-0"]//img/@data-zoom-src').extract()
        if cover:
            item['cover'] = 'https://www.acnestudios.com/'+cover[0]

        item['main_prd'] = response.meta.get('sku')
        item['products']= [(str(x).split('/')[-1].split('.')[0]) for x in outfits]

        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info in fits:
                continue
            fits.append(info)
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = 'acne'
    merchant = 'Acne Studios'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = '//ul[@data-context]/li',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './/a[@class="thumb-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="back-in-stock-ctr"]', _parser.checkout)),
            ('sku', '//div/@data-pid'),
            ('name', ('//meta[@property="og:title"]/@content', _parser.name)),
            ('images', ('//div[@class="pdp-gallery__images"]//img/@data-src', _parser.images)),
            ('color',('//meta[@property="og:title"]/@content',_parser.color)),
            ('description', ('//div[@data-content-toggle-id="pdp-description"]//text() | //div[@data-content-toggle-id="pdp-details"]//text()',_parser.description)),
            ('sizes', ('//div[@data-attr="size"]/a[not(contains(@class,"out-of-stock")) and not(contains(@class,"emptytext"))]/text()', _parser.sizes)),
            ('prices', ('//div[@class="price"]//span[@class="value"]/text()', _parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=62248,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@data-content-toggle-id="pdp-size-fit"]//text()',
            )
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-small-leather-goods',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-accessories',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-eyewear'
            ],
            b = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-bags'
            ],
            c = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-t-shirts',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-shirts',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-sweatshirts',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-knitwear',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-trousers',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-jeans',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-jackets',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-outerwear',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-shorts'
            ],
            s = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=man-shoes'
            ]
        ),
        f = dict(
            a = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-accessories',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-jewellery',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-eyewear',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-small-leather-goods'
            ],
            b = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-bags'
            ],
            c = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-outerwear',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-dresses',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-skirts',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-knitwear',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-sweatshirts',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-blouses',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-trousers',
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-suit-jackets',

            ],
            s = [
                'https://www.acnestudios.com/us/en/search?sz=10000&start=0&format=page-element&cgid=woman-shoes'
            ],
        params = dict(
            # TODO:
            page = 1,
            )
        )
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/us/en/',
        ),
        CN = dict(
            area = 'CN',
            language = 'ZH',
            currency = 'CNY',
            country_url = '/cn/zh/',
            currency_sign = '\xa5',
        ),
        JP = dict(
            area = 'EU',
            language = 'JA',
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = '/jp/ja/',
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            country_url = '/kr/en/',
            currency_sign = '\u20a9',
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            country_url = '/hk/en/',
            currency_sign = 'HK$',
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = 'EUR',
            country_url = '/apac/en/',
            currency_sign = '\u20ac',
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/uk/en/',
            currency_sign = '\xa3',
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            country_url = '/ca/en/',
            currency_sign = 'C$',
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            country_url = '/au/en/',
            currency_sign = 'A$'
        ),
        DE = dict(
            area = 'DE',
            language = 'DE',
            currency = 'EUR',
            country_url = '/de/de/',
            currency_sign = '\u20ac',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            country_url = '/no/en/',
            currency_sign = 'Nok'
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'EUR',
            country_url = '/emea/en/',
            currency_sign = '\u20ac',
        )
        )
        


