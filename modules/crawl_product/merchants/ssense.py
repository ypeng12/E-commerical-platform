from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import re
from parsel import Selector  
from utils.size_helper import parse_sizes
from collections import OrderedDict

class Parser(MerchantParser):
    def _tmp(self, res, item, **kwargs):
        # 只做数据中转，不做最终输出
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
        item['sku'] = item['tmp'].get('sku', 'UNKNOWN')

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp'].get('name', '').upper()

    def _designer(self, res, item, **kwargs):
        brand = item['tmp'].get('brand', {})
        item['designer'] = brand.get('name', '').upper() if isinstance(brand, dict) else (brand.upper() if brand else '')
    def _url(self, res, item, **kwargs):
        # 优先 og:url，其次 canonical
        url = res.xpath('//meta[@property="og:url"]/@content').get()
        if not url:
            url = res.xpath('//link[@rel="canonical"]/@href').get()
        item['url'] = (url or '').strip()
        
    def _description(self, res, item, **kwargs):
        import re
        # 只从 <meta name="description" content="..."> 取
        desc = res.xpath('//meta[@name="description"]/@content').get() or ''
        # 规范空白
        desc = desc.replace('\r', ' ').replace('\n', ' ').replace('\xa0', ' ')
        desc = re.sub(r'\s+', ' ', desc).strip()
        item['description'] = desc


    def _images(self, res, item, **kwargs):
        # 1) 先从 OG/Twitter 取图
        metas = res.xpath(
            '//meta[@property="og:image"]/@content'
            ' | //meta[@name="twitter:img:src"]/@content'
        ).getall()
        collected = [m.strip() for m in metas if m and m.strip()]

        # 2) 再用 JSON-LD 的 image 兜底（支持 str/list）
        img_ld = item['tmp'].get('image')
        if isinstance(img_ld, str) and img_ld.strip():
            collected.append(img_ld.strip())
        elif isinstance(img_ld, list):
            collected.extend([x.strip() for x in img_ld if isinstance(x, str) and x.strip()])

        # 3) 去重且保持顺序，并写回 images / cover
        images = list(OrderedDict.fromkeys(collected))
        item['images'] = images
        item['cover']  = images[0] if images else ''

    def _color(self, res, item, **kwargs):
        # 从 description 提取 Supplier color，或留空
        desc = item['tmp'].get('description', '')
        color = ''
        m = re.search(r'Supplier color:\s*([^\n]+)', desc)
        if m:
            color = m.group(1).strip()
        item['color'] = color
    def _sizes(self, res, item, **kwargs):
        from parsel import Selector
        import re

        html = res.get() if hasattr(res, 'get') else (res or '')
        sel = Selector(text=html)

        # 1) 收集页面下拉里“可选尺码”的原始标签（保持你原有写法）
        seen = set()
        raw_sizes = []
        options = sel.xpath('//select[@id="pdpSizeDropdown"]/option[not(@disabled)]/text()').getall()
        for opt in options:
            opt = (opt or '').strip()
            if not opt:
                continue
            # 文本像 "EU 31 - Out of stock" / "EU 31"
            size_part = opt.split('-')[0].strip()
            if size_part and size_part not in seen:
                seen.add(size_part)
                raw_sizes.append(size_part)

        # 没有尺码，清空四件套
        if not raw_sizes:
            item['originsizes'] = ''
            item['parsedsizes'] = ''
            item['sizes'] = ''
            item['size_prices'] = {}
            return

        # 2) 用 size_convert 的规则做映射
        try:
            # parse_sizes( item, noit_str, orig_str, ... )
            # 这里把原始标签大写后用分号拼，传两遍（noit候选/原始），由内部决定映射
            raw_labels = [s.strip().upper() for s in raw_sizes]
            raw = ';'.join(raw_labels)
            ori_all, _, _ = parse_sizes(item, raw, raw, size_standard={})
        except Exception:
            # 兜底：保持可用（noit-parsed-orig 都用原始）
            ori_all = ';'.join([f'{x}-{x}-{x}' for x in [s.strip().upper() for s in raw_sizes]])

        # 3) 只保留“页面真实存在”的尺码段，构建三件套
        raw_set = set([s.strip().upper() for s in raw_sizes])
        segs = []
        for seg in ori_all.split(';'):
            seg = seg.strip()
            if not seg:
                continue
            ps = [p.strip() for p in seg.split('-')]
            if len(ps) < 3 or not all(ps[:3]):
                continue
            noit, parsed_sz, orig = ps[0], ps[1], ps[2].upper()
            if orig not in raw_set:
                continue  # 不新增尺码
            segs.append((noit, parsed_sz, orig))

        if not segs:
            item['originsizes'] = ''
            item['parsedsizes'] = ''
            item['sizes'] = ''
            item['size_prices'] = {}
            return

        # originsizes: NOIT-PARSED-ORIG;
        item['originsizes'] = ';'.join([f'{n}-{p}-{o}' for (n, p, o) in segs]) + ';'
        # parsedsizes: 展示=第三段 ORIG（注意这里 parse_sizes 已经把 EU 去掉，通常是数字或 XS/S/...）
        parsed_list = [o for (_, _, o) in segs]
        item['parsedsizes'] = ';'.join(parsed_list) + ';'
        # sizes: 用 NOIT 统一转 ITxx
        sizes_list = [(f'IT{n}' if not str(n).upper().startswith('IT') else str(n).upper()) for (n, _, _) in segs]
        item['sizes'] = ';'.join(sizes_list) + ';'

        # 4) size_prices
        def _fmt(v):
            try:
                return f"{float(v):.2f}"
            except Exception:
                return str(v) if v is not None else ''

        # 判断服装（展示含字母）还是数字码（鞋/裤等）
        is_apparel = any(any(ch.isalpha() for ch in o) for o in parsed_list)

        # 原展示标签 -> key 的映射
        orig_to_key = {}
        if is_apparel:
            # 服装：key 用 parsedsizes（XS/S/...）
            for (_, _, o) in segs:
                orig_to_key[o] = o
        else:
            # 数字/鞋码：key 用 sizes（IT..）
            for (n, _, o) in segs:
                it_key = f'IT{n}' if not str(n).upper().startswith('IT') else str(n).upper()
                orig_to_key[o] = it_key

        # 优先逐尺码价（如果你在别处放入了 item['size_prices_raw']，键需是“原展示标签”，如 'EU 31'→parse后第三段通常是 '31'）
        per_size_raw = item.get('size_prices_raw') or {}

        # 全局价兜底（页面价）
        lp_default = item.get('listprice')
        sp_default = item.get('saleprice')
        if lp_default in (None, '') and sp_default not in (None, ''):
            lp_default = sp_default
        if sp_default in (None, '') and lp_default not in (None, ''):
            sp_default = lp_default

        size_prices = {}

        if per_size_raw:
            # 仅写“确实有逐尺码价”的尺码
            for orig_label, prices in per_size_raw.items():
                k = orig_to_key.get(str(orig_label).upper())
                if not k:
                    # 有些站原标签可能带 "EU 31"，而第三段是 "31"；尝试把 'EU ' 去掉再匹配
                    k = orig_to_key.get(str(orig_label).upper().replace('EU ', '').strip())
                if not k:
                    continue
                lp = prices.get('list_price', lp_default)
                sp = prices.get('sale_price', sp_default if sp_default is not None else lp)
                size_prices[k] = {'list_price': _fmt(lp), 'sale_price': _fmt(sp)}
        else:
            # 没有逐尺码价：用全局价给“当页存在”的尺码赋值（不新增）
            lp = _fmt(lp_default) if lp_default not in (None, '') else ''
            sp = _fmt(sp_default) if sp_default not in (None, '') else lp
            for k in orig_to_key.values():
                size_prices[k] = {'list_price': lp, 'sale_price': sp}

        item['size_prices'] = size_prices


    def _prices(self, res, item, **kwargs):
        offer = item['tmp'].get('offers', {})
        try:
            price = offer.get('price', 0.0)
            item['saleprice'] = float(price)
            item['listprice'] = float(price)
        except Exception:
            item['saleprice'] = 0.0
            item['listprice'] = 0.0

    def _related_products(self, res, item, **kwargs):
        return

_parser = Parser()

class Config(MerchantConfig):
    name = 'ssense'
    merchant = 'SSENSE'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('tmp', ('//html', _parser._tmp)),
            ('sku', ('//html', _parser._sku)),
            ('name', ('//html', _parser._name)),
            ('url', ('//html', _parser._url)),          # ← 新增
            ('images', ('//html', _parser._images)),
            ('designer', ('//html', _parser._designer)),
            ('description', ('//html', _parser._description)),
            ('color', ('//html', _parser._color)),
            ('prices', ('//html', _parser._prices)),
            ('sizes', ('//html', _parser._sizes)),
           
        ])
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )

def clean_output(item):
    # 只保留你要的主字段，不包括 images、cover、tmp
    main_keys = [
        'gender', 'merchant', 'crawler_name', 'category', 'country', 'area', 'language', 'currency', 'opflag',
        'sku', 'name', 'designer', 'color', 'description', 'sizes', 'saleprice', 'listprice'
    ]
    return {k: v for k, v in item.items() if k in main_keys}

