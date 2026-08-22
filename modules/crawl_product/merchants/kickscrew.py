from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from utils.cfg import *
import re

class Parser(MerchantParser):
    def _tmp(self, res, item, **kwargs):
        item['tmp'] = {}
        try:
            scripts = res.xpath('//script[@type="application/ld+json"]/text()').getall()
            for script in scripts:
                try:
                    data = json.loads(script.strip())
                    if isinstance(data, dict):
                        if data.get('@type') == 'ProductGroup':
                            item['tmp'] = data
                            return
                        if '@graph' in data:
                            for node in data['@graph']:
                                if node.get('@type') == 'ProductGroup':
                                    item['tmp'] = node
                                    return
                except json.JSONDecodeError:
                    continue
        except Exception:
            item['tmp'] = {}

    def _sku(self, res, item, **kwargs):
        item['sku'] = item['tmp'].get('@id', '').split('/')[-1] or 'UNKNOWN'
        sizes_json = json.loads(res.xpath('.//script[@id="__NEXT_DATA__"]/text()').extract_first())['props']['pageProps']['fallback']
        key = [i for i in sizes_json.keys() if 'query getProduct' in i]
        sizes_datas = sizes_json[key[0]]['variants']
        sizes_json = {}
        sizes_li = []
        for sizes_data in sizes_datas:
            if sizes_data['availableForSale'] and sizes_data['price']['amount']:
                size_name = [data for data in sizes_data['selectedOptions'] if 'Size' in data['name']][0]['value']
                sizes_li.append(size_name)
                saleprice = sizes_data['price']['amount']
                listprice = sizes_data['compareAtPrice'] if sizes_data['compareAtPrice'] else saleprice
                sizes_json[size_name] = {'list_price': listprice,
                                         'sale_price': saleprice}
        item['originsizes'] = sizes_li
        item['size_prices'] = sizes_json

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp'].get('name', '').upper()

    def _designer(self, res, item, **kwargs):
        brand = item['tmp'].get('brand', {})
        item['designer'] = brand.get('name', '').upper() if isinstance(brand, dict) else ''

    def _description(self, res, item, **kwargs):
        item['description'] = item['tmp'].get('description', '')

    def _images(self, res, item, **kwargs):
        variants = item['tmp'].get('hasVariant', [])
        image_set = set()
        for variant in variants:
            img = variant.get('image')
            if img:
                image_set.add(img)
        item['images'] = list(image_set)
        item['cover'] = item['images'][0] if item['images'] else ''

    def _color(self, res, item, **kwargs):
        variants = item['tmp'].get('hasVariant', [])
        color_set = set()
        for variant in variants:
            color = variant.get('color', '').strip()
            if color:
                color_set.add(color)
        item['color'] = ', '.join(color_set)
    #
    # def _sizes(self, res, item, **kwargs):
    #     sizes = []
    #     try:
    #         scripts = res.xpath('//script[contains(text(),"ProductOption")]/text()').getall()
    #         print(scripts)
    #         for script in scripts:
    #             if 'ProductOption' in script:
    #                 match = re.search(r'(\{.*?\})', script)
    #                 if match:
    #                     data = json.loads(match.group(1))
    #                     for opt in data.get('options', []):
    #                         if opt.get('name', '').lower() == 'size':
    #                             raw_sizes = opt.get('values', [])
    #                             for size in raw_sizes:
    #                                 us_match = re.search(r"Men's US (\d+\.?\d*)", size)
    #                                 if us_match:
    #                                     sizes.append(us_match.group(1))
    #                             break
    #     except:
    #         pass
    #
    #     if not sizes:
    #         variants = item['tmp'].get('hasVariant', [])
    #         for variant in variants:
    #             size_data = variant.get('size') or {}
    #             if isinstance(size_data, dict):
    #                 name = size_data.get('name')
    #                 if name:
    #                     sizes.append(name)
    #
    #     item['sizes'] = list(OrderedDict.fromkeys(sizes))

    def _prices(self, res, item, **kwargs):
        try:
            price_text = res.xpath('//div[contains(@class,"product-price")]/text()').re_first(r'\$([\d\.]+)')
            if price_text:
                item['saleprice'] = float(price_text)
                item['listprice'] = float(price_text)
                return
        except:
            pass

        try:
            scripts = res.xpath('//script[contains(text(),"priceRange")]/text()').getall()
            for script in scripts:
                if 'priceRange' in script:
                    match = re.search(r'"priceRange":\{"maxVariantPrice":\{"amount":"(\d+\.?\d*)"', script)
                    if match:
                        raw = float(match.group(1))
                        amount = raw / 10 if raw > 1000 else raw
                        item['saleprice'] = item['listprice'] = amount
                        return
        except:
            pass

        item['saleprice'] = 0.0
        item['listprice'] = 0.0

    def _related_products(self, res, item, **kwargs):
        return

    def _metadata(self, res, item, **kwargs):
        tmp = item.get('tmp', {})
        metadata = {}

        if 'releaseDate' in tmp:
            metadata['release_date'] = tmp['releaseDate']
        if 'category' in tmp:
            metadata['category'] = tmp['category']
        if 'productGroupID' in tmp:
            metadata['product_group_id'] = tmp['productGroupID']
        if 'aggregateRating' in tmp:
            metadata['rating'] = tmp['aggregateRating'].get('ratingValue')
            metadata['review_count'] = tmp['aggregateRating'].get('reviewCount')

        for prop in tmp.get('additionalProperty', []):
            if prop.get('name') == 'collection':
                metadata['collection'] = prop.get('value')
            if prop.get('name') == 'silhouette':
                metadata['silhouette'] = prop.get('value')

        item['metadata'] = metadata

_parser = Parser()

class Config(MerchantConfig):
    name = 'kickscrew'
    merchant = 'KicksCrew'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('tmp', ('//html', _parser._tmp)),
            ('sku', ('//html', _parser._sku)),
            ('name', ('//html', _parser._name)),
            ('designer', ('//html', _parser._designer)),
            ('description', ('//html', _parser._description)),
            ('images', ('//html', _parser._images)),
            ('color', ('//html', _parser._color)),
            ('prices', ('//html', _parser._prices)),
        ])
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )
