from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from urllib.parse import urljoin
import requests
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        data = json.loads(checkout.extract_first())
        item['tmp'] = data
        check_soldout = data['offers']['availability']
        if 'instock' in check_soldout.lower():
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        try:
            color = res.extract_first().strip().strip('— ').upper()
        except:
            color = ''
        data = item['tmp']
        item['sku'] = (data['sku'].split('-')[0] + '_' + color) if color else data['sku'].split('-')[0]
        item['name'] = data['name'].upper()
        item['color'] = color
        item['designer'] = data['brand']['name'].upper()
        detail = data['description']
        item['description'] = detail

    def _images(self, data, item, **kwargs):
        imgs = item['tmp']['image']
        item['images'] = [imgs]
        item['cover'] = item['images'][0]

    def _prices(self, prices, item, **kwargs):
        item['originlistprice'] = item['tmp']['offers']['price']
        item['originsaleprice'] = item['tmp']['offers']['price']

    def _sizes(self, res, item, **kwargs):
        # datas = json.loads(res.extract_first())
        # variants = datas['props']['pageProps']
        # for variant in variants:
        osizes = []
        for size in res.extract():
            if size not in osizes:
                osizes.append(size)
        if not osizes and item['category'] in ['a','b','e']:
            osizes.append('IT')
        item['originsizes'] = osizes

    def _parse_multi_items(self, response, item, **kwargs):
        data = item['tmp']
        variants = data['variants'] if data['variants'] else [data['master']]
        multi_colors = True
        for option_type in data['option_types']:
            if option_type['name'] == 'size':
                multi_colors = False
        if multi_colors:
            for variant in variants:
                item_color = deepcopy(item)
                originsizes = []
                color = ''

                for option in variant['option_values']:
                    if option['option_type_name'] == 'size':
                        originsizes.append(option['name'])
                    elif option['option_type_name'] == 'color':
                        color = option['name']

                if variant['in_stock'] and not originsizes:
                    originsizes = ['IT']

                item_color['originsizes'] = originsizes
                self.sizes(originsizes, item_color, **kwargs)

                item_color['color'] = color
                item_color['sku'] = item_color['sku'] + '_' + color.upper() if color else item_color['sku']

                images = []
                imgs = variant['images'] if variant['images'] else data['master']['images']
                for img in imgs:
                    images.append(img['large_url'])
                item_color['images'] = images
                item_color['cover'] = images[0]

                yield item_color
        else:
            originsizes = []
            color = ''
            for variant in variants:

                for option in variant['option_values']:
                    if option['option_type_name'] == 'size' and variant['in_stock']:
                        originsizes.append(option['name'])
                    elif option['option_type_name'] == 'color':
                        color = option['name']

            if variant['in_stock'] and not originsizes:
                originsizes = ['IT']

            item['originsizes'] = originsizes
            self.sizes(originsizes, item, **kwargs)

            images = []
            imgs = data['master']['images']
            for img in imgs:
                images.append(img['large_url'])
            item['images'] = images
            item['cover'] = images[0]

            item['color'] = color
            item['sku'] = item['sku'] + '_' + color.upper() if color else item['sku']

            yield item

    def _parse_item_url(self, response, **kwargs):
        obj = json.loads(response.body)
        products = obj['meta']["totalPages"]
        pages = int(products)
        for x in range(1, pages+1):
            url = response.url.split("&page=")[0]+'&page='+str(x)
            result = getwebcontent(url)
            obj = json.loads(result)
            products = obj['products']
            for quote in products:
                href = quote['slug']+'.json'
                url =  urljoin('https://shop.goop.com/shop/products/', href)
                yield url,quote['brand_name']

    def _parse_images(self, response, **kwargs):
        images = []
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())

        imgs = [data['image']]
        for img in imgs:
            images.append(img)

        return images
    def _parse_checknum(self, response, **kwargs):

        obj = json.loads(response.body)
        number = (obj['meta']['totalCount'])
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info.lower() or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = 'goop'
    merchant = 'Goop'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout',('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('sku',('//span[@class="VariantPickerstyles__SelectedOptionText-vvspn3-1 jMqIvg"]/text()', _parser.sku)),
            ('images',('//html', _parser.images)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//span[@class="VariantPickerstyles__SwatchText-vvspn3-6 hjXHYX"]/text()', _parser.sizes)),
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
            size_info_path = '//div[@class="ProductDetailsstyles__Text-sc-1osiovg-2 ckoXeF"]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),

        )

    # parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
                "https://shop.goop.com/shop/collection/jewelry.json/?page=",
                "https://shop.goop.com/shop/collection/accessories.json/?page=",
            ],
            b = [
                "https://shop.goop.com/shop/collection/bags.json/?page=",
            ],
            c = [
                "https://shop.goop.com/shop/collection/clothing.json?page=",
            ],
            s = [
                "https://shop.goop.com/shop/collection/shoes.json?page=",
            ],
            e = [
                "https://shop.goop.com/shop/collection/beauty.json/?page="
            ],
        ),
        m = dict(
            e = [
                "https://shop.goop.com/shop/collection/men/beauty.json/?page="
            ],
            c = [
                "https://shop.goop.com/shop/collection/men/clothing.json/?page="
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
            currency = 'USD',
            )
        )

        