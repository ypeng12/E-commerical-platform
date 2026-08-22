from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, sku_data, item, **kwargs):
        if item['country'] != 'CN' and 'cn.forzieri.com' in item['url']:
            item['error'] = 'ignore'
            return False
        sku = sku_data.extract_first()
        url = 'https://public.forzieri.com/v1/products/' + sku
        response = requests.get(url)
        sold_dict = json.loads(response.text)
        if sold_dict['sold_out']:
            return True
        else:
            return False
        
    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('10000', str(i))
  
        return url

    def _sku(self, sku_data, item, **kwargs):
        productSku = sku_data.extract_first()
        parts = productSku.split('-')
        if len(parts) >= 3 and item['category'] in ['s','c']:
            item['sku'] = '-'.join(productSku.split('-')[:2])
        else:
            item['sku'] = productSku
        item['sku'] = item['sku'].upper()

    def _designer(self, designer_data, item, **kwargs):
        brand = designer_data.extract_first().strip().upper()
        filtrate = re.compile('[\u4E00-\u9FA5]')
        item['designer'] = filtrate.split(brand)[0].strip()
          
    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append(img)
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

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        sizes = sizes_data.extract()
        if len(sizes) > 0:
            for size in sizes:
                if 'select' in size.lower():
                    continue
                item['originsizes'].append(size.split('/')[0].split('-')[-1].split('(')[0].split('|')[0].strip().replace('IT','').replace('EU','').replace('FR','').replace('US','').replace('M','').replace(',','.'))
        else:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@id="salePrice"]//text()').extract()
        listPrice = prices.xpath('.//span[@id="listPrice"]//text()').extract()
        item['originsaleprice'] = ''.join(salePrice) if salePrice else ''.join(listPrice)
        item['originlistprice'] = ''.join(listPrice) if salePrice else ''

    def _parse_swatches(self, response, swatch_path, **kwargs):
        swatchRes = response.xpath(swatch_path['path']).extract()
        swatches = []
        for swatch in swatchRes:
            swatches.append(swatch.upper())

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        dept_id = response.xpath('//input[@name="dept_id"]/@value').extract_first()
        sku = response.url.split('?')[0].split('/')[-1]
        base_url = 'https://www.forzieri.com/ajaxs/product_schedatecnica.ajax.asp?l=usa&c=usa&dept_id=%s&sku=%s'%(dept_id,sku)
        res = requests.get(base_url)
        html = etree.HTML(res.text)
        infos = html.xpath('//table/tr')
        fits = []
        for info in infos:
            info_li = info.xpath('.//text()')
            info_str = ':'.join([a for a in [x.strip() for x in info_li] if a])
            if info_str.strip() and info_str.strip() not in fits and ('cm' in info_str.strip() or 'DIMENSIONS' in info_str.strip() or 'WEIGHT' in info_str.strip()):
                fits.append(info_str.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="current"]/text()').extract_first().strip())*48
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'forzieri'
    merchant = 'FORZIERI'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="current"]/text()',
            list_url = _parser.list_url,
            items = '//article',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './div[@class="product-list-item-info"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@id="productSku"]/text()', _parser.checkout)),
            ('sku', ('//span[@id="productSku"]/text()',_parser.sku)),
            ('name', '//span[@class="product-name"]/text()'),
            ('designer', ('//span[@class="brand-name"]/a/text()', _parser.designer)),
            ('images', ('//div[@class="sticky-wrap gallery-wrap"]/div/img/@src', _parser.images)),
            ('color','//span[@itemprop="color"]/text()'),
            ('description', ('//div[@id="descriptionProduct"]//div/p[1]/text()',_parser.description)),
            ('sizes', ('//select[@id="variantSelect"]/option/text()', _parser.sizes)),
            ('prices', ('//p[@id="productPriceOffer"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[@id="product-variants-scroller"]//li/a/@data-sku',
            image_path='//div[@id="productGallery"]//div/img/@src',
            ),
        image = dict(
            image_path = '//div[@class="sticky-wrap gallery-wrap"]/div/img/@src'
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//html',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.forzieri.com/mens-accessories/10000',
                'https://www.forzieri.com/mens-jewelry/10000',
                'https://www.forzieri.com/mens-watches/10000',
                'https://www.forzieri.com/fine-watches/10000'
            ],
            b = [
                'https://www.forzieri.com/mens-bags/10000'
            ],
            c = [
                'https://www.forzieri.com/mens-leather-jackets/10000',
                'https://www.forzieri.com/dress-shirts/10000',
                'https://www.forzieri.com/sale/mens-clothing/10000'
            ],
            s = [
                'https://www.forzieri.com/mens-shoes/10000',
                'https://www.forzieri.com/sale/mens-shoes/10000'
            ],
        ),
        f = dict(
            a = [
                'https://www.forzieri.com/womens-accessories/10000',
                'https://www.forzieri.com/jewelry/fine-jewelry/10000',
                'https://www.forzieri.com/jewelry/fashion-jewelry/10000',
                'https://www.forzieri.com/jewelry/murano/10000',
                'https://www.forzieri.com/womens-watches/10000'
            ],
            b = [
                'https://www.forzieri.com/handbags/10000',
                'https://www.forzieri.com/sale/handbags/10000'
            ],
            c = [
                'https://www.forzieri.com/leather-jackets/10000',
                'https://www.forzieri.com/outerwear-furs/10000',
                'https://www.forzieri.com/sale/clothing/10000'
            ],
            s = [
                'https://www.forzieri.com/shoes/10000',
                'https://www.forzieri.com/sale/shoes/10000'
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
            country_url = 'www.forzieri.com',
        ),
        CN = dict(
            language = 'ZH', 
            currency = 'CNY',
            country_url = 'www.cn.forzieri.com',
            currency_sign = '\xa5',
            vat_rate = 1.010,
            translate = [
            ('fine-watches/10000','chn/deptd.asp?l=chn&c=chn&dept_id=121&page=10000'),
            ('mens-accessories/10000','chn/group.asp?l=chn&c=chn&gr=10&page=10000'),
            ('mens-jewelry/10000','chn/deptd.asp?l=chn&c=chn&dept_id=888801&page=10000'),
            ('mens-watches/10000','chn/deptd.asp?l=chn&c=chn&dept_id=84&page=10000'),
            ('mens-bags/10000','chn/deptd.asp?l=chn&c=chn&dept_id=108&page=10000'),
            ('mens-leather-jackets/10000','chn/deptd.asp?l=chn&c=chn&dept_id=79&page=10000'),
            ('dress-shirts/10000','chn/deptd.asp?l=chn&c=chn&dept_id=68&page=10000'),
            ('sale/mens-clothing/10000','chn/salea.asp?l=chn&c=chn&gr=12&page=10000'),
            ('mens-shoes/10000','chn/deptd.asp?l=chn&c=chn&dept_id=75&page=10000'),
            ('sale/mens-shoes/10000','chn/salea.asp?l=chn&c=chn&gr=6&page=10000'),
            ('womens-accessories/10000','chn/group.asp?l=chn&c=chn&gr=9&page=10000'),
            ('jewelry/fine-jewelry/10000','chn/group.asp?l=chn&c=chn&gr=312&page=10000'),
            ('jewelry/fashion-jewelry/10000','chn/group.asp?l=chn&c=chn&gr=313&page=10000'),
            ('jewelry/murano/10000','chn/group.asp?l=chn&c=chn&gr=314&page=10000'),
            ('womens-watches/10000','chn/deptd.asp?l=chn&c=chn&dept_id=33&page=10000'),
            ('handbags/10000','chn/deptd.asp?l=chn&c=chn&dept_id=18&page=10000'),
            ('sale/handbags/10000','chn/salea.asp?l=chn&c=chn&gr=3&page=10000'),
            ('leather-jackets/10000','chn/deptd.asp?l=chn&c=chn&dept_id=77&page=10000'),
            ('outerwear-furs/10000','chn/deptd.asp?l=chn&c=chn&dept_id=106&page=10000'),
            ('sale/clothing/10000','chn/salea.asp?l=chn&c=chn&gr=11&page=10000'),
            ('shoes/10000','chn/deptd.asp?l=chn&c=chn&dept_id=73&page=10000'),
            ('sale/shoes/10000','chn/salea.asp?l=chn&c=chn&gr=5&page=10000')
            ]
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = 'www.jp.forzieri.com',
            translate = [
            ('fine-watches/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=121&page=10000'),
            ('mens-accessories/10000','jpn/group.asp?l=jpn&c=jpn&gr=10&page=10000'),
            ('mens-jewelry/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=888801&page=10000'),
            ('mens-watches/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=84&page=10000'),
            ('mens-bags/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=108&page=10000'),
            ('mens-leather-jackets/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=79&page=10000'),
            ('dress-shirts/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=68&page=10000'),
            ('sale/mens-clothing/10000','jpn/salea.asp?l=jpn&c=jpn&gr=12&page=10000'),
            ('mens-shoes/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=75&page=10000'),
            ('sale/mens-shoes/10000','jpn/salea.asp?l=jpn&c=jpn&gr=6&page=10000'),
            ('womens-accessories/10000','jpn/group.asp?l=jpn&c=jpn&gr=9&page=10000'),
            ('jewelry/fine-jewelry/10000','jpn/group.asp?l=jpn&c=jpn&gr=312&page=10000'),
            ('jewelry/fashion-jewelry/10000','jpn/group.asp?l=jpn&c=jpn&gr=313&page=10000'),
            ('jewelry/murano/10000','jpn/group.asp?l=jpn&c=jpn&gr=314&page=10000'),
            ('womens-watches/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=33&page=10000'),
            ('handbags/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=18&page=10000'),
            ('sale/handbags/10000','jpn/salea.asp?l=jpn&c=jpn&gr=3&page=10000'),
            ('leather-jackets/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=77&page=10000'),
            ('outerwear-furs/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=106&page=10000'),
            ('sale/clothing/10000','jpn/salea.asp?l=jpn&c=jpn&gr=11&page=10000'),
            ('shoes/10000','jpn/deptd.asp?l=jpn&c=jpn&dept_id=73&page=10000'),
            ('sale/shoes/10000','jpn/salea.asp?l=jpn&c=jpn&gr=5&page=10000')
            ]
        ),
        KR = dict( 
            currency = 'KRW',
            country_url = 'www.kr.forzieri.com',
            currency_sign = 'w.',
            translate = [
            ('fine-watches/10000','kor/deptd.asp?l=kor&c=kor&dept_id=121&page=10000'),
            ('mens-accessories/10000','kor/group.asp?l=kor&c=kor&gr=10&page=10000'),
            ('mens-jewelry/10000','kor/deptd.asp?l=kor&c=kor&dept_id=888801&page=10000'),
            ('mens-watches/10000','kor/deptd.asp?l=kor&c=kor&dept_id=84&page=10000'),
            ('mens-bags/10000','kor/deptd.asp?l=kor&c=kor&dept_id=108&page=10000'),
            ('mens-leather-jackets/10000','kor/deptd.asp?l=kor&c=kor&dept_id=79&page=10000'),
            ('dress-shirts/10000','kor/deptd.asp?l=kor&c=kor&dept_id=68&page=10000'),
            ('sale/mens-clothing/10000','kor/salea.asp?l=kor&c=kor&gr=12&page=10000'),
            ('mens-shoes/10000','kor/deptd.asp?l=kor&c=kor&dept_id=75&page=10000'),
            ('sale/mens-shoes/10000','kor/salea.asp?l=kor&c=kor&gr=6&page=10000'),
            ('womens-accessories/10000','kor/group.asp?l=kor&c=kor&gr=9&page=10000'),
            ('jewelry/fine-jewelry/10000','kor/group.asp?l=kor&c=kor&gr=312&page=10000'),
            ('jewelry/fashion-jewelry/10000','kor/group.asp?l=kor&c=kor&gr=313&page=10000'),
            ('jewelry/murano/10000','kor/group.asp?l=kor&c=kor&gr=314&page=10000'),
            ('womens-watches/10000','kor/deptd.asp?l=kor&c=kor&dept_id=33&page=10000'),
            ('handbags/10000','kor/deptd.asp?l=kor&c=kor&dept_id=18&page=10000'),
            ('sale/handbags/10000','kor/salea.asp?l=kor&c=kor&gr=3&page=10000'),
            ('leather-jackets/10000','kor/deptd.asp?l=kor&c=kor&dept_id=77&page=10000'),
            ('outerwear-furs/10000','kor/deptd.asp?l=kor&c=kor&dept_id=106&page=10000'),
            ('sale/clothing/10000','kor/salea.asp?l=kor&c=kor&gr=11&page=10000'),
            ('shoes/10000','kor/deptd.asp?l=kor&c=kor&dept_id=73&page=10000'),
            ('sale/shoes/10000','kor/salea.asp?l=kor&c=kor&gr=5&page=10000')
            ]
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'EUR',
            country_url = 'www.eu.forzieri.com',
            currency_sign = '\u20ac',
            thousand_sign = '.',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            country_url = 'www.eu.forzieri.com',
            currency_sign = '\u20ac',
            thousand_sign = '.',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = 'www.uk.forzieri.com',
            currency_sign = '\xa3',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = 'www.ca.forzieri.com',
            currency_sign = 'C$',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = 'www.au.forzieri.com',
            currency_sign = 'AU$'
        ),
        DE = dict(
            language = 'DE',
            currency = 'EUR',
            country_url = 'www.de.forzieri.com',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            translate = [
            ('mens-accessories','herren-accessoires'),
            ('mens-jewelry','herrenschmuck'),
            ('mens-watches','herrenuhren'),
            ('mens-bags','herrentaschen'),
            ('mens-leather-jackets','herren-lederjacken'),
            ('dress-shirts','hemden'),
            ('sale/mens-clothing','sale/herren-kleidung'),
            ('mens-shoes','herren-schuhe'),
            ('sale/mens-shoes','sale/herren-schuhe'),
            ('womens-accessories','damen-accessoires'),
            ('jewelry/fine-jewelry','schmuck/feiner-schmuck'),
            ('jewelry/fashion-jewelry','schmuck/mode-schmuck'),
            ('jewelry/murano','schmuck/murano'),
            ('womens-watches','damenuhren'),
            ('handbags','handtaschen'),
            ('sale/handbags','sale/taschen'),
            ('leather-jackets','lederjacken'),
            ('outerwear-furs','damen-jacken-maentel'),
            ('sale/clothing','sale/kleidung'),
            ('shoes','schuhe'),
            ('sale/shoes','sale/schuhe')
            ]
        ),

        NO = dict(
            currency = 'NOK',
            country_url = 'www.no.forzieri.com',
            currency_sign = 'kr'
        ),
        RU = dict(
            language = 'RU',
            currency = 'RUB',
            country_url = 'www.ru.forzieri.com',
            currency_sign = '\u0440\u0443\u0431.',
            translate = [
            ('fine-watches/10000','rus/deptd.asp?l=rus&c=rus&dept_id=121&page=10000'),
            ('mens-accessories/10000','rus/group.asp?l=rus&c=rus&gr=10&page=10000'),
            ('mens-jewelry/10000','rus/deptd.asp?l=rus&c=rus&dept_id=888801&page=10000'),
            ('mens-watches/10000','rus/deptd.asp?l=rus&c=rus&dept_id=84&page=10000'),
            ('mens-bags/10000','rus/deptd.asp?l=rus&c=rus&dept_id=108&page=10000'),
            ('mens-leather-jackets/10000','rus/deptd.asp?l=rus&c=rus&dept_id=79&page=10000'),
            ('dress-shirts/10000','rus/deptd.asp?l=rus&c=rus&dept_id=68&page=10000'),
            ('sale/mens-clothing/10000','rus/salea.asp?l=rus&c=rus&gr=12&page=10000'),
            ('mens-shoes/10000','rus/deptd.asp?l=rus&c=rus&dept_id=75&page=10000'),
            ('sale/mens-shoes/10000','rus/salea.asp?l=rus&c=rus&gr=6&page=10000'),
            ('womens-accessories/10000','rus/group.asp?l=rus&c=rus&gr=9&page=10000'),
            ('jewelry/fine-jewelry/10000','rus/group.asp?l=rus&c=rus&gr=312&page=10000'),
            ('jewelry/fashion-jewelry/10000','rus/group.asp?l=rus&c=rus&gr=313&page=10000'),
            ('jewelry/murano/10000','rus/group.asp?l=rus&c=rus&gr=314&page=10000'),
            ('womens-watches/10000','rus/deptd.asp?l=rus&c=rus&dept_id=33&page=10000'),
            ('handbags/10000','rus/deptd.asp?l=rus&c=rus&dept_id=18&page=10000'),
            ('sale/handbags/10000','rus/salea.asp?l=rus&c=rus&gr=3&page=10000'),
            ('leather-jackets/10000','rus/deptd.asp?l=rus&c=rus&dept_id=77&page=10000'),
            ('outerwear-furs/10000','rus/deptd.asp?l=rus&c=rus&dept_id=106&page=10000'),
            ('sale/clothing/10000','rus/salea.asp?l=rus&c=rus&gr=11&page=10000'),
            ('shoes/10000','rus/deptd.asp?l=rus&c=rus&dept_id=73&page=10000'),
            ('sale/shoes/10000','rus/salea.asp?l=rus&c=rus&gr=5&page=10000')
            ]
            
        ),
        )

        


