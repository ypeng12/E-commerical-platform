from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        data = json.loads(res.extract_first())
        sold_out = data['offers']['availability']
        item['tmp'] = data
        if 'InStock' not in sold_out:
            return True
        else:
            return False

    def _name(self,res,item,**kwargs):
        item['name'] = item['tmp']['name']
        item['designer'] = item['tmp']['brand']['name']

        item['description'] = item['tmp']['description']

    def _prices(self, res, item, **kwargs):
        saleprice = res.xpath('./span[@class="price-value"]/span/text()').extract_first()
        listprice = res.xpath('.//span[contains(@class,"strike-through")]/span/@content').extract_first()
        item['originlistprice'] = ("$" + listprice) if listprice else saleprice
        item['originsaleprice'] = saleprice
        

    def _parse_multi_items(self,response,item,**kwargs):
        json_datas = response.xpath('//div[contains(@class,"color-style")]/button[@data-attr="style-value"]')
        sizes_json1 = json.loads(response.xpath('//script[contains(text(),"window.productInventory")]/text()').extract_first().split(' = ')[-1].rsplit(';',1)[0])
        sizes_json2 = json.loads(response.xpath('//script[contains(text(),"productInfo[")]/text()').extract_first().split(' = ')[-1].rsplit(';',1)[0])
        all_size_key = sizes_json1['variants']
        instock_sizes = []
        for size_key in all_size_key:
            if all_size_key[size_key]['status'] == 'IN_STOCK':
                instock_sizes.append(size_key)
        all_sizes_style = sizes_json2['variants']
        color_datas = json_datas.xpath('./@aria-label').extract()
        color_ids = json_datas.xpath('./span/@data-attr-value').extract()

        for color,code in zip(color_datas,color_ids):
            item_color = deepcopy(item)
            item_color['color'] = color.split('Select Style')[1].strip()
            item_color['sku'] = code
            availsizes = []
            for style_id in all_sizes_style:
                if style_id['style'] == code:
                    if style_id['id'] in instock_sizes:
                        if 'width' in style_id:
                            availsizes.append(style_id['size'] + ':' + style_id['width'])
                        else:
                            availsizes.append(style_id['size'])
            item_color['originsizes'] = availsizes
            self.sizes(availsizes, item_color, **kwargs)
            images = response.xpath('//div[contains(@class,"color-style")]/button/span[@data-attr-value="{}"]/@style'.format(code)).extract_first().split('url(')[1].rsplit(')',1)[0]
            item_color['images'] = [images.split('?')[0]]
            item_color['cover'] = item_color['images'][0]

            yield item_color

    def _parse_images(self,response,**kwargs):
        image_code = response.xpath('//div[@class="color-style"]/button[@data-attr="style-value"]/span/@data-attr-value').extract()
        if len(image_code) == 1:
            images_li = []
            images = response.xpath('//div[contains(@class,"carousel-item zoom-image-js")]/picture/source[1]/@data-srcset').extract()
            for image in images:
                image = image.split('?')[0]
                if image not in images_li:
                    images_li.append(image)
            return images_li
        else:
            for code in image_code:
                images = response.xpath('//div[@class="color-style"]/button/span[@data-attr-value="{}"]/@style'.format(code)).extract_first().split('url(')[1].rsplit(')',1)[0]
                return [images.split('?')[0]]

    def _page_num(self,pages,**kwargs):
        return 1

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(starts='',ends='')
        return url

_parser = Parser()

class Config(MerchantConfig):
    name = "newbalance"
    merchant = "New Balance"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = ('//div[contains(@class,"products-viewed text-center")]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="image-container"]',
            designer = 'newbalance',
            link = './a/@href',
        ),
        product = OrderedDict([
            ('checkout', ('//script[@type="application/ld+json"][contains(text(),"#product")]/text()', _parser.checkout)),
            ('name', ('//html', _parser.name)),
            ('description', '//div[@class="b-product_long_description"]/text()'),
            ('images', ('//html', _parser.images)),
            ('prices', ('//div[contains(@class,"prices")]/div', _parser.prices)),
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
               "https://www.newbalance.com/women/accessories/socks/?start={start}&sz={ends}",
               "https://www.newbalance.com/women/accessories-and-gear/fitness-gear/?start={start}&sz={ends}",
               "https://www.newbalance.com/women/accessories/Hats-and-Gloves/?start={start}&sz={ends}",
               "https://www.newbalance.com/women/accessories/Sports-Recovery/?start={start}&sz={ends}",
               "https://www.newbalance.com/women/accessories-and-gear/masks/?start={start}&sz={ends}"
                ],
            b = [
                "https://www.newbalance.com/women/accessories/Bags/?start={start}&sz={ends}",
                ],
            c = [
                "https://www.newbalance.com/women/clothing/all-clothing/?start={start}&sz={ends}"
            ],
            s = [
                "https://www.newbalance.com/women/shoes/all-shoes/?start={start}&sz={ends}"
            ],
        ),
        m = dict(
            a = [
                "https://www.newbalance.com/men/accessories-and-gear/?start={start}&sz={ends}"
            ],
            b = [
                "https://www.newbalance.com/men/accessories/Bags/?start={start}&sz={ends}"
            ],
            c = [
                "https://www.newbalance.com/men/clothing/all-clothing/?start={start}&sz={ends}"
            ],
            s = [
                "https://www.newbalance.com/men/shoes/all-shoes/?start={start}&sz={ends}",
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
        ),
    )