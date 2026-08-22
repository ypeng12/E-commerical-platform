from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import re
from utils.cfg import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        try:
            for script in checkout.extract():
                data = json.loads(script)
                if data.get('@type') == 'Product':
                    item['tmp'] = data
                    return False  # assume in stock
            return True
        except Exception:
            return True

    def _sku(self, res, item, **kwargs):
        tmp = item.get('tmp', {})
        # 优先用图片URL中的10位数字做SKU
        img_url = tmp.get('image', '')
        sku = ''
        if img_url:
            m = re.search(r'/(\d{10})_', img_url)
            if m:
                sku = m.group(1)
        # 兜底：取tmp['sku'] 或原始sku只取前10位
        if not sku:
            sku = str(tmp.get('sku', ''))
            if len(sku) > 10:
                sku = sku[:10]
        # Fallback: 从页面文本搜 sku_number
        if not sku or sku == 'UNKNOWN':
            text = ''.join(res.extract())
            match = re.search(r'"sku_number"\s*:\s*"(\d{10,})"', text)
            if match:
                sku = match.group(1)[:10]
        if not sku:
            sku = 'UNKNOWN'
        item['sku'] = sku

        item['name'] = tmp.get('name', '').upper()
        brand = tmp.get('brand', {})
        item['designer'] = brand.get('name', '').upper() if isinstance(brand, dict) else str(brand).upper()
        item['description'] = tmp.get('description', '')

    def _images(self, res, item, **kwargs):
        images = item['tmp'].get('image', [])
        if isinstance(images, str):
            images = [images]
        item['images'] = images
        item['cover'] = images[0] if images else ''

    def _prices(self, res, item, **kwargs):
        try:
            text = ''.join(res.extract())
            sale = re.search(r'"list_price"\s*:\s*"([\d\.]+)"', text)
            msrp = re.search(r'"msrp"\s*:\s*"([\d\.]+)"', text)
            if sale:
                item['saleprice'] = float(sale.group(1))
            if msrp:
                item['listprice'] = float(msrp.group(1))
            if not item.get('listprice'):
                item['listprice'] = item.get('saleprice')
        except Exception:
            item['listprice'] = item.get('saleprice')

    def _sizes(self, res, item, **kwargs):
        raw = res.extract()
        sizes = [s.strip() for s in raw if s.strip()]
        item['sizes'] = sizes

    def _color(self, res, item, **kwargs):
        colors = res.extract()
        clean = [c.strip() for c in colors if c.strip()]
        item['color'] = ', '.join(clean)

_parser = Parser()

class Config(MerchantConfig):
    name = 'ruelala'
    merchant = 'RueLaLa'
    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('checkout', ('//script[@type="application/ld+json"]/text()', _parser._checkout)),
            ('sku', ('//html', _parser._sku)),
            ('images', ('//html', _parser._images)),
            ('prices', ('//html', _parser._prices)),
            ('sizes', ('//button[contains(@class,"sku-size")]/text()', _parser._sizes)),
            ('color', ('//input[contains(@class,"sku-color")]/@data-display_value', _parser._color)),
        ])
    )
    countries = dict(
        US=dict(language='EN', currency='USD')
    )
