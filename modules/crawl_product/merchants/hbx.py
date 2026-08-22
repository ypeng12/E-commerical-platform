# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils import utils
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data
        if json_data['soldOutAt']:
            return True
        else:
            return False

    def _page_num(self, data, **kwargs):
        page_num = 0
        return int(page_num)

    def _name(self, res, item, **kwargs):
        json_data = item['tmp']
        item['sku'] = json_data['id']
        item['name'] = json_data['name']
        item['designer'] = json_data['brands'][0]['name'].upper()

    def _description(self, description, item, **kwargs):
        html = etree.HTML(item['tmp']['description'])
        descs = html.xpath('//text()')
        color = ''
        description = []
        for desc in descs:
            if desc.strip():
                description.append(desc)
            if 'Color:' in desc:
                color = desc.split('Color:')[-1].strip().upper()
        item['description'] = "\n".join(description)
        item['color'] = color if color else ''

    def _images(self, images, item, **kwargs):
        data = images.extract_first().split("zoomed-images='")[1]
        images_li = re.match(r'(\[.*?\])',data).group()
        images = json.loads(images_li)
        item['images'] = images
        item['cover'] = item['images'][0]

    def _prices(self, res, item, **kwargs):
        json_data = item['tmp']
        if json_data['originalPrice']:
            listprice = json_data['originalPrice']['display']
        else:
            listprice = json_data['originalPrice']
        saleprice = json_data['price']['display']
        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _sizes(self, sizes, item, **kwargs):
        data = item['tmp']
        final_sale = data['isBackInStock']
        preorder = data['isPreOrder']
        memo = ':p' if preorder else ''
        memo = ':f' if final_sale else ''

        osizes = []
        for variant in data['variants']:
            if variant['isAvailable']:
                osize = variant['optionValues'][0]['value']
                osizes.append(osize + memo)
        item['originsizes'] = osizes

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//ul[@class="slides"]/li/img/@src').extract()
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = "hbx"
    merchant = "HBX"
    # url_split = False


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div/span[contains(text(),"of")]/text()', _parser.page_num),
            items = '//div[@class="product-thumbnail"]',
            designer = './/h5[@class="brand-name function-bold"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//div[@data-controller="product"]/@data-product-json-value', _parser.checkout)),
            ('name', ('//html', _parser.name)),
            ('description', ('//div[@itemprop="description"]/li/text()',_parser.description)),
            ('images',('//product-image-slider',_parser.images)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//div[@id="product-summary"]/@data-product',_parser.sizes)),
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
            size_info_path = '//div[@id="sizing-section"]//ul//li//text()',
            ),
        blog = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://hbx.com/women/categories/accessories/page/",
                ],
            b = [
                "https://hbx.com/women/categories/bags/page/",
                ],
            c = [
                "https://hbx.com/women/categories/clothing/page/",
            ],
            s = [
                "https://hbx.com/women/categories/shoes/page/",
            ]
        ),
        m = dict(
            a = [
                "https://hbx.com/men/categories/accessories/page/",
            ],
            b = [
                "https://hbx.com/men/categories/bags/page/"
            ],
            c = [
                "https://hbx.com/men/categories/clothing/page/",
            ],
            s = [
                "https://hbx.com/men/categories/shoes/page/",
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        )
        )
