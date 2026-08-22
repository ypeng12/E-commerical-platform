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
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_data = int(data.lower().split('of')[-1].strip())
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = i
        url = urljoin(response_url.split('?')[0], '?currPage=%s'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().split("code:**")[-1].split('**')[0].strip().upper()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

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
        
    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="old"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[@class="new"]/text()').extract()[0]
        except:
            item['originlistprice'] = prices.xpath('./@content').extract()[0]
            item['originsaleprice'] = prices.xpath('./@content').extract()[0]
    def _color(self, color, item, **kwargs):
        item['color'] = color.extract_first().upper()


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="slide"]/a/@href').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath("//div[@class='pager']/div/span[contains(text(),'age')]/text()").extract_first().lower().split('of')[-1].strip())*36
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'monti'
    merchant = 'Monti Boutique'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ("//div[@class='pager']/div/span[contains(text(),'age')]/text()",_parser.page_num),
            list_url = _parser.list_url,
            items = '//ol[@class="products-list clearfix"]/li//div[@class="data"]',
            designer = './/span[@class="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[contains(@class,"js-gtm-detail-add-to-cart")]', _parser.checkout)),
            ('images',('//div[@class="slide"]/a/@href',_parser.images)), 
            ('sku',('//meta[@name="description"]/@content',_parser.sku)),
            ('name', '//h2[@itemprop="name"]/text()'),
            ('designer','//@data-gtm-brand'),
            ('color',('//@data-gtm-variant',_parser.color)),
            ('description', ('//div[@id="description-tab"]//text()',_parser.description)),
            ('prices', ('//span[@itemprop="price"]', _parser.prices)),
            ('sizes',('//select[@id="idTaglia"]/option/text()',_parser.sizes)),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.montiboutique.com/en-US/men/accessories?currPage=",
                "https://www.montiboutique.com/en-US/men/jewels?currPage="
            ],
            b = [
                "https://www.montiboutique.com/en-US/men/bags?currPage="
            ],
            c = [
                'https://www.montiboutique.com/en-US/men/clothing?currPage='
            ],
            s = [
                "https://www.montiboutique.com/en-US/men/shoes?currPage=",
                ],
        ),
        f = dict(
            a = [
                "https://www.montiboutique.com/en-US/women/accessories?currPage=",
                "https://www.montiboutique.com/en-US/women/jewels?currPage="
            ],
            b = [
                "https://www.montiboutique.com/en-US/women/bags?currPage="
            ],
            c = [
                'https://www.montiboutique.com/en-US/women/clothing?currPage='
            ],
            s = [
                "https://www.montiboutique.com/en-US/women/shoes?currPage=",
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
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLoc': 'id=237&nome=United States',
            }
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            cookies={
            'TassoCambio': 'IsoTassoCambio=CNY',
            'geoLoc': 'id=168&nome=China',
            }
            
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            cookies={
            'TassoCambio': 'IsoTassoCambio=JPY',
            'geoLoc': 'id=105&nome=Japan',
            }
            
        ),
        KR = dict( 
            currency = 'KRW',
            cookies={
            'TassoCambio': 'IsoTassoCambio=KRW',
            'geoLoc': 'id=202&nome=South Korea',
            }
        ),
        HK = dict(
            currency = 'HKD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=HKD',
            'geoLoc': 'id=94&nome=Hong Kong',
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=USD',
            'geoLoc': 'id=196&nome=Singapore',
            }
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies={
            'TassoCambio': 'IsoTassoCambio=GBP',
            'geoLoc': 'id=235&nome=United Kingdom',
            }
        ),
        CA = dict(
            currency = 'CAD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=CAD',
            'geoLoc': 'id=37&nome=Canada',
            }
        ),
        AU = dict(
            currency = 'AUD',
            cookies={
            'TassoCambio': 'IsoTassoCambio=AUD',
            'geoLoc': 'id=12&nome=Australia',
            }
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies={
            'TassoCambio': 'IsoTassoCambio=EUR',
            'geoLoc': 'id=78&nome=Germany',
            }
        ),

        NO = dict(
            currency = 'NOK',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies={
            'TassoCambio': 'IsoTassoCambio=EUR',
            'geoLoc': 'id=160&nome=Norway',
            }
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies={
            'TassoCambio': 'IsoTassoCambio=EUR',
            'geoLoc': 'id=180&nome=Russia',
            }
        )
#      
        )

        


