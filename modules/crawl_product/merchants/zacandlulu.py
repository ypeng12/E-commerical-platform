from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if 'sold out' not in checkout.extract_first().strip().lower():
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_json = data.extract_first()
        return 2

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=', '?p=%s'%i)
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img.split("?")[0]
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, res, item, **kwargs):
        sizes_li = []
        sizes = res.extract()
        for size in sizes:
            if 'sold out' not in size.strip().lower():
                sizes_li.append(size.split('/')[0].strip().split('-')[0])
        item['originsizes'] = sizes_li

    def _prices(self, res, item, **kwargs):
        oprices = json.loads(res.extract_first().split('productData: ')[1].split('LBConfigs.cart = ')[0].strip().split('variantID:')[0].strip()[0:-1])
        saleprice = str(oprices['price_max'])
        ori_listprice = str(oprices['compare_at_price_max'])
        listprice = ori_listprice if ori_listprice != "0" else saleprice

        item['originlistprice'] = str(float(listprice[0:-2] + '.' + listprice[-2:]))
        item['originsaleprice'] = str(float(saleprice[0:-2] + '.' + saleprice[-2:]))

        color = oprices['variants'][0]['option2']
        item['color'] = color.upper() if color else ''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product_photo"]/a/img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'zacandlulu'
    merchant = 'Zac & Lulu'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"var boostPFSAppConfig = ")]',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@data-product-item]/article[@class="productitem"]',
            designer = 'zacandlulu',
            link = './a/@href'
            ),
        product = OrderedDict([
        	('checkout', ('////span[@class="atc-button--text"]/text()', _parser.checkout)),
            ('sku','//div[@id="shopify-product-reviews"]/@data-id'),
            ('name','//div[@class="product-details"]/h1[@class="product-title"]/text()'),
            ('images',('//*[@data-media-type="image"]/@data-zoom',_parser.images)), 
            ('designer','//div[@class="product-details"]/div[@class="product-vendor"]/a/text()'),
            ('description', ('//div[@class="product-description rte"]//text()',_parser.description)),
            ('sizes',('//select[@class="form-options no-js-required"]//option/text()',_parser.sizes)),
            ('prices', ('//script[contains(text(),"var LBConfigs = window.LBConfigs")]', _parser.prices)),
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
        m = dict(
        ),
        f = dict(
            s = [
            	"https://zacandlulu.com/collections/womens-footwear?page=",
            ],
        ),
        b = dict(
            a = [
                "https://zacandlulu.com/collections/boys-designer-accessories?page=",
                "https://zacandlulu.com/collections/boys-designer-hats?page="
            ],
            c = [
                "https://zacandlulu.com/collections/boys-designer-coats-jackets?page=",
                "https://zacandlulu.com/collections/boys-designer-shorts?page=",
                "https://zacandlulu.com/collections/boys-designer-t-shirts-tops?page=",
                "https://zacandlulu.com/collections/boys-designer-tracksuits?page=",
                "https://zacandlulu.com/collections/boys-designer-trousers?page="
            ],
            s = [
                "https://zacandlulu.com/collections/boys-designer-shoes?page="
            ]
        ),
        g = dict(
            a = [
                "https://zacandlulu.com/collections/girls-accessories?page=",
            ],
            c = [
                "https://zacandlulu.com/collections/girls-tops?page=",
                "https://zacandlulu.com/collections/girls-dresses?page=",
                "https://zacandlulu.com/collections/girls-trousers?page=",
                "https://zacandlulu.com/collections/girls-coats-jackets?page=",
                "https://zacandlulu.com/collections/girls-playsuits-and-jumpsuits?page=",
                "https://zacandlulu.com/collections/girls-skirts?page=",
                "https://zacandlulu.com/collections/girls-shorts-1?page="
            ],
            s = [
                "https://zacandlulu.com/collections/girls-shoes?page="
            ],
        ),
        u = dict(
            h = [
                "https://zacandlulu.com/collections/home?page=",
                "https://zacandlulu.com/collections/apron?page=",
                "https://zacandlulu.com/collections/bed-linen?page=",
                "https://zacandlulu.com/collections/tablewear?page=",
                "https://zacandlulu.com/collections/lighting?page="
            ],
        ),
        i = dict(
            a = [
                "https://zacandlulu.com/collections/designer-baby-accessories?page=",
                "https://zacandlulu.com/collections/baby-gifts?page=",
                "https://zacandlulu.com/collections/baby-play?page=",
                "https://zacandlulu.com/collections/strollers?page="
            ],
            c = [
                "https://zacandlulu.com/collections/designer-babysuits?page=",
                "https://zacandlulu.com/collections/designer-baby-coats-jackets?page=",
                "https://zacandlulu.com/collections/baby-dresses-and-skirts?page=",
                "https://zacandlulu.com/collections/designer-baby-tops?page=",
                "https://zacandlulu.com/collections/designer-baby-trousers-shorts?page=",
                "https://zacandlulu.com/collections/girls-skirts?page=",
                "https://zacandlulu.com/collections/girls-shorts-1?page="
            ],
            s = [
                "https://zacandlulu.com/collections/baby-designer-shoes?page="
            ],
        ),
    )

    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD'
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        )
    )