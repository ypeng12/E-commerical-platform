from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from copy import deepcopy
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout_data = json.loads(checkout.extract_first().split('window.hulkapps.product = ')[1].split('window.hulkapps.product_collection = ')[0].strip())
        item['tmp'] = checkout_data
        if not checkout_data['available']:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        item['sku'] = '-'.join(item['tmp']['variants'][0]['sku'].split('-')[0:-1])
        item['color'] = item['tmp']['variants'][0]['option2']

    def _images(self,res,item,**kwargs):
        item['images'] = ["https://" + image for image in item['tmp']['images']]
        item['cover'] = item['images'][0]

    def _name(self,response,item,**kwargs):
        item['name'] = item['tmp']['title']
        item['designer'] = 'SOLID & STRIPED'

    def _sizes(self,res,item,**kwargs):
        sizes_li = item['tmp']['variants']
        sizes = []
        for size in sizes_li:
            if size['available']:
                sizes.append(size['option1'])
        item["originsizes"] = sizes

        saleprice = str(item['tmp']['variants'][0]['price'])
        listprice = str(item['tmp']['variants'][0]['compare_at_price'])
        item['originsaleprice'] = str(float(saleprice[0:-2] + "." + saleprice[-2:]))
        if listprice != 'None':
            item['originlistprice'] = str(float(listprice[0:-2] + "." + listprice[-2:]))
        else:
            item['originlistprice'] = item['originsaleprice']

    def _parse_images(self, response, **kwargs):
        images_data = res.xpath('//div[@class="product-shop-slider product-shop-slider-desktop royalSlider rsDefault"]//a/@href')
        images_li = []
        for images in images_data:
            if 'https://' not in images and images not in images_li:
                images_li.append('https://' + images)
        return images_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info not in fits:
                fits.append(info)
        return fits

_parser = Parser()

class Config(MerchantConfig):
    name = "solid"
    merchant = "SOLID & STRIPED"

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//a[@class="product-card-link"]',
            designer = '//div[@class="mini-cart-title"]/span',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[contains(text(),"window.hulkapps.product =")]', _parser.checkout)),
            ('sku',('//html',_parser.sku)),
            ('description','//meta[@name="description"]/@content | //div[@class="product-shop-desc-content"]/p/span/text() | //div[@class="product-shop-desc open"]/text()'),
            ('name', ('//html',_parser.name)),
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
            method = _parser.parse_size_info,
            size_info_path = '//p[@data-mce-fragment="1"]/text()',
            ),
        checknum = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.solidandstriped.com/collections/active-accessories?page=',
                'https://www.solidandstriped.com/collections/hats-2?page=',
                'https://www.solidandstriped.com/collections/hair-accessories?page=',
                'https://www.solidandstriped.com/collections/eyewear?page='
            ],
            b = [
                'https://www.solidandstriped.com/collections/beach-bags-1?page='
            ],
            c = [
                'https://www.solidandstriped.com/collections/relaunch-all-beachwear?page='
            ],
            s = [
                'https://www.solidandstriped.com/collections/freedom-moses?page='
            ],
        ),
        m = dict(
            a = [
            ],
            b = [
                
            ],
            c = [
                'https://www.solidandstriped.com/collections/mens-swim-1?page=',
                'https://www.solidandstriped.com/collections/sale-new-to-sale-mens?page='
            ],
            s = [
            ],
        ),
    )

    countries = dict(
        US=dict(
            language='EN',
            area='US',
        ),
        GB=dict(
            currency='GB',
            discurrency='USD',
        )
    )