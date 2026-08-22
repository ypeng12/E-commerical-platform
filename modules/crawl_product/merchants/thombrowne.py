from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'VALEXTRA'

    def _images(self, images, item, **kwargs):
        images = images.extract()
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append(img)   
        item['cover'] = img_li[0]
        item['images'] = img_li
        
    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []
        if item['category'] in ['a','b']:
            if not sizes:
                size_li.append('IT')
            else:
                size_li = sizes
        else:
            for size in sizes:
                if size.strip() not in size_li:
                    size_li.append(size.strip())
        item['originsizes'] = size_li

    def _prices(self, data, item, **kwargs):
        price = data.extract_first()
        item['originlistprice'] = price
        item['originsaleprice'] = price
        item['color'] = item['color'].upper()
        

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
      
_parser = Parser()



class Config(MerchantConfig):
    name = 'thombrowne'
    merchant = 'Thom Browne'
    headers = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586',
    'Cookie': '__cfduid=d222a39fe9ef2d666ff268376eb9605db1550643427; cf_clearance=3fc9b24fccd6188e606711e159efa74e8948d1f9-1550643432-2592000-150; _gcl_au=1.1.1179160605.1550643396; _fbp=fb.1.1550643399411.2102279016; stc114492=tsa:1550643399483.580966426.0916483.08659306882542345.:20190220064753|env:1%7C20190323061639%7C20190220064753%7C2%7C1039184:20200220061753|uid:1550643399482.1273827182.532954.114492.1409237181.:20200220061753|srchist:1039184%3A1%3A20190323061639:20200220061753; _ga=GA1.2.1317439296.1550643398; _gid=GA1.2.868547332.1550643398; dfUserSub=%2Fus; ss=SSRiI5as0-OiuOaMJkmuFXlBR1Rm2UHUWGqdfXzacGV2ZWXYWeolzCbtjJH9pI6W7kgG6-9ZzkbafkxReBsf-7sLNAUcRgJtIoUs1i_ceDeWcApPWIcBCxhOyrXgBAgmG--lzlS4NjkzwxN0wl_Xh_XzRVhVgMov0KCMkJuISKwJfI8QK-iloDfUBN__5p8W-K7YwlMEr9UbT1BDQr98dg; csi=5e761c34-cb4e-4903-a8ae-8d037af71f57; _ga=GA1.1.1317439296.1550643398; _gid=GA1.1.868547332.1550643398; gender=1; cookieAlert=true; _gat_UA-70424015-1=1',
    'Referer': 'https://www.thombrowne.com/us/shopping/anchor-sequin-narrow-sport-coat-13253018',
    'Host': 'www.thombrowne.com',
    'X-NewRelic-ID': 'VQUCV1ZUGwIFVlBRDgcA',
    'X-Requested-With': 'XMLHttpRequest',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@class="pages"]//li[last()-1]//text()',
            items = '//div[@class="category-products "]/ul/li',
            designer = './/div[@class="sc-dyGzUR kCMbOt sc-hBbWxd cqWPzI"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-test="ProductDetailPage-outOfStockButton"]', _parser.checkout)),
            ('sku', '//span[@itemprop="sku"]/text()'),
            ('name', '//meta[@property="og:title"]/@content'),    # TODO: path & function
            ('designer', ('//html',_parser.designer)),
            ('images', ('//div[@class="product-image-gallery"]/img/@src', _parser.images)),
            ('color','//span[@itemprop="color"]/text()'),
            ('description', ('//meta[@name="twitter:description"]/@content',_parser.description)),
            ('sizes', ('//ul[@class="size-list product-variation-list gl_clear-fix"]/li/a[not(contains(@title,"Check availability in our stores"))]/text()', _parser.sizes)),
            ('prices', ('//span[@itemprop="price"]/@content', _parser.prices))
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(
            ),
        designer = dict(

            ),
        )



    list_urls = dict(
        f = dict(
            a = [

            ],
            b = [



            ],
            c = [

            ],
            s = [
            ],
        ),
        m = dict(
            a = [
            ],
            b = [

            ],
            c = [
            ],
            s = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/en-us/',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = '/en-us/',
            currency_sign = '$',
            ),
        # CN = dict(
        #     currency = 'CNY',
        #     country_url = '/eu/en/',
        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     country_url = '.jp/',
        #     translate = [
        #         ('women/new-in/new-bags/','products/list.php?category_id=13'),
        #         ('women/top-handles-handbags/','products/list.php?category_id=59'),
        #         ('women/shoulder-bags/','products/list.php?category_id=57'),
        #         ('women/totes/','products/list.php?category_id=16'),
        #         ('women/clutches/','products/list.php?category_id=17'),
        #         ('women/mini/','products/list.php?category_id=58'),
        #         ('women/accessories-add-ons/','products/list.php?category_id=60'),
        #         ('men/briefcases/','products/list.php?category_id=22'),
        #         ('men/document-holders-portfolios-pouches/','products/list.php?category_id=39'),
        #         ('men/shoulder-bags/','products/list.php?category_id=23'),

        #     ]

        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     country_url = '/eu/en/',

        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     country_url = '/eu/en/',
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     country_url = '/eu/en/',
        # ),
        GB = dict(
            currency = 'GBP',
            country_url = '/en-gb/',
        ),
        # RU = dict(
        #     currency = 'RUB',
        #     country_url = '/eu/en/',
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     country_url = '/eu/en/',
        # ),
        AU = dict(
            discurrency = 'USD',
            currency = 'AUD',
            country_url = '/en-au/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/en-eu/',
        ),
        # NO = dict(
        #     area = 'NOK',
        #     country_url = '/eu/en/',
        # ),

        )

        


