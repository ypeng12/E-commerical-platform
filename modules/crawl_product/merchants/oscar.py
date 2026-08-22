from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.utils import *
import re

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _color(self, res, item, **kwargs):
        json_datas = res.extract_first()
        data = json.loads(json_datas.split('productDetailsData = ')[1].rsplit(';',1)[0])
        item['color'] = data['ProductData'][0]['ColorName'].upper()
        item['description'] = data['ProductData'][0]['ProductDescription']
        item['tmp'] = data

    def _images(self, images, item, **kwargs):
        images = item['tmp']['ProductData'][0]['AlternateImages']
        imgs_li = []
        head = 'https://kwiazurecdn.azureedge.net'
        for img in images:
            img = head + img['ThumbImage']
            if img not in imgs_li:
                imgs_li.append(img)
        item['images'] = imgs_li
        item['cover'] = imgs_li[0]

    def _prices(self, res, item, **kwargs):
        originsaleprice = res.xpath('./div[@class="ourPriceDiv"]/span/text()').extract_first()
        item['originsaleprice'] = originsaleprice
        item['originlistprice'] = originsaleprice

    def _sizes(self, sizes, item, **kwargs):
        sizes_data = item['tmp']['ProductData'][0]['Variants'][0]['Choices']
        originsizes = []
        memo = ''
        for size in sizes_data:
            if size['AllowBackorders']:
                memo = ':b'
            if size['QtyOnHand']:
                originsizes.append(size['VariantName'] + memo)

        item['originsizes'] = originsizes

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="text/javascript"][contains(text(),"productDetailsData =")]/text()').extract_first().split('productDetailsData = ')[1].rsplit(';',1)[0])
        images = data['ProductData'][0]['AlternateImages']
        imgs = []
        head = 'https://kwiazurecdn.azureedge.net'
        for img in images:
            img = head + img['ThumbImage']
            if img not in imgs:
                imgs.append(img)

        return imgs
        
_parser = Parser()

class Config(MerchantConfig):
    name = 'oscar'
    merchant = 'Oscar de la Renta'

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//ul[@class="p-list preloaded"]/li/div[contains(@class,"cd_product_cr")]/div',
            designer = './a/img/@alt',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@id="cphContent_divBuyBtn"]/div[@id="btnAddToCart"]/text()', _parser.checkout)),
            ('sku', '//section[@class="product-single"]/div[@class="container"]/div/@data-parentproductid'),
            ('name', '//div[contains(@class,"product-single-info")]/h1[@class="product_name"]/span/text()'),
            ('designer', '//div[@itemprop="offers"]/span[@itemprop="seller"]/span/text()'),
            ('color', ('//script[@type="text/javascript"][contains(text(),"productDetailsData =")]/text()',_parser.color)),
            ('images', ('//html', _parser.images)),
            ('prices', ('//div[@class="price-panel"]', _parser.prices)),
            ('sizes', ('//html', _parser.sizes)),
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
        f = dict(
            a = [
                'https://www.oscardelarenta.com/shop/jewelry/?page='
            ],
            e = [
                'https://www.oscardelarenta.com/shop/beauty/?page='
            ],
            b = [
                'https://www.oscardelarenta.com/shop/handbags-%26-accessories/?page='
            ],
            c = [
                'https://www.oscardelarenta.com/shop/ready-to-wear/dresses/?page=',
                'https://www.oscardelarenta.com/shop/ready-to-wear/gowns-%26-caftans/?page=',
                'https://www.oscardelarenta.com/shop/ready-to-wear/blouses-%26-knits/?page=',
                'https://www.oscardelarenta.com/shop/ready-to-wear/jackets-%26-coats/?page=',
                'https://www.oscardelarenta.com/shop/ready-to-wear/pants-%26-skirts/?page='
            ],
        ),
    )
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cookie = {
            'CurrencyCodeRate':'USD',
            }
            ),
        CN = dict(
            currency = 'CNY',
            cookie = {
            'CurrencyCodeRate':'CNY',
            'CountryCode':'CN',
            },
        ),
        GB = dict(
            currency = 'GBP',
            cookie = {
            'CurrencyCodeRate':'GBP',
            'CountryCode':'GB',
            },
        ),

        )

        


