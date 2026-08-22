from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import re
from utils.cfg import *

class Parser(MerchantParser):
    def _tmp(self, res, item, **kwargs):
        item['tmp'] = {}
        try:
            scripts = res.xpath('//script[@type="application/ld+json"]/text()').getall()
            for script in scripts:
                try:
                    data = json.loads(script.strip())
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        item['tmp'] = data
                        return
                except Exception:
                    continue
        except Exception:
            item['tmp'] = {}

    def _sku(self, res, item, **kwargs):
        script = res.xpath('//script[@id="__st"]/text()').get()
        sku = ''
        if script:
            try:
                match = re.search(r'__st\s*=\s*({.*?});', script, re.S)
                if match:
                    data = json.loads(match.group(1))
                    sku = str(data.get('rid', ''))
            except Exception:
                pass
        item['sku'] = sku if sku else 'UNKNOWN'

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp'].get('name', '').strip()

    def _designer(self, res, item, **kwargs):
        brand = item['tmp'].get('brand', {})
        item['designer'] = brand.get('name', '') if isinstance(brand, dict) else brand if isinstance(brand, str) else ''

    def _description(self, res, item, **kwargs):
        desc = item['tmp'].get('description', '')
        if isinstance(desc, str):
            parts = desc.split('. ')
            seen = set()
            dedup_parts = []
            for part in parts:
                if part not in seen:
                    seen.add(part)
                    dedup_parts.append(part)
            item['description'] = '. '.join(dedup_parts).strip()
        else:
            item['description'] = ''

    def _images(self, res, item, **kwargs):
        imgs = item['tmp'].get('image') or []
        if isinstance(imgs, str):
            imgs = [imgs]
        elif isinstance(imgs, dict) and 'url' in imgs:
            imgs = [imgs['url']]
        elif isinstance(imgs, dict):
            imgs = [imgs.get('image')] if 'image' in imgs else []
        item['images'] = [img['url'] if isinstance(img, dict) and 'url' in img else img for img in imgs if isinstance(img, (str, dict))]
        item['images'] = list(OrderedDict.fromkeys(item['images']))
        item['cover'] = item['images'][0] if item['images'] else ''

    def _variants(self, res, item, **kwargs):
        sizes, color_set, sku_set, variants_data = [], set(), set(), []
        script = res.xpath('//script[contains(text(),"ShopifyAnalytics") or contains(text(),"productVariants")]/text()').get()
        if script:
            try:
                json_match = re.search(r'productVariants":(\[.*?\])', script, re.S)
                if json_match:
                    raw = json_match.group(1)
                    raw = raw.replace('\n', '').replace('\t', '').replace('"', '"')
                    variants = json.loads(raw)
                    for v in variants:
                        title = v.get("title", "")
                        sku = v.get("sku", "")
                        price = v.get("price", {}).get("amount")
                        available = v.get("available", True)
                        size, color = "", ""
                        if "/" in title:
                            size, color = [x.strip() for x in title.split('/', 1)]
                        else:
                            size = title.strip()
                        if size:
                            sizes.append(size)
                        if color:
                            color_set.add(color)
                        if sku:
                            sku_set.add(sku)
                        # 价格修正
                        if price:
                            price = price.replace(',', '').replace('$', '').strip()
                            try:
                                price = float(price)
                            except Exception:
                                price = 0.0
                        else:
                            price = 0.0
                        variants_data.append({
                            "size": size,
                            "color": color,
                            "sku": sku,
                            "price": price,
                            "in_stock": available
                        })
                    item["variants_data"] = variants_data
            except Exception:
                pass

        # 用 HTML 补全所有可能的服装尺码（men/women/kids/unisex）
        sizes_json = list(OrderedDict.fromkeys(sizes))
        try:
            html_sizes = res.xpath('//fieldset[contains(@name,"Clothing Size")]//input[@type="radio"]/@value').getall()
            for s in html_sizes:
                if s not in sizes_json:
                    sizes_json.append(s)
        except Exception:
            pass
        item["sizes"] = sizes_json
        item["color"] = ', '.join(sorted(color_set))

    def _prices(self, res, item, **kwargs):
        sale = res.xpath('//span[contains(@class, "product__price--sale")]/text()').re_first(r'\$([\d,\.]+)')
        listp = res.xpath('//span[contains(@class, "product__price--compare")]/text()').re_first(r'\$([\d,\.]+)')
        if not sale:
            sale = res.xpath('//span[contains(@class, "product__price")]/text()').re_first(r'\$([\d,\.]+)')
        if not listp:
            listp = sale
        sale = sale.replace(',', '') if sale else ''
        listp = listp.replace(',', '') if listp else ''
        try:
            item['saleprice'] = float(sale) if sale else 0.0
        except Exception:
            item['saleprice'] = 0.0
        try:
            item['listprice'] = float(listp) if listp else 0.0
        except Exception:
            item['listprice'] = 0.0
        item.pop('tmp', None)

    def _related_products(self, res, item, **kwargs):
        return

_parser = Parser()

class Config(MerchantConfig):
    name = 'shopsimon'
    merchant = 'ShopSimon'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('tmp', ('//html', _parser._tmp)),
            ('variants', ('//html', _parser._variants)),
            ('sku', ('//html', _parser._sku)),
            ('name', ('//html', _parser._name)),
            ('designer', ('//html', _parser._designer)),
            ('description', ('//html', _parser._description)),
            ('images', ('//html', _parser._images)),
            ('prices', ('//html', _parser._prices)),
        ])
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )
