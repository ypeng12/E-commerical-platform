from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from utils.cfg import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        try:
            raw = checkout.extract_first()
            data = json.loads(raw)
            item['tmp'] = data
            offers = data.get('offers', [])
            if isinstance(offers, list) and offers:
                availability = offers[0].get('availability', '').lower()
            else:
                availability = offers.get('availability', '').lower() if isinstance(offers, dict) else ''
            return 'instock' not in availability
        except Exception:
            return True  # assume OOS if parsing fails

    def _sku(self, res, item, **kwargs):
        base_sku = res.xpath('//meta[@name="photorank:tags"]/@content').get() or str(item.get('tmp', {}).get('productID', '')).strip()
        data = item.get('tmp', {})
        offers = data.get('offers', [])
        if isinstance(offers, dict):
            offers = [offers]
        colors = set()
        for offer in offers:
            offered = offer.get('itemOffered', {})
            color = offered.get('color', '').strip().upper()
            if color:
                colors.add(color)
        if len(colors) == 1:
            final_sku = f"{base_sku}{list(colors)[0]}"
            color_field = list(colors)[0]
        elif len(colors) > 1:
            final_sku = f"{base_sku}MULTI"
            color_field = ";".join(colors)
        else:
            final_sku = base_sku + "UNKNOWN"
            color_field = ""
        item['sku'] = final_sku
        item['color'] = color_field

        item['merchant'] = 'Macys'
        item['designer'] = data.get('brand', {}).get('name', '').upper() if data.get('brand', {}) else ''
        item['name'] = data.get('name', '')
        item['description'] = data.get('description', '')
        item['category'] = 'c'
        item['area'] = 'US'
        item['country'] = 'US'
        item['currency'] = 'USD'
        item['language'] = 'EN'
        item['gender'] = 'f'
        item['opflag'] = 'update'
        item['jobid'] = None
        url_path = data.get('url', '')
        if url_path and not url_path.startswith('http'):
            url_path = "https://www.macys.com" + url_path
        item['url'] = url_path if url_path else ''
        # 不清理 tmp！

    def _images(self, res, item, **kwargs):
        images = item.get('tmp', {}).get('image', [])
        if isinstance(images, str):
            images = [images]
        if not images:
            # 兜底从 meta 取
            images = res.xpath('//meta[@property="og:image"]/@content').getall() or []
        item['images'] = images
        item['cover'] = images[0] if images else ''
        # 不清理 tmp！

    def _prices(self, res, item, **kwargs):
        offers = item.get('tmp', {}).get('offers', [])
        # 若offers为str，再解码一次（极端情况）
        if isinstance(offers, str):
            try:
                offers = json.loads(offers)
            except Exception:
                offers = []
        # print("DEBUG offers =", offers)
        price = None
        if isinstance(offers, list) and offers:
            price = offers[0].get('price')
        elif isinstance(offers, dict):
            price = offers.get('price')
        # print("DEBUG price =", price)
        try:
            if price is not None and price != '':
                item['listprice'] = float(price)
                item['saleprice'] = float(price)
            else:
                item['listprice'] = ''
                item['saleprice'] = ''
        except Exception as e:
            print("DEBUG price cast error:", e)
            item['listprice'] = price or ''
            item['saleprice'] = price or ''
        if 'tmp' in item:
            del item['tmp']

_parser = Parser()

class Config(MerchantConfig):
    name = 'macys'
    merchant = 'Macys'
    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('checkout', ('//script[@type="application/ld+json" and contains(text(), "Product")]/text()', _parser._checkout)),
            ('sku', ('//html', _parser._sku)),
            ('images', ('//html', _parser._images)),
            ('prices', ('//html', _parser._prices)),
        ]),
    )
    countries = dict(
        US=dict(language='EN', currency='USD')
    )
