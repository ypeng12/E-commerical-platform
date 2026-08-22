from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        sold_out = []
        data = json.loads(res.xpath('//script[@type="application/ld+json"]/text()').extract_first().strip())
        item['tmp'] = data
        if 'offers' not in data.keys():
            return True
        for avail in data['offers']:
            sold_out.append(avail['availability'].lower())

        error_data = res.xpath('//h1[@class="content-header"]/text()').extract_first()
        if error_data:
            return True
        if "instock" in sold_out:
            return False
        else:
            return True

    def _name(self,res,item,**kwargs):
        item['name'] = item['tmp']['name']
        item['designer'] = 'GANNI'

        description = item['tmp']['description'].strip().split('.')
        for desc in description:
            description=re.findall(r'<li>([\s\S]+?)</li>',desc.strip())
            item['description'] = "\n".join(description)

    def _prices(self, res, item, **kwargs):
        temp_data = json.loads(res.extract_first())
        originsaleprice = temp_data['price']['dwPrice']['sales']['formatted']
        try:
            originlistprice = temp_data['price']['dwPrice']['list']['formatted']
        except:
            originlistprice = originsaleprice
        item['originsaleprice'] = originsaleprice
        item['originlistprice'] = originlistprice

    def _parse_multi_items(self,response,item,**kwargs):
        color_num = json.loads(response.xpath('//json-adapter/@product').extract_first())
        color_datas = color_num['variationAttributes'][0]['values']
        for color_data in color_datas:
            sku = color_num['productMasterId']
            item_color = deepcopy(item)
            item_color['color'] = color_data['id'].upper()
            code_tail = color_data['image']['url'].split(sku)[1].split('-')[1]
            item_color['sku'] = sku + '-' + code_tail
            item_color['images'] = [color_data['image']['url'].replace('sw=200','sw=2000')]
            item_color['cover'] = item_color['images'][0]

            sizes_url = requests.get(color_data['url'])
            size_json = json.loads(sizes_url.text)
            size_list = size_json['product']['variationAttributes'][1]
            osize = []
            for size in size_list['values']:
                if size['available']:
                    osize.append(size['id'])
            item_color['originsizes'] = osize
            self.sizes(osize, item_color, **kwargs)
            yield item_color

    def _parse_images(self,response,**kwargs):
        images_json = json.loads(response.xpath('//json-adapter/@product').extract_first())
        image_datas = images_json['variationAttributes'][0]['values']
        images = []
        for image_data in image_datas:
            if kwargs['sku'] in image_data['image']['url']:
                images.append(image_data['image']['url'])
        return images

    def _parse_num(self,pages,**kwargs):
        # pages = pages/24+1
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('&sz=1', '&sz=%s'%i)
        return url

    def _parse_item_url(self,response,**kwargs):
        item_data = response.xpath('//json-adapter/@product-search').extract_first()
        item_data = json.loads(item_data)
        for url_items in item_data['products']:
            yield url_items['url'],'designer'

_parser = Parser()


class Config(MerchantConfig):
    name = "ganni"
    merchant = "Ganni"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
        ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('name', ('//html', _parser.name)),
            ('prices', ('//json-adapter/@product', _parser.prices)),
            ]),
        image = dict(
            method = _parser.parse_images,
        ),
        look = dict(
        ),
        swatch = dict(
        ),        
    )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
               "https://www.ganni.com/us/accessories/?start=0&sz=1?"
                ],
            b = [
                "https://www.ganni.com/us/bags/?start=0&sz=1?",
                ],
            c = [
                "https://www.ganni.com/us/clothing/?start=0&sz=1?"
            ],
            s = [
                "https://www.ganni.com/us/shoes/?start=0&sz=1?"
            ],
        ),
        m = dict(
            a = [
                
            ],
            b = [
                
            ],
            c = [
                
            ],
            s = [
               
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US=dict(
            language = 'EN',
            currency = 'USD',
            country_url = '/us/',
        ),
        GB=dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/en-gb/',
        )
    )