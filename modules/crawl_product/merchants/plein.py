from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True
    def _sku(self, data, item, **kwargs):
        sku = data.extract()[0].split(':')[-1].strip()
        item['sku'] = sku.upper()
        item['designer'] = 'PHILIPP PLEIN'

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            if item['sku'] in img and img not in item['images']:
                item['images'].append(img)
        item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description.extract() 
        desc_li = []
        for desc in description:
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        sizes1 = sizes.extract()
        
        for s in sizes1:
            item['originsizes'].append(s.strip())
        if len(item['originsizes']) == 0 and kwargs['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[@class="price-sales"]/text()').extract()
        listprice = prices.xpath('.//span[@class="price-standard"]/text()').extract()

        try:
            item['originsaleprice'] = saleprice[0].strip()
            item['originlistprice'] = listprice[0].strip()
        except:
            item['originsaleprice'] = item['originlistprice'] = saleprice[0].strip()

    def _page_num(self, pages, **kwargs): 
        page_num = 60
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = response_url.replace('start=0','start='+str(i*60))
        return url

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="b-pdp-thumbnail_list"]/div/img/@src').extract()
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()        
        fits = []
        desc_li = []
        if len(infos)>1:
            for info in infos:
                if info.strip() and info.strip() not in fits and ('cm' in info.strip().lower() or ' mm' in info.strip().lower() or '(mm' in info.strip().lower()):
                    fits.append(info.strip())
        elif len(infos)==1:
            descs = infos[0].split('.')
            skip = False
            for i in range(len(descs)):            
                if skip:
                    try:
                        num1 = int(descs[i][-1])
                        num2 = int(descs[i+1][0])
                        desc_li[-1] = desc_li[-1] + '.' + descs[i+1]
                    except:
                        skip = False
                    continue
                if 'cm' in descs[i] or '(mm' in descs[i] or 'Measures' in descs[i] or ' mm' in descs[i]:
                    try:
                        try:
                            num1 = int(descs[i][-1])
                            num2 = int(descs[i+1][0])
                            desc = descs[i] + '.' + descs[i+1]
                            skip = True
                        except:
                            num1 = int(descs[i][0])
                            num2 = int(descs[i-1][-1])
                            desc = descs[i-1] + '.' + descs[i]
                    except:
                        desc = descs[i]
                    desc_li.append(desc.strip())

        size_info = '\n'.join(fits+desc_li)
        return size_info    

        
_parser = Parser()

def mysortkey(i):
    r = 100
    if '_ses' in i:
        r = 0
    if '_sf' in i:
        r = 0
    if '_stp' in i:
        r = 1
    if '_s34' in i:
        r = 2
    if '_sbt' in i:
        r = 3
    if '_d' in i:
        r = 100
    return r

class Config(MerchantConfig):
    name = "plein"
    merchant = "PHILIPP PLEIN"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[contains(@class,"b-product_tile-swatches-item")]',
            designer = './/div[@class="shop-page-tile-description"]/span[@class="h2"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add-to-cart"]', _parser.checkout)),
            ('sku',('//span[@itemprop="productID"]/text()',_parser.sku)),
            ('color','//span[@class="color selected-value"]/text()'),
            ('name', '//div[@class="b-pdp-product_name"]/text()'),  
            ('images', ('//div[@class="b-pdp-thumbnail_list"]/div/img/@src | //div[@class="b-pdp-thumbnail_list js-pdp-thumbnails"]/div/img/@src', _parser.images)),
            ('description', ('//div[contains(@class,"b-pdp-product_description")]//div[@class="b-pdp-accordeon_content toggle-content"]//text()',_parser.description)),
            ('sizes', ('//ul[@class="b-swatches-list size"]//li[contains(@class,"selectable")]/a/div/text()', _parser.sizes)), 
            ('prices', ('//div[@class="product-price"]', _parser.prices)),

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
            size_info_path = '//div[@class="b-pdp-accordeon_content toggle-content"]/text()',
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.plein.com/us/women/accessories/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false",

            ],

            c = [
                "https://www.plein.com/us/women/clothing/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false",

            ],
            s = [
                "https://www.plein.com/us/women/shoes/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false",
            ],
            b = [
                "https://www.plein.com/us/women/bags/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false"
            ],
        ),
        m = dict(
            a = [
                "https://www.plein.com/us/men/accessories/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false"
            ],
            b = [
                "https://www.plein.com/us/men/bags/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false",
            ],
            c = [
                "https://www.plein.com/us/men/clothing/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false",

            ],
            s = [
                "https://www.plein.com/us/men/shoes/?prefn1=hasPicture&prefn2=isBlocked&pmin=1.00&sz=60&start=0&format=page-element&prefv1=true&prefv2=false",

            ],


        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = 'www.plein.com/us/',
            cookies = {'selectedCountry':'US'}

            ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = 'www.plein.cn/cn/',
            cookies = {
                'selectedCountry':'CN',
                'selectedLocale':'en_CN',
                'siteID':'PhilippPleinASIA'
            },
            # translate = [('www.plein.com','www.plein.cn'),('us/women/','cn/women/women-'),('us/men/','cn/men/men-')]
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'www.plein.com/gb/',
            cookies = {
                'selectedCountry': 'GB',
                'selectedLocale': 'en_GB',
                'siteID': 'PhilippPleinEU'
            }
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.plein.com/jp/',
            thousand_sign='.',
            cookies = {
                'selectedCountry': 'JP',
                'selectedLocale': 'en_JP',
                'siteID': 'PhilippPleinASIA'
            }
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.plein.com/kr/',
            thousand_sign='.',
            cookies = {
                'selectedCountry': 'KR',
                'selectedLocale': 'en_KR',
                'siteID': 'PhilippPleinASIA'
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.plein.cn/sg/',
            thousand_sign='.',
            cookies = {
                'selectedCountry': 'SG',
                'selectedLocale': 'en_SG',
                'siteID': 'PhilippPleinASIA'
            }

        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'www.plein.cn/hk/',
            cookies = {
                'selectedCountry': 'HK',
                'selectedLocale': 'en_HK',
                'siteID': 'PhilippPleinASIA'
            }

        ),
        RU = dict(
            currency = 'RUB',
            thousand_sign='.',
            currency_sign = '\u0440\u0443\u0431',
            country_url = 'www.plein.com/ru/',
            cookies = {
                'selectedCountry': 'RU',
                'selectedLocale': 'en_RU',
                'siteID': 'PhilippPleinRU'
            }
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = 'www.plein.com/ca/',
            cookies = {
                'selectedCountry': 'CA',
                'selectedLocale': 'en_CA',
                'siteID': 'PhilippPleinUS'
            }
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.plein.com/au/',
            thousand_sign='.',
            cookies = {
                'selectedCountry': 'AU',
                'selectedLocale': 'en_AU',
                'siteID': 'PhilippPleinASIA'
            }
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.plein.com/de/',
            thousand_sign='.',
            cookies = {
                'selectedCountry': 'DE',
                'selectedLocale': 'en_DE',
                'siteID': 'PhilippPleinEU'
            }
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.plein.com/no/',
            thousand_sign='.',
            cookies = {
                'selectedCountry': 'NO',
                'selectedLocale': 'en_NO',
                'siteID': 'PhilippPleinEU'
            }
        ),

        )