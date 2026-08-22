from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, scripts, item, **kwargs):
        scripts_data = scripts.extract()
        for script in scripts_data:
            if 'spConfig' in script:
                script_str = script
                break
        script_str = script_str.split('Product.Config(')[-1].split('$$')[0].split(');')[0]
        script_dict = json.loads(script_str)
        if len(list(script_dict['attributes'].values())[0]['options']) == len(script_dict['outOfStockProducts']):
            sold_out = True
        else:
            sold_out = False
            item['tmp'] = script_dict
        return sold_out

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?p=%s'%i
        return url

    def _sku(self, data, item, **kwargs):
        skus = data.extract()
        for sku in skus:
            if 'Reference' in sku:
                sku_str = sku
                break
        item['sku'] = sku_str.split(':')[-1].strip()

    def _color(self, data, item, **kwargs):
        colors = data.extract()
        color_str = ''
        for color in colors:
            if 'Color' in color:
                color_str = color
                break
        item['color'] = color_str.split(':')[-1].strip() if color_str else ''

    def _name(self, data, item, **kwargs):
        item['name'] = data.extract_first().strip()

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append(img.replace('http:','https:'))
        item['images'] = img_li
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        json_dict = item['tmp']
        products = list(json_dict['attributes'].values())[0]['options']
        sold_out_li = json_dict['outOfStockProducts']
        size_li = []
        for product in products:
            if product['products'][0] in sold_out_li:
                continue
            size_li.append(product['label'])

        item['originsizes'] = size_li
        # item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = ''

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path'])
        detail = response.xpath(swatch_path['current_path']).extract()
        for line in detail:
            if 'Reference' in line:
                pid = line.split(':')[-1].strip().upper()
        swatches = []
        swatches.append(pid)
        for data in datas:
            pid = data.xpath('./@data-sku').extract()[0]
            swatches.append(pid)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('height' in info or 'Dimensions' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@data-page-id]/@data-page-id').extract_first())*9
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'christian'
    merchant = 'Christian Louboutin'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@data-page-id]/@data-page-id',
            list_url = _parser.list_url,
            items = '//div[@class="product"]',
            designer = './div/p/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script/text()', _parser.checkout)),
            ('sku', ('//p[@class="content"]//text()',_parser.sku)),
            ('name', ('//span[@class="title title-cap"]/text()',_parser.name)),    # TODO: path & function
            ('designer', '//meta[@property="og:brand"]/@content'),
            ('images', ('//div[@class="swiper-container gallery-top"]//img/@src', _parser.images)),
            ('description', ('//div[@class="description"]/text() | //div[@class="description"]/p/text()',_parser.description)), # TODO:
            ('color',('//p[@class="content"]//text()', _parser.color)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//span[@class="regular-price"]/span/text()', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//ul[@class="thumbs"]/li/a',
            current_path='//p[@class="content"]/text()',
            image_path = '//div[@class="swiper-container gallery-top"]//img/@src',
            ),
        image = dict(
            image_path = '//div[@class="swiper-container gallery-top"]//img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//p[@class="content"]//text()',   
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'http://us.christianlouboutin.com/us_en/shop-online-3/mens-1/accessories.html?p=10000'
            ],
            b = [
                'http://us.christianlouboutin.com/us_en/shop-online-3/mens-1/leather-goods/mens-bags.html?p=10000',
                'shop-online-3/mens-1/bags.html'
            ],
            c = [
            ],
            s = [
                'http://us.christianlouboutin.com/us_en/shop-online-3/mens-1/mens-shoes.html?p=10000',
            ],
        ),
        f = dict(
            a = [
                'http://us.christianlouboutin.com/us_en/shop-online-3/women-1/accessories.html?p=10000'
            ],
            b = [
                'http://us.christianlouboutin.com/us_en/shop-online-3/women-1/bags.html?p=10000'
            ],
            c = [
            ],
            s = [
                'http://us.christianlouboutin.com/us_en/shop-online-3/women-1/women.html?p=10000',
            ],
            e = [
                'http://us.christianlouboutin.com/us_en/shop-online-3/beauty/nails.html?p=10000',
                'http://us.christianlouboutin.com/us_en/shop-online-3/beauty/lips.html?p=10000',
                'http://us.christianlouboutin.com/us_en/shop-online-3/beauty/parfums-1.html?p=10000',
            ],

        params = dict(
            page = 1,
            ),
        ),

        # country_url_base = '//us.christianlouboutin.com/us_en/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            cur_rate = 1,
            country_url = '//us.christianlouboutin.com/us_en/',
            ),

        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '//eu.christianlouboutin.com/uk_en/',
            translate = [
            ('shop-online-3/mens-1/accessories.html','homepage-1/men-collection/accessories-1.html'),
            ('shop-online-3/mens-1/bags.html','homepage-1/men-collection/accessories.html'),
            ('shop-online-3/mens-1/mens-shoes.html','homepage-1/men-collection/shoes.html'),
            ('shop-online-3/women-1/accessories.html','homepage-1/accessories.html'),
            ('shop-online-3/women-1/bags.html','homepage-1/women-1/leather-goods.html'),
            ('shop-online-3/women-1/women.html','homepage-1/women-1/shoes.html'),
            ('shop-online-3/beauty/nails.html','homepage-1/beauty/nails.html'),
            ('shop-online-3/beauty/lips.html','homepage-1/beauty/lips.html'),
            ('shop-online-3/beauty/parfums-1.html','homepage-1/beauty/parfums.html'),
            ]
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'C$',
            country_url = '//us.christianlouboutin.com/ca_en/',
            translate = [
            ('shop-online-3/mens-1/accessories.html','shop-online-1/mens/accessories.html'),
            ('shop-online-3/mens-1/bags.html','shop-online-1/mens/bags.html'),
            ('shop-online-3/mens-1/mens-shoes.html','shop-online-1/mens/mens-shoes.html'),
            ('shop-online-3/women-1/accessories.html','shop-online-1/women-canada/accessories.html'),
            ('shop-online-3/women-1/bags.html','shop-online-1/women-canada/bags.html'),
            ('shop-online-3/women-1/women.html','shop-online-1/women-canada/women.html'),
            ('shop-online-3/beauty/nails.html','shop-online-1/beauty/nails.html'),
            ('shop-online-3/beauty/lips.html','shop-online-1/beauty/lips.html'),
            ('shop-online-3/beauty/parfums-1.html','shop-online-1/beauty/parfums.html'),
            ]
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '//eu.christianlouboutin.com/de_en/',
            translate = [
            ('shop-online-3/mens-1/accessories.html','homepage-1/men-collection/accessories-1.html'),
            ('shop-online-3/mens-1/bags.html','homepage-1/men-collection/accessories.html'),
            ('shop-online-3/mens-1/mens-shoes.html','homepage-1/men-collection/shoes.html'),
            ('shop-online-3/women-1/accessories.html','homepage-1/accessories.html'),
            ('shop-online-3/women-1/bags.html','homepage-1/women-1/leather-goods.html'),
            ('shop-online-3/women-1/women.html','homepage-1/women-1/shoes.html'),
            ('shop-online-3/beauty/nails.html','homepage-1/beauty/nails.html'),
            ('shop-online-3/beauty/lips.html','homepage-1/beauty/lips.html'),
            ('shop-online-3/beauty/parfums-1.html','homepage-1/beauty/parfums.html'),
            ]
        ),

        )

        


