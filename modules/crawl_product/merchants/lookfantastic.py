from collections import OrderedDict

from scrapy import Selector
from . import MerchantConfig, MerchantParser
import json
import re

class Parser(MerchantParser):

    def _extract_defaultvariant(self, html):
        m = re.search(r'const\s+defaultVariant\s*=\s*({.*?});', html, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                try:
                    return json.loads(m.group(1).replace("'", '"'))
                except Exception:
                    pass
        return {}

    def _sku(self, res, item, **kwargs):
        html = res.get()
        # 1. 先用 window.__product_id__ 正则
        m = re.search(r'window\.__product_id__\s*=\s*"?(?P<sku>\d+)"?;', html)
        if m:
            item['sku'] = m.group('sku')
            return
        # 2. fallback: defaultVariant
        vdata = self._extract_defaultvariant(html)
        if 'sku' in vdata:
            item['sku'] = str(vdata['sku'])
            return
        # 3. fallback: productsObj
        data = self._extract_productsobj(html)
        if data:
            item['sku'] = str(list(data.keys())[0])
        else:
            item['sku'] = 'UNKNOWN'

    def _name(self, res, item, **kwargs):
        html = res.get()
        vdata = self._extract_defaultvariant(html)
        if 'title' in vdata:
            item['name'] = vdata.get('title', '').strip() or 'No name'
            return
        # fallback: productsObj
        data = self._extract_productsobj(html)
        sku = item.get('sku', '')
        product_data = data.get(sku) or (data[list(data.keys())[0]] if data else {})
        item['name'] = product_data.get('item_name', '').strip() or 'No name'

    def _designer(self, res, item, **kwargs):
        html = res.get()
        vdata = self._extract_defaultvariant(html)
        # defaultVariant 没有品牌，用 productsObj
        data = self._extract_productsobj(html)
        sku = item.get('sku', '')
        product_data = data.get(sku) or (data[list(data.keys())[0]] if data else {})
        item['designer'] = product_data.get('item_brand', '').strip() or 'UNKNOWN'

    def _prices(self, res, item, **kwargs):
        html = res.get()
        vdata = self._extract_defaultvariant(html)
        # 优先 defaultVariant price
        if vdata.get("price") and vdata["price"].get("price") and "amount" in vdata["price"]["price"]:
            try:
                item['saleprice'] = float(vdata["price"]["price"]["amount"])
            except Exception:
                item['saleprice'] = 0.0
        else:
            item['saleprice'] = 0.0
        if vdata.get("price") and vdata["price"].get("rrp") and "amount" in vdata["price"]["rrp"]:
            try:
                item['listprice'] = float(vdata["price"]["rrp"]["amount"])
            except Exception:
                item['listprice'] = 0.0
        else:
            item['listprice'] = 0.0
        # fallback: productsObj
        if item['listprice'] == 0.0 or item['saleprice'] == 0.0:
            data = self._extract_productsobj(html)
            sku = item.get('sku', '')
            product_data = data.get(sku) or (data[list(data.keys())[0]] if data else {})
            try:
                item['listprice'] = item['listprice'] or float(product_data.get('price', 0.0)) or 0.0
                item['saleprice'] = item['saleprice'] or float(product_data.get('value', 0.0)) or 0.0
            except Exception:
                pass

    def _extract_productsobj(self, html):
        m = re.search(r'<script[^>]+data-track="productVisit"[^>]*>([\s\S]*?)</script>', html, re.S)
        if m:
            script = m.group(1)
            m2 = re.search(r'productsObj\s*=\s*({.*?})\s*;', script, re.S)
            if m2:
                try:
                    return json.loads(m2.group(1))
                except Exception:
                    try:
                        return json.loads(m2.group(1).replace("'", '"'))
                    except Exception:
                        pass
        m = re.search(r'productsObj\s*=\s*({.*?})\s*;', html, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                try:
                    return json.loads(m.group(1).replace("'", '"'))
                except Exception:
                    pass
        return {}

    def _images(self, res, item, **kwargs):
        html = res.get()
        sel = Selector(text=html)

        # 先从 defaultVariant 拿
        vdata = self._extract_defaultvariant(html)
        images = []
        if isinstance(vdata, dict) and vdata.get('images') and isinstance(vdata['images'], list):
            for img in vdata['images']:
                if isinstance(img, dict) and img.get('original'):
                    images.append(img['original'])
                elif isinstance(img, str):
                    images.append(img.strip())

        # 兜底1：og:image
        if not images:
            og_img = (sel.xpath('//meta[@property="og:image"]/@content').get() or '').strip()
            if og_img:
                images.append(og_img)

        # 兜底2：<script> const image = "..." ;
        if not images:
            m_img = re.search(r'const\s+image\s*=\s*["\']([^"\']+)["\']\s*;', html)
            if m_img:
                images.append(m_img.group(1).strip())

        # 去重并落盘
        seen, deduped = set(), []
        for u in images:
            if u and u not in seen:
                deduped.append(u)
                seen.add(u)

        item['images'] = deduped
        item['cover'] = deduped[0] if deduped else ''
        return deduped

    def _url(self, res, item, **kwargs):
        html = res.get()
        sel = Selector(text=html)

        # 优先 og:url
        url = (sel.xpath('//meta[@property="og:url"]/@content').get() or '').strip()

        # 兜底：<script> const url = "..." ;
        if not url:
            m = re.search(r'const\s+url\s*=\s*["\']([^"\']+)["\']\s*;', html)
            if m:
                url = m.group(1).strip()

        item['url'] = url
        return url

    def _cover(self, res, item, **kwargs):
        imgs = item.get('images') or []
        return imgs[0] if imgs else ''

    def _description(self, res, item, **kwargs):
        html = res.get()
        m = re.search(r'const\s+defaultVariant\s*=\s*({.*?});', html, re.S)
        if m:
            try:
                data = json.loads(m.group(1))
                content_list = data.get('content', [])
                for c in content_list:
                    if c.get('key') == 'synopsis':
                        value = c.get('value', {}).get('richContentListValue', [])
                        if value and value[0].get('content'):
                            raw_html = value[0]['content'][0].get('content', '')
                            clean = re.sub(r'<[^>]+>', '', raw_html).strip()
                            item['description'] = re.sub(r'\s+', ' ', clean)
                            return
            except:
                pass
        item['description'] = ''

    def _sizes(self, res, item, **kwargs):
        html = res.get()
        sel = Selector(text=html)

        seen = set()
        sizes = []

        # 这里假设 Lookfantastic 有鞋/衣服时才会有 select
        options = sel.xpath('//select[@id="pdpSizeDropdown"]/option[not(@disabled)]/text()').getall()
        for opt in options:
            opt = opt.strip()
            if '-' in opt:
                size = opt.split('-')[0].strip()
                if size not in seen:
                    sizes.append(size)
                    seen.add(size)

        # if not found size need to return blank
        if not sizes:
            item['originsizes'] = ''
            item['parsedsizes'] = ''
            item['sizes'] = ''
            item['size_prices'] = {}

        else:

            # I didn't found any product have size 
            # if found need fix this line

            item['parsedsizes'] = ';'.join(sizes)
            item['sizes'] = sizes

_parser = Parser()

class Config(MerchantConfig):
    name = 'lookfantastic'
    merchant = 'Lookfantastic'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('sku', ('//html', _parser._sku)),
            ('name', ('//html', _parser._name)),
            ('designer', ('//html', _parser._designer)),
            ('description', ('//html', _parser._description)),
            ('prices', ('//html', _parser._prices)),
            ('url', ('//html', _parser._url)),
            ('images', ('//html', _parser._images)),
            ('cover', ('//html', _parser._cover)),
            ('color', ('//html', _parser._color)),
            ('sizes', ('//html', _parser._sizes)),
        ])
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )
