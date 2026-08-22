import re
import requests
import json
import math
from collections import OrderedDict

from . import MerchantConfig, MerchantParser


list_urls = dict(
        f=dict(
            c=[
                'https://www.senser.net/collections/womens-clothing'
            ],
            s=[
                'https://www.senser.net/collections/womens-shoes'
            ],
            b=[
                'https://www.senser.net/collections/womens-bags'
            ],
            a=[
                'https://www.senser.net/collections/womens-accessories'
            ]
        ),
        m=dict(
            c=[
                'https://www.senser.net/collections/mens-clothing'
            ],
            s=[
                'https://www.senser.net/collections/mens-shoes'
            ],
            b=[
                'https://www.senser.net/collections/mens-bags'
            ],
            a=[
                'https://www.senser.net/collections/mens-accessories'
            ]
        ),
        b=dict(
            c=[
                'https://www.senser.net/collections/kids-boys/clothing'
            ],
            s=[
                'https://www.senser.net/collections/kids-boys/shoes'
            ],
            a=[
                'https://www.senser.net/collections/kids-boys/accessories'
            ]
        ),
        g=dict(
            c=[
                'https://www.senser.net/collections/kids-girls/clothing'
            ],
            s=[
                'https://www.senser.net/collections/kids-girls/shoes'
            ],
            a=[
                'https://www.senser.net/collections/kids-girls/accessories'
            ]
        ),
        i=dict(
            c=[
                'https://www.senser.net/collections/kids-babys/clothing'
            ],
            s=[
                'https://www.senser.net/collections/kids-babys/shoes'
            ],
            a=[
                'https://www.senser.net/collections/kids-babys/accessories'
            ]
        ),
    )


class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        """检测是否有库存"""
        if "add to" in res.extract_first().lower():
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        """获取商品的sku"""
        if 'src' in kwargs.keys() and kwargs['src']:
            sku = re.findall(r'\b\d{15}\b', kwargs['src'])[0]
        else:
            sku = re.findall(r'\b\d{15}\b', item['url'])[0]
        if sku.isdigit():
            item['sku'] = sku
        else:
            item['sku'] = ''

    def _name(self, res, item, **kwargs):
        """获取商品名称、品牌、图片、颜色、描述"""
        url = f"https://app.sensershop.com/imappusa/usa/spu/detail/get?saleSpuId={item['sku']}"
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            product_data = response.json()['data']

            item['designer'] = product_data['basic']['brandName']
            item['name'] = product_data['basic']['spuName']
            item['images'] = product_data['basic']['coverImgs']
            item['color'] = product_data['properties'][3]['spuPropertyValue']
            item['description'] = product_data['properties'][-1]['spuPropertyValue']

    def _sizes(self, res, item, **kwargs):
        """获取商品型号"""
        url = f"https://app.sensershop.com/imappusa/usa/spu/detail/price?saleSpuId={item['sku']}"
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            product_data = response.json()['data']['itemList']
            item['tmp'] = product_data
            sizes = []
            for i in product_data:
                size = i['size']
                if '-' in size:
                    size = size.replace('-', '')
                sizes.append(size)
            item['originsizes'] = sizes

    def _prices(self, res, item, **kwargs):
        """获取商品价格"""
        listprice = 0
        saleprice = 0
        for i in item['tmp']:
            if i['totalPrice'] > saleprice:
                saleprice = i['totalPrice']
                listprice = saleprice
            if i['underlinedPrice']:
                if i['underlinedPrice'] > listprice:
                    listprice = i['underlinedPrice']
        item['originlistprice'] = str(listprice)
        item['originsaleprice'] = str(saleprice)

    def _page_num(self, data, **kwargs):
        """获取列表的页码"""
        uri = list_urls[kwargs['gender']][kwargs['category']][0].split('net/')[1]
        url = "https://app.sensershop.com/imappusa/usa/spu/aggregation"

        headers = {
            'baseparams': str({"regionType":"usa","requestFrom":"PC","channelId":"8101","uri":f"/{uri}","browserId":"365356354670175","fingerprint":"2938120786413412823","country":"usa","fromUrl":""}),
            'content-type': 'application/json',
            'token': '035b7588-490e-4104-a6ed-0f8a38a85281',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        data = json.dumps({
            "pageNo": 1,
            "pageSize": 96,
            "orderBy": 1,
            "isInitPage": True
        })

        response = requests.request("POST", url, headers=headers, data=data)
        if response.status_code == 200:
            total_count = response.json()['data']['totalCount']
            page_num = math.ceil(total_count/96)
        page_num = 1
        return page_num

    def _parse_item_url(self, response, **kwargs):
        """获取商品链接"""
        pageNO = int(re.findall(r'\b\d{15}\b', response.url)[0])
        res_url = re.sub(r'\d+$', '', response.url)
        uri = res_url.split('net/')[1]
        url = 'https://app.sensershop.com/imappusa/usa/spu/page'
        headers = {
            'baseparams': str({"regionType": "usa", "requestFrom": "PC", "channelId": "8101", "uri": f"/{uri}",
                               "browserId": "365356354670175", "fingerprint": "2938120786413412823", "country": "usa",
                               "fromUrl": ""}),
            'content-type': 'application/json',

            'token': '035b7588-490e-4104-a6ed-0f8a38a85281',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        data = json.dumps({
            "pageNo": pageNO,
            "pageSize": 96,
            "orderBy": 1,
            "isInitPage": True
        })
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            pro_list = response.json()['data']['list']
            for i in pro_list:
                designer = i['brandName']
                sku = i['saleSpuId']
                pro_url = f'https://www.senser.net/products/{sku}'
                yield pro_url, designer


_parser = Parser()


class Config(MerchantConfig):
    name = "senser"
    merchant = "SENSER"

    path = dict(
        # 列表数据配置
        plist=dict(
            page_num=('//html', _parser.page_num),
            parse_item_url=_parser.parse_item_url,
        ),
        # 商品数据配置
        product=OrderedDict([
            ('checkout', (
            '//button[@class="button add-to-bag-btn"]/div[@class="button-content"]/span/text()',
            _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('name', ('//html', _parser.name)),
            ('sizes', ('//html', _parser.sizes)),
            ('price', ('//html', _parser.prices)),
        ]),
    )

    list_urls = list_urls

    countries = dict(
        US=dict(
            language='EN',
            area='US',
            currency='USD',
        ),
        AU=dict(
            currency='AUD',
            discurrency='USD',
            # vat_rate=1.061,
        ),
    )

