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

    def _page_num(self, items, **kwargs):         
        page_num = int(items)/36 + 1
        return page_num

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].split()[-1].strip()

    def _images(self, html, item, **kwargs):
        images = html.xpath('//img[@itemprop="image"]/@content').extract()   
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
            if desc.strip():
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        orisizes = sizes.extract()
        sizes = []
        for osize in orisizes:
            if not osize.replace('IT','').strip().isdigit():
                size = osize.replace('IT','').strip()
            else:
                size = osize
            sizes.append(size)
        item['originsizes'] = sizes
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="detail__price--new"]/text()').extract()
        regularPrice = prices.xpath('.//span[@class="detail__price--old"]/text()').extract()
        if len(salePrice) == 0:
            salePrice = prices.xpath('./text()').extract_first()  
            item['originlistprice'] = salePrice.strip()
            item['originsaleprice'] = salePrice.strip()        
        else:
            try:
                item['originlistprice'] = regularPrice[0].strip()
                item['originsaleprice'] = salePrice[0].strip()
            except:
                item['error'] = "price can't ba processed"

    def _color(self, data, item, **kwargs):
        try:
            item['color'] = data.xpath('.//div[@class="color single-line"]/text()').extract()[-1].strip()
        except Exception as e:
            item['color'] = ''

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//img[@itemprop="image"]/@content').extract()       
        img_li = []  
        for img in images:
            if img not in img_li:
                img_li.append(img)

        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = ' '.join(fits)
        return size_info
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="pager__summary"]/span/b[last()]//text()').extract_first().replace('"','').strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "al"
    merchant = "Al Duca d'Aosta"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pager__summary"]/span/b[last()]//text()',_parser.page_num),
            items = '//div[contains(@class,"products-list")]/div',
            designer = './/span[@class="product__brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@class="button button--primary"]', _parser.checkout)),
            ('sku', ('//b[@itemprop="sku"]/text()',_parser.sku)),
            ('name', '//*[@itemprop="name"]/text()'),
            ('designer', '//h1[@itemprop="brand"]/span[@itemprop="name"]/a/text() | //span[@itemprop="brand"]/span[@itemprop="name"]/a/text()'),
            ('color',('//html',_parser.color)),
            ('images', ('//html', _parser.images)),
            ('description', ('//div[@itemprop="description"]/text()', _parser.description)),
            ('sizes', ('//div[@class="detail__size"]/label/text()', _parser.sizes)), 
            ('prices', ('//span[@itemprop="price"]', _parser.prices)),
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
            size_info_path = '//div[@class="measures single-line"]//text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.alducadaosta.com/us/men/accessories?currPage=",
            ],
            b = [
                "https://www.alducadaosta.com/us/men/bags?currPage=",
            ],
            c = [
                 "https://www.alducadaosta.com/us/men/clothing?currPage=",
            ],
            s = [
                "https://www.alducadaosta.com/us/men/shoes?currPage=",
            ],
        ),
        f = dict(
            a = [
                'https://www.alducadaosta.com/us/women/accessories?currPage='
            ],
            b = [
                'https://www.alducadaosta.com/us/women/bags?currPage=',
               ],
            c = [
                'https://www.alducadaosta.com/us/women/clothing?currPage='
            ],
            s = [
                'https://www.alducadaosta.com/us/women/shoes?currPage='
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
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = '/us/',
            cookies = {'geoLoc':'id=237&nome=USA&countryShort=us'}
            
            ),
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = 'USD',
        #     country_url = '/row-en/',

        # ),
        JP = dict(
            currency = 'JPY',
            thousand_sign = '.',
            currency_sign = '\xa5',
            country_url = '/jp/',
            cookies = {'geoLoc':'id=105&nome=Japan&countryShort=jp'}

        ),
        KR = dict(
            currency = 'KRW',
            thousand_sign = '.',
            currency_sign = '\u20a9',
            country_url = '/kr/',
            cookies = {'geoLoc':'id=202&nome=South Korea&countryShort=kr'}            

        ),
        SG = dict(
            currency = 'SGD',
            thousand_sign = '.',
            discurrency = 'EUR',
            country_url = '/sg/',
            currency_sign = '\u20ac',
            cookies = {'geoLoc':'id=196&nome=Singapore&countryShort=sg'}            

        ),
        HK = dict(
            currency = 'HKD',
            thousand_sign = '.',
            currency_sign = 'HK$',
            country_url = '/hk/',
            cookies = {'geoLoc':'id=94&nome=Hong Kong&countryShort=hk'}        

        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/gb/',
            cookies = {'geoLoc':'id=235&nome=United Kingdom&countryShort=gb'}

        ),
        RU = dict(
            currency = 'RUB',
            thousand_sign = '.',
            discurrency = 'EUR',
            country_url = '/ru/',
            currency_sign = '\u20ac',
            cookies = {'geoLoc':'id=180&nome=Russia&countryShort=ru'}

        ),
        CA = dict(
            currency = 'CAD',            
            country_url = '/ca/',
            currency_sign = 'C$',
            cookies = {'geoLoc':'id=37&nome=Canada&countryShort=ca'}

        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = "A$",
            country_url = '/au/',
            cookies = {'geoLoc':'id=12&nome=Australia&countryShort=au'}            

        ),
        DE = dict(
            currency = 'EUR',
            thousand_sign = '.',
            currency_sign = '\u20ac',
            country_url = '/de/',
            cookies = {'geoLoc':'id=78&nome=Germany&countryShort=de'}              

        ),
        NO = dict(
            currency = 'NOK',
            thousand_sign = '.',
            discurrency = 'EUR',
            country_url = '/no/',
            currency_sign = '\u20ac',
            cookies = {'geoLoc':'id=160&nome=Norway&countryShort=no'}
        ),

        )

        


