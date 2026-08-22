# -*- coding: utf-8 -*-
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
        sold_out = checkout.xpath('//button[@value="Email Me When Available"]')
        check_out = checkout.xpath('//button[text()="Add to Bag"]')
        if not checkout or sold_out: 
            return True
        else:
            return False
        
    def _page_num(self, data, **kwargs):
        count = int(data.strip())
        page_num = count/21 + 1
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?sz='+str(21 * i)+'&start=0'
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = ''.join(sku_data.extract_first().split('/')[-1].split('_')[0:2])

        item['sku'] = sku.strip() if len(sku.strip())==11 else ''

    def _name(self, name_data, item, **kwargs):
        item['name'] = name_data.extract_first().strip()
        item['designer'] = 'HACKETT'
          
    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = imgs
        item['cover'] = item['images'][0]

    def _color(self, colors, item, **kwargs):
        colors = colors.extract()
        item['color'] = ''.join(colors).strip()

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.xpath('//ul[@class="tab-content c-product-variations__sublist size"]/li/a/text()').extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

    def _prices(self, prices, item, **kwargs):
        price = prices.xpath('.//div[@class="product-price"]//span[@itemprop="price"]/text()').extract_first()
        item['originlistprice'] = price.strip()
        item['originsaleprice'] = price.strip()

    def _description(self, description, item, **kwargs):
        descs = description.extract()
        desc_li = []
        for desc in descs:
            if not desc.strip():
                continue
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="images-container js-zoom"]/picture//img/@data-src').extract()
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('dimensions' in info.strip().lower() or 'width' in info.strip().lower() or 'cm' in info.strip().lower() or 'mm' in info.strip().lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info
    def _parse_checknum(self, response, **kwargs):
        
        number = int(response.xpath('//div[@id="results-products"]//b/text()').extract_first().strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'hackett'
    merchant = 'Hackett'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@id="results-products"]//b/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[@id="search-result-items"]/li',
            designer = './div/a/@data-brand',
            link = './/a[@class="thumb-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//meta[@property="og:image"]/@content',_parser.sku)),
            # ('sku', ('//div[@itemprop="productID"]/text()',_parser.sku)),
            ('name', ('//meta[@property="og:title"]/@content', _parser.name)),
            ('color', ('//div[@class="c-product-variations__color-label"]/text()', _parser.color)),
            ('images', ('//div[@class="images-container js-zoom"]/picture//img/@data-src', _parser.images)),
            ('description', ('//div[@class="c-product-description__content"]//text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@id="product-content"]', _parser.prices))
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
            size_info_path = '//div[@class="content"][1]//text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),

        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.hackett.com/intl/men/shop-all/accessories/belts-and-braces/',
                'https://www.hackett.com/intl/men/shop-all/accessories/cufflinks-and-studs/',
                'https://www.hackett.com/intl/men/shop-all/accessories/scarves-hats-and-gloves/',
                'https://www.hackett.com/intl/men/shop-all/accessories/ties-bow-ties-and-pocket-squares/',
                'https://www.hackett.com/intl/men/shop-all/accessories/umbrellas/',
                'https://www.hackett.com/intl/men/shop-all/accessories/wallets-and-keyrings/',
            ],
            b = [
                'https://www.hackett.com/intl/men/shop-all/accessories/bags-and-luggage/',
            ],
            c = [
                'https://www.hackett.com/intl/men/shop-all/clothing/blazers/',
                'https://www.hackett.com/intl/men/shop-all/clothing/coats-and-jackets/',
                'https://www.hackett.com/intl/men/shop-all/clothing/knitwear/',
                'https://www.hackett.com/intl/men/shop-all/clothing/polo-and-rugby-shirts/',
                'https://www.hackett.com/intl/men/shop-all/clothing/shirts/',
                'https://www.hackett.com/intl/men/shop-all/clothing/shorts-and-swimwear/',
                'https://www.hackett.com/intl/men/shop-all/clothing/suits-and-waistcoats/',
                'https://www.hackett.com/intl/men/shop-all/clothing/trousers-and-jeans/',
                'https://www.hackett.com/intl/men/shop-all/clothing/t-shirts-and-sweatshirts/',
                'https://www.hackett.com/intl/men/shop-all/accessories/socks-and-underwear/',
            ],
            s = [
                'https://www.hackett.com/intl/men/shop-all/shoes/all-shoes/'
            ],
        ),
        f = dict(


        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '/intl/',
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = 'CN\xa5',
            cookies = {
            'dwsecuretoken_00b0cc1c3e295dd89916510526f454c9':'I8OoQVLnYw0jojJCDhgsKWPbEESEV6jRcQ==',
            'dwsecuretoken_794930f152925e13630bbbd010f5fd65':'pPcotWMvqoiCCE36NRYnTFW7wkUh07tVOg==',
            'dwsecuretoken_fad765028c7d098040d6ac6a59481bbb':'3iXi05_SL45bVwsskh8Q54ReoE_2MeFi4A==',
            'dwsid':'uO8rV4B6yLBuox0o2W0h5NkjA7iH1bjnp7WPIJKVxrk5MLTO2OrD1palOm3srUbtAS_B5-_IQAx9X2bghIaJIw==',
            }
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/gb/',
            translate = [
                ('/shop-all/','/view-all/'),
                ('-and-','-'),
            ],
        ),
        DE = dict(
            language = 'DE',
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/de/',
            translate = [
                ('/men/shop-all/','/herren/alles-shoppen/'),
                ('/accessories/bags-and-luggage/','/accessoires/taschen-reisegepack'),
                ('/accessories/belts-and-braces/','/accessoires/gurtel-hosentrager'),
                ('/accessories/cufflinks-and-studs/','/accessoires/manschettenknöpfe-krawattenklammern'),
                ('/accessories/scarves-hats-and-gloves/','/accessoires/schals-hute-mutzen-handschuhe'),
                ('/accessories/socks-and-underwear/','/accessoires/socken-unterwasche'),
                ('/accessories/ties-bow-ties-and-pocket-squares/','/accessoires/krawatten-fliegen-einstecktucher'),
                ('/accessories/umbrellas/','/accessoires/regenschirme'),
                ('/accessories/wallets-and-keyrings/','/accessoires/portemonnaies-schlusselanhanger'),
                ('/clothing/blazers/','/kleidung/blazer'),
                ('/clothing/coats-and-jackets/','/kleidung/mantel-jacken'),
                ('/clothing/knitwear/','/kleidung/strickwaren'),
                ('/clothing/polo-and-rugby-shirts/','/kleidung/polo-rugby-shirts'),
                ('/clothing/shirts/','/kleidung/hemden'),
                ('/clothing/shorts-and-swimwear/','/kleidung/shorts-bademode'),
                ('/clothing/suits-and-waistcoats/','/kleidung/anzuge-westen'),
                ('/clothing/trousers-and-jeans/','/kleidung/hosen-jeans'),
                ('/clothing/t-shirts-and-sweatshirts/','/kleidung/t-shirts-sweatshirts'),
                ('/shoes/all-shoes/','/schuhe/alles-schuhe'),
            ],
        )
        )

        


