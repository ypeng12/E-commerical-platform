from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        checkout = json.loads(res.extract_first())
        item['tmp'] = checkout
        if checkout['available']:
            return False
        else:
            return True

    def _parse_num(self,pages,**kwargs):
        # pages = pages/43+1
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?pageNumber=', '?pageNumber=%s'%i)
        return url

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first().strip()

        item['color'] = item['tmp']['variants'][0]['option2']
        item['description'] = re.findall(r'<span>([\s\S]+?)</span>',item['tmp']['description'])
        item['designer'] = 'MALONE SOULIERS'

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('.//div[@class="price__regular"]//dd/span/text()').extract_first()
        saleprice = res.xpath('.//div[@class="price__sale"]//dd/span/text()').extract_first()
        item['originsaleprice'] = listprice
        item['originlistprice'] = saleprice

    def _images(self, res, item, **kwargs):
        images_list  = item['tmp']['images']
        image_li = []
        for images in images_list:
            if "http" not in images:
                image_li.append('https:' + images)
        item['images'] = image_li
        item['cover'] = 'https:' + item['tmp']['featured_image'] if 'http' not in item['tmp']['featured_image'] else item['tmp']['featured_image']

    def _sizes(self, res, item, **kwargs):
        sizes_info = item['tmp']['variants']
        sizes_li = []
        for size in sizes_info:
            if size['available']:
                sizes_li.append(size['option1'])
        item['originsizes'] = sizes_li

    def _parse_images(self, response, **kwargs):
        images_json = json.loads(response.xpath('//script[@id="ProductJson-product-template"]/text()').extract_first())
        image_datas = images_json['images']
        image_li = []
        for images in image_datas:
            if "http" not in images:
                image_li.append('https:' + images)
        return image_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "malone"
    merchant = "Malone Souliers"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//link[@itemprop="url"]/@href',
            designer = '//div[@data-test="web-product-cell"]/meta[@itemprop="productID"]/@content',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[@id="ProductJson-product-template"]/text()', _parser.checkout)),
            ('name', ('//h1[@class="name pos-rel"]/text()',_parser.name)),
            ('prices', ('//div[@class="product__price"]', _parser.prices)),
            ('image',('//html',_parser.images)),
            ('sizes', ('//script[@id="ProductJson-product-template"]/text()', _parser.sizes)),
            ]),
        image = dict(
            method = _parser.parse_images,
        ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="collapseTwo"]/div/ul/li/text()',
        ),
        look = dict(
        ),
        swatch = dict(
        ),
    )        
    list_urls = dict(
        f = dict(
            a = [
               "https://www.shopstyle.com/browse/womens-accessories?pageNumber="
            ],
            b = [
                "https://www.shopstyle.com/browse/handbags?pageNumber=",
            ],
            c = [
                "https://www.shopstyle.com/browse/womens-clothes?pageNumber="
            ],
            e = [
                "https://www.shopstyle.com/browse/womens-beauty?pageNumber="
            ],
            s = [
                "https://www.shopstyle.com/browse/womens-shoes?pageNumber="
            ],
        ),
        m = dict(
            a = [
                "https://www.shopstyle.com/browse/mens-accessories?pageNumber="
            ],
            b = [
                "https://www.shopstyle.com/browse/mens-bags?pageNumber="
            ],
            c = [
                "https://www.shopstyle.com/browse/mens-clothes?pageNumber="
            ],
            s = [
               "https://www.shopstyle.com/browse/mens-shoes?pageNumber="
            ],
        ),
        g = dict(
            c = [
                "https://www.shopstyle.com/browse/girls-outerwear?pageNumber=",
                "https://www.shopstyle.com/browse/girls-dresses?pageNumber=",
                "https://www.shopstyle.com/browse/girls-pants?pageNumber=",
                "https://www.shopstyle.com/browse/girls-skirts?pageNumber=",
                "https://www.shopstyle.com/browse/girls-tops?pageNumber=",
            ],
            s = [
                "https://www.shopstyle.com/browse/girls-shoes?pageNumber=",
            ]
        ),
        b = dict(
            c = [
                "https://www.shopstyle.com/browse/boys-outerwear?pageNumber=",
                "https://www.shopstyle.com/browse/boys-pants?pageNumber=",
                "https://www.shopstyle.com/browse/boys-sweaters?pageNumber=",
                "https://www.shopstyle.com/browse/boys-tops?pageNumber=",
            ],
            s = [
                "https://www.shopstyle.com/browse/boys-shoes?pageNumber="
            ]
        ),
        u = dict(
            h = [
                "https://www.shopstyle.com/browse/living?pageNumber="
            ]
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