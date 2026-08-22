from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page = data.extract_first().split(' ')[0]
        return int(page)//60

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _sku(self, res, item, **kwargs):
        code = res.extract_first()
        item['sku'] = code if code.isdigit() else ''
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        item['images'] = images
        item['cover'] = images[0]

    def _sizes(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        data = json_data['product']['variants']
        item['tmp'] = json_data['product']
        sizes = []
        for size_key in data.keys():
            if data[size_key]['isInStock']:
                sizes.append(data[size_key]['size']['label'])
        item['originsizes'] = sizes

    def _prices(self, res, item, **kwargs):
        listprice = str(item['tmp']['price'])
        saleprice = str(item['tmp']['salePrice'])
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-image-container"]/div[@class="slider-wrap"]//span[@class="img j-zoom-link"]/@data-href').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'childrensalon'
    merchant = 'Childrensalon'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="amount"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@data-ajax-replace="product_list"]/ul[@class="products-grid"]/li',
            designer = './a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//button[@data-action="add-to-cart"]/span/span', _parser.checkout)),
            ('name','//h1[contains(@class,"product-name")][@itemprop="name"]/text()'),
            ('sku', '//div[@class="product-number info-part"]/span[@class="info-part-copy"]/text()'),
            ('designer','//span[@itemprop="brand"]/@content'),
            ('images',('//div[@class="product-image-container"]/div[@class="slider-wrap"]//span[@class="img j-zoom-link"]/@data-href', _parser.images)),
            ('description', ('//div[@class="description-text"]/p/text()', _parser.description)),
            ('sizes',('//script[@data-cs="productViewActionsConfig"]/text()', _parser.sizes)),
            ('prices', ('//div[@class="detail__price"]', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
         
            ),
        )

    list_urls = dict(
        r = dict(
            a = [
                'https://www.childrensalon.com/baby/baby-accessories?p={}'
            ],
            b = [
                'https://www.childrensalon.com/baby/baby-bags?p={}'
            ],
            c = [
                'https://www.childrensalon.com/baby/dresses-skirts?p={}'
            ],
            s = [
                'cchildrensalon.com/shoes/baby-toddler?p={}'
            ],

        ),
        g = dict(
            a = [
                "https://www.childrensalon.com/girl/accessories?p={}",
                "https://www.childrensalon.com/girl/hats?p={}"
            ],
            b = [
                "https://www.childrensalon.com/girl/bags?p={}"
            ],
            c = [
                "https://www.childrensalon.com/girl/coats-jackets?p={}",
                "https://www.childrensalon.com/girl/dresses?p={}"
            ],
            s = [
                "https://www.childrensalon.com/shoes?gender=girl&p={}",
            ],

        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            cookies = {
                '__gcc':'US',
                '__country':'US',
                'currency':'USD',
                '__cs_merch_ver4':'ver5-us',
            }
        ),
        GB = dict(
            language = 'EN',
            currency = 'GBP',
            cookies = {
                '__gcc':'US',
                '__country':'GB',
                'currency':'GBP',
                '__cs_merch_ver4':'ver5-uk-b',
            }
        )
    )

        


