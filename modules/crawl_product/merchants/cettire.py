from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return False

    def _page_num(self, data, **kwargs):
        page_num = data
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        pid = data.extract_first().split('?')[0].split('-')[-1]
        item['sku'] = pid if len(pid) in [8, 9] and pid.isdigit() else ''

    def _name(self, data, item, **kwargs):
        json_data = json.loads(data.extract_first().split('__NEXT_DATA__ = ')[1].split(';__NEXT_LOADED_PAGES__')[0])
        vendor_ids = json_data['props']['apolloState']['data'].keys()
        data = json_data['props']['apolloState']['data']
        item['tmp'] = data
        for key in vendor_ids:
            all_real_keys = ['_id', 'productId', 'title', 'slug', 'description', 'vendor', 'isLowQuantity', 'isSoldOut', 'isBackorder', 'sku', 'barcode', 'productType', 'vip', 'metafields', 'pricing', 'shop', 'primaryImage', 'media', 'tags', 'variants', 'seoTitle', 'seoDescription', 'seoUrl', '__typename']
            allname_keys = [i for i in data[key].keys()]
            if allname_keys == all_real_keys:
                item['name'] = data[key]['title']
                item['designer'] = data[key]['vendor']
                description = data[key]['description']

                desc_li = []
                for desc in description.split('<br />'):
                    detail = desc.strip()
                    if not detail:
                        continue
                    desc_li.append(detail)
                description = '\n'.join(desc_li)

                item['description'] = description

    def _images(self, images, item, **kwargs):
        vendor_ids = item['tmp'].keys()
        json_data = item['tmp']
        datas = []
        for key in vendor_ids:
            all_real_keys = ['thumbnail', 'small', 'medium', 'large', 'original', '__typename']
            allname_keys = [i for i in json_data[key].keys()]
            if allname_keys == all_real_keys:
                datas.append(json_data[key]['thumbnail'])

        images = []
        for image in datas:
            if image not in images:
                images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, data, item, **kwargs):
        json_data = json.loads(data.extract_first().split('__NEXT_DATA__ = ')[1].split(';__NEXT_LOADED_PAGES__')[0])
        vendor_ids = json_data['props']['apolloState']['data'].keys()
        data = json_data['props']['apolloState']['data']
        sizes = []
        for key in vendor_ids:
            if 'size' not in data[key] or ('isSoldOut' in data[key] and data[key]['isSoldOut']):
                continue
            if data[key]['size'] in ['IT1','IT2','IT3','IT4','IT5','IT6']:
                size = data[key]['size'].replace('IT','')
            else:
                size = data[key]['size']
            sizes.append(size)
        item['originsizes'] = sizes

    def _prices(self, data, item, **kwargs):
        json_data = json.loads(data.extract_first().split('__NEXT_DATA__ = ')[1].split(';__NEXT_LOADED_PAGES__')[0])
        vendor_ids = json_data['props']['apolloState']['data'].keys()
        data = json_data['props']['apolloState']['data']
        saleprice = 0
        for key in vendor_ids:
            if 'price' in data[key] and data[key]['currencyCode'] == 'USD' and data[key]['regionCode'] == 'us':
                if data[key]['price'] > saleprice:
                    saleprice = data[key]['price']
                    listprice = data[key]['compareAtPrice']
        item['originlistprice'] = str(listprice) if listprice else str(saleprice)
        item['originsaleprice'] = str(saleprice)

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[@class="swiper-container swiper-product-pc"]/div/div/img/@src').extract()
        images = []
        for img in img_li:
            img = 'https:' + img.split('?')[0]
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and 'Dimensions' in info.strip():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()


class Config(MerchantConfig):
    name = 'cettire'
    merchant = "CETTIRE"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination"]/span[5]//text()',_parser.page_num),
            items = '//div[contains(@class,"product-list")]',
            designer = './/div[@class="product-card__brand"]/div/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//select[@class="product-form__variants"]/option/@data-sku', _parser.checkout)),
            ('sku',('//link[@hreflang="en-gb"]/@href',_parser.sku)),
            ('name', ('//script[contains(text(),"__NEXT_DATA__ =")]/text()',_parser.name)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//script[contains(text(),"__NEXT_DATA__ =")]/text()', _parser.sizes)),
            ('prices', ('//script[contains(text(),"__NEXT_DATA__ =")]/text()', _parser.prices))
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
            size_info_path = '//div[@itemprop="description"]//text()',   
            ),
        )
    list_urls = dict(
        m = dict(
            a = [
                'https://www.cettire.com/collections/mens-accessories?page='
            ],
            b = [
                'https://www.cettire.com/collections/mens-bags?page='
            ],
            c = [
                'https://www.cettire.com/collections/mens-clothing?page='
            ],
            s = [
                'https://www.cettire.com/collections/mens-shoes?page='
            ],
        ),
        f = dict(
            a = [
                'https://www.cettire.com/collections/womens-accessories?page='
            ],
            b = [
                'https://www.cettire.com/collections/womens-bags?page='
            ],
            c = [
                'https://www.cettire.com/collections/womens-clothing?page='  
            ],
            s = [
                'https://www.cettire.com/collections/womens-shoes?page='
            ],


        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            country_url = 'cettire.com'
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
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = 'uk.cettire.com',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = 'au.cettire.com',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = 'eu.cettire.com',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
        )
    )
        


