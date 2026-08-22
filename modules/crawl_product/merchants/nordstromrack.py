from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import re
from utils.cfg import *

class Parser(MerchantParser):
    def _tmp(self, res, item, **kwargs):
        item['tmp'] = {}
        try:
            script = res.xpath('//script[@type="application/ld+json"]/text()').get()
            if script:
                data = json.loads(script.strip())
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    item['tmp'] = data
        except Exception:
            item['tmp'] = {}
    def _color(self, res, item, **kwargs):
        # 1. 优先用正则提取 "anchor*TextArea" 的 color 值
        html = ''.join(res.extract())
        colors = set()
        color_blocks = re.findall(r'"color"\s*:\s*({.*?})\s*,\s*"', html, re.S)
        for block in color_blocks:
            try:
                if not block.strip().endswith('}'):
                    block += '}'
                color_json = json.loads(block)
                for k, v in color_json.items():
                    if k.startswith('anchor') and k.endswith('TextArea') and v:
                        colors.add(v)
            except Exception:
                anchor_matches = re.findall(r'"anchor\w+TextArea"\s*:\s*"([^"]+)"', block)
                for val in anchor_matches:
                    if val:
                        colors.add(val)
        # 2. 没提取到再用 meta
        if not colors:
            color_meta = res.xpath('//meta[@name="color"]/@content').get()
            if color_meta:
                colors.add(color_meta.strip())
        # 3. 还没有的话用页面上的 color-name
        if not colors:
            color = res.xpath('//span[contains(@class, "color-name")]/text()').get()
            if color:
                colors.add(color.strip())
        item['color'] = ', '.join(sorted(colors)) if colors else ''

    def _sku(self, res, item, **kwargs):
        url = res.xpath('//meta[@property="og:url"]/@content').get()
        product_id = ''
        if url:
            m = re.search(r'/(\d+)', url)
            if m:
                product_id = m.group(1)
        color = item.get('color', '').strip()
        if product_id and color:
            item['sku'] = f"{product_id}_{color}"
        elif product_id:
            item['sku'] = product_id
        else:
            item['sku'] = 'UNKNOWN'


    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp'].get('name', '').strip()

    def _designer(self, res, item, **kwargs):
        brand = item['tmp'].get('brand', {})
        item['designer'] = brand.get('name', '').strip() if isinstance(brand, dict) else str(brand).strip()

    def _description(self, res, item, **kwargs):
        desc = item['tmp'].get('description', '')
        # 如果是 HTML 字符串，去掉标签
        if isinstance(desc, str):
            desc = re.sub(r'<.*?>', '', desc)
            item['description'] = desc.strip()
        else:
            item['description'] = ''

    def _images(self, res, item, **kwargs):
        imgs = item['tmp'].get('image', [])
        if isinstance(imgs, str):
            imgs = [imgs]
        item['images'] = imgs
        item['cover'] = imgs[0] if imgs else ''



    def _prices(self, res, item, **kwargs):
        offers = item.get('tmp', {}).get('offers', {})
        # 先取 sale price（现价）
        sale_price = offers.get('price')
        try:
            item['saleprice'] = float(sale_price) if sale_price else 0.0
        except:
            item['saleprice'] = 0.0

        # 提取 list price（原价/可比价）
        # 优先找 class 里有 fj69a 的标签（你的 HTML 示例中这个就是原价）
        list_price_text = res.xpath('//span[contains(@class, "fj69a")]/text()').re_first(r'[\$]?([\d\.]+)')
        if not list_price_text:
            # 兜底：查 class 里包含 original/regular/comparable 的
            list_price_text = res.xpath('//span[contains(@class,"original") or contains(@class,"regular") or contains(@class,"comparable")]/text()').re_first(r'[\$]?([\d\.]+)')
        if not list_price_text:
            # 再兜底：查 <del> 标签
            list_price_text = res.xpath('//del/text()').re_first(r'[\$]?([\d\.]+)')
        if list_price_text:
            try:
                item['listprice'] = float(list_price_text)
            except:
                item['listprice'] = item['saleprice']
        else:
            # 最后如果真找不到，用 saleprice 兜底
            item['listprice'] = item['saleprice']

        # 清理tmp
        item.pop('tmp', None)

    #need to fix the price size 

    def _sizes(self, res, item, **kwargs):
        sizes = []
        size_prices = {}
        scripts = res.xpath('//script[contains(text(),"optionFirstTextArea")]/text()').getall()
        for script in scripts:
            size_blocks = re.findall(r'({"anchorFirstTextArea"\s*:\s*"Size".*?"options":\s*\[.*?\][^}]*})', script, re.S)
            for block in size_blocks:
                try:
                    data = json.loads(block)
                    options = data.get("options", [])
                    for opt in options:
                        if opt.get('isAvailable'):
                            sz = opt.get('displayValue') or opt.get('optionFirstTextArea') or opt.get('value')
                            if sz and sz not in sizes:
                                sizes.append(sz)
                                # 用全局listprice/saleprice填充，不再用 0
                                size_prices[sz] = {
                                    'list_price': item.get('listprice', 0.0),
                                    'sale_price': item.get('saleprice', 0.0)
                                }
                except Exception:
                    continue
        item['sizes'] = sizes
        item['size_prices'] = size_prices


    def _related_products(self, res, item, **kwargs):
        return

_parser = Parser()

class Config(MerchantConfig):
    name = 'nordstromrack'
    merchant = 'Nordstrom Rack'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('tmp', ('//html', _parser._tmp)),
            ('color', ('//html', _parser._color)),
            ('sku', ('//html', _parser._sku)),
            ('name', ('//html', _parser._name)),
            ('designer', ('//html', _parser._designer)),
            ('description', ('//html', _parser._description)),
            ('images', ('//html', _parser._images)),
            ('prices', ('//html', _parser._prices)),
            ('sizes', ('//html', _parser._sizes)),

        ])
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )
