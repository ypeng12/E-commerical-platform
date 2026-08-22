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
        data = checkout.extract_first()
        script = data.split('=')[-1].replace(';', '').strip()
        script = json.loads(script)
        if script.get('attributes').get('availability') == "IN_STOCK":
            item['tmp'] = script
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_data = data.split('pagedetails = ')[-1].split(';')[0].strip()
        num_dict = json.loads(num_data)
        count = num_dict['result_count']
        page_num = count / 12 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*12
        url = urljoin(response_url, '?sz=12&start=%s'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        script = item['tmp']
        item['sku'] = script.get('id')
        item['name'] = script.get('name')
        item['designer'] = 'VERSACE'
        item['color'] = script.get('color').upper()
        item['tmp'] = script

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['image_urls']
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        images = [x for x in images]
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        script = item['tmp']
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = script.get('description') +'\n' +'\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        script = item['tmp']
        sku_sizes = item['sku'].split('_')[-1]
        item['originsizes'] = []    
        sizes = script['attributes']['variations_availability']['arr_variants_available']
        for size in sizes:
            if sku_sizes in size:
                if item['category'] == 's' and int(size.split('/')[1].strip())>100:
                    orisize = str(float(size.split('/')[1].strip())/10)
                else:
                    orisize = size.split('/')[1].strip()
                item['originsizes'].append(orisize)
        if item['category'] == 'b' or item['category'] == 'a' or item['category'] == 'e':
            if not item['originsizes']:
                item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        script = item['tmp']
        item['originlistprice'] = str(script.get('unit_price'))
        item['originsaleprice'] = str(script.get('unit_sale_price'))

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"primary-image-item")]/img/@src').extract()
        images = []
        for img in imgs:
            image = 'https://www.versace.com' + img
            if image not in images:
                images.append(image)
        return images
        
    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path'])
        swatches = []
        for data in datas:
            swatch = data.xpath("./@href").extract()[0].split('?pid=')[-1].split('&')[0]
            swatches.append(swatch)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        data = response.xpath('//script[contains(text(), "result_count")]/text()').extract_first()
        num_data = data.split('pagedetails = ')[-1].split(';')[0].strip()
        num_dict = json.loads(num_data)
        count = num_dict['result_count']
        number = int(count)
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'versace'
    merchant = 'VERSACE'
    merchant_headers = {
    'User-Agent':'ModeSensBotVersace202110'
    }
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(), "result_count")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@class="js-grid-tile"]',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './/a[@class="js-producttile_link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[contains(text(), "universal_variable.product")]/text()', _parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            # ('name', ('//html', _parser.name)),
            # ('designer', ('//html', _parser.designer)),
            ('images', ('//div[@id="thumbnails"]/div/div/img/@src', _parser.images)),
            # ('color','//span[@class="js_color-description"]/text()'),
            ('description', ('//div[@class="product-details baseline-small"]//li/text()',_parser.description)), # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//ul[contains(@class,"js-menu-swatches Color js-menu-color")]/li/a',

            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="tab4"]/ul/li/text()',             
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.versace.com/us/en-us/men/small-accessories/',
                'https://www.versace.com/us/en-us/men/accessories/belts/',
                'https://www.versace.com/us/en-us/men/accessories/foulards-scarves/',
                'https://www.versace.com/us/en-us/men/accessories/ties/',
                'https://www.versace.com/us/en-us/men/accessories/fashion-jewelry/',
                'https://www.versace.com/us/en-us/men/watches/',

            ],
            b = [
                'https://www.versace.com/us/en-us/men/accessories/bags-backpacks/'
            ],
            c = [
                'https://www.versace.com/us/en-us/men/clothing/'
            ],
            s = [
                'https://www.versace.com/us/en-us/men/shoes/'
            ],
            e = [
                "https://www.versace.com/us/en-us/men/fragrances/"
            ],
        ),
        f = dict(
            a = [
                'https://www.versace.com/us/en-us/women/accessories/',
                'https://www.versace.com/us/en-us/women/watches/',

            ],
            b = [
                'https://www.versace.com/us/en-us/women/bags/'
            ],
            c = [
                'https://www.versace.com/us/en-us/women/clothing/',
            ],
            s = [
                'https://www.versace.com/us/en-us/women/shoes/'
            ],
            e = [
                "https://www.versace.com/us/en-us/women/fragrances/"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '.com/us/en-us/',
        ),
        CN = dict(
            language = 'ZH', 
            currency = 'CNY',
            currency_sign = '\xa3',
            country_url = '.cn/zh-cn/',
            translate = [
            ('women/clothing/','%E5%A5%B3%E5%A3%AB/%E6%88%90%E8%A1%A3%E7%B3%BB%E5%88%97/'),
            ('women/bags/','%E5%A5%B3%E5%A3%AB/%E5%8C%85%E8%A2%8B/'),
            ('women/shoes/','%E5%A5%B3%E5%A3%AB/%E5%A5%B3%E9%9E%8B/'),
            ('women/accessories/','%E5%A5%B3%E5%A3%AB/%E5%8C%85%E8%A2%8B%E5%92%8C%E9%85%8D%E9%A5%B0/'),
            ('women/watches/','%E5%A5%B3%E5%A3%AB/%E8%85%95%E8%A1%A8/'),
            ('women/fragrances/',''),
            ('men/clothing/','%E7%94%B7%E5%A3%AB/%E6%88%90%E8%A1%A3%E7%B3%BB%E5%88%97/'),
            ('men/accessories/bags-backpacks/','%E7%94%B7%E5%A3%AB/%E5%8C%85%E8%A2%8B%E5%92%8C%E9%85%8D%E9%A5%B0/%E5%8C%85%E8%A2%8B/'),
            ('men/shoes/','%E7%94%B7%E5%A3%AB/%E7%94%B7%E9%9E%8B/'),
            ('men/fragrances/',''),
            ('men/small-accessories/','%E7%94%B7%E5%A3%AB/%E5%B0%8F%E9%85%8D%E9%A5%B0/'),
            ('men/accessories/belts/','%E7%94%B7%E5%A3%AB/%E5%8C%85%E8%A2%8B%E5%92%8C%E9%85%8D%E9%A5%B0/%E8%85%B0%E5%B8%A6/'),
            ('men/accessories/foulards-scarves/','%E5%B8%BD%E5%AD%90%E5%9B%B4%E5%B7%BE/'),
            ('men/accessories/ties/','%E7%94%B7%E5%A3%AB/%E5%8C%85%E8%A2%8B%E5%92%8C%E9%85%8D%E9%A5%B0/%E9%A2%86%E5%B8%A6/'),
            ('men/accessories/fashion-jewelry/','%E7%94%B7%E5%A3%AB/%E5%8C%85%E8%A2%8B%E5%92%8C%E9%85%8D%E9%A5%B0/%E6%97%B6%E5%B0%9A%E7%8F%A0%E5%AE%9D/'),
            ('men/watches/','%E7%94%B7%E5%A3%AB/%E8%85%95%E8%A1%A8/')
            ]
        ),
        # JP = dict(
        #     currency = 'JPY',
        #     # currency_sign = u'\xa3',
        #     country_url = '/international/en/',
        # ),
#         KR = dict( 
#             area='AS',
#             currency = 'KRW',
#             currency_sign = u'\xe2',
#             # thousand_sign = '.',
#         ),
#         HK = dict(
#             area='AS',
#             currency = 'HKD',
#             country_url = '/hk/',
#             currency_sign = 'HK$',
#         ),
#         SG = dict(
#             area='AS',
#             currency = 'SGD',
#             # discurrency = 'USD',
#             country_url = '/sg/',
#             currency_sign = 'SG$',
#             # thousand_sign = '.',
#         ),
        GB = dict(
            currency = 'GBP',
            country_url = '.com/gb/en-gb/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        # AU = dict(
        #     language = 'DE', 
        #     currency = 'AUD',
        #     discurrency = 'EUR',
        #     # currency_sign = u'AU$',
        #     translate = [
        #     ('https://www.versace.com/us/en-us/women/clothing/','https://www.versace.com/eu/de/damen/kleidung/'),
        #     ('https://www.versace.com/us/en-us/women/bags/','https://www.versace.com/eu/de/damen/handtaschen/'),
        #     ('https://www.versace.com/us/en-us/women/shoes/','https://www.versace.com/eu/de/damen/schuhe/'),
        #     ('https://www.versace.com/us/en-us/women/accessories/','https://www.versace.com/eu/de/damen/accessoires/'),
        #     ('https://www.versace.com/us/en-us/women/watches/','https://www.versace.com/eu/de/damen/uhren/'),
        #     ('https://www.versace.com/us/en-us/women/fragrances/','https://www.versace.com/eu/de/world-of-versace/brand/versace-fragrances/'),
        #     ('https://www.versace.com/us/en-us/men/clothing/','https://www.versace.com/eu/de/herren/kleidung/'),
        #     ('https://www.versace.com/us/en-us/men/accessories/bags-backpacks/','https://www.versace.com/eu/de/herren/accessoires/taschen-rucksacke/'),
        #     ('https://www.versace.com/us/en-us/men/shoes/','https://www.versace.com/eu/de/herren/schuhe/'),
        #     ('https://www.versace.com/us/en-us/men/fragrances/','https://www.versace.com/eu/de/world-of-versace/brand/versace-fragrances/'),
        #     ('https://www.versace.com/us/en-us/men/small-accessories/','https://www.versace.com/eu/de/herren/kleinlederwaren/'),
        #     ('https://www.versace.com/us/en-us/men/accessories/belts/','https://www.versace.com/eu/de/herren/accessoires/gurtel/'),
        #     ('https://www.versace.com/us/en-us/men/accessories/foulards-scarves/','https://www.versace.com/eu/de/herren/accessoires/foulards-tucher/'),
        #     ('https://www.versace.com/us/en-us/men/accessories/ties/','https://www.versace.com/eu/de/herren/accessoires/krawatten/'),
        #     ('https://www.versace.com/us/en-us/men/accessories/fashion-jewelry/','https://www.versace.com/eu/de/herren/accessoires/modeschmuck/'),
        #     ('https://www.versace.com/us/en-us/men/watches/','https://www.versace.com/eu/de/herren/uhren/')
        #     ]

        # ),
        DE = dict(
            language = 'DE', 
            currency = 'EUR',
            country_url = '.com/de/de-de/',
            translate = [
            ('women/clothing/','damen/kleidung/'),
            ('women/bags/','damen/handtaschen/'),
            ('women/shoes/','damen/schuhe/'),
            ('women/accessories/','damen/accessoires/'),
            ('women/watches/','damen/uhren/'),
            ('women/fragrances/','world-of-versace/brand/versace-fragrances/'),
            ('men/clothing/','herren/kleidung/'),
            ('men/accessories/bags-backpacks/','herren/accessoires/taschen-rucksacke/'),
            ('men/shoes/','herren/schuhe/'),
            ('men/fragrances/','world-of-versace/brand/versace-fragrances/'),
            ('men/small-accessories/','herren/kleinlederwaren/'),
            ('men/accessories/belts/','herren/accessoires/gurtel/'),
            ('men/accessories/foulards-scarves/','herren/accessoires/foulards-tucher/'),
            ('men/accessories/ties/','herren/accessoires/krawatten/'),
            ('men/accessories/fashion-jewelry/','herren/accessoires/modeschmuck/'),
            ('men/watches/','herren/uhren/')
            ]
        ),
#         NO = dict(
#             area='EU',
#             currency = 'NOK',
#             country_url = '/no/',
#             discurrency = 'EUR',
#             thousand_sign = '.',
#         ),
#         RU = dict(
#             area='EU',
#             language = 'RU',
#             currency = 'RUB',
#             country_url = '/ru/',
#             currency_sign = u'EUR',
#             thousand_sign = u'\xa0',
#             discurrency = 'EUR',
#      
        )

        


