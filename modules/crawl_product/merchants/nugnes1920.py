from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):
    def _checkout(self, scripts, item, **kwargs):
        script_str = scripts.extract_first()
        script_str = script_str.split('product:')[-1].strip().split('cart:')[0].strip()[:-1] 
        script_dict = json.loads(script_str)
        item['tmp'] = script_dict
        if not script_dict or script_dict['available'] == False:
            return True
        else:
            item['tmp'] = script_dict
            return False

    def _page_num(self, data, **kwargs):
        pages = (int(data.strip()))
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?page')[0] + '?page='+str(i)
        return url

    def _sku(self, data, item, **kwargs):
        code = data.extract_first().upper().split('CODE:')[-1].strip()
        sku = item['url'].split('?')[0].split('_')[-1].strip().upper()
        if sku.startswith(code):
            item['sku'] = sku
        else:
            item['sku'] = ''

    def _designer(self, data, item, **kwargs):
        item['designer'] = item['tmp']['vendor']
        item['name'] = item['tmp']['title']
          
    def _images(self, images, item, **kwargs):        
        img_li = item['tmp']['images']
        images = []
        for img in img_li:
            img = img.replace('//','https://')
            if img not in images:
                images.append(img)

        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = item['tmp']['variants']
        size_li = []

        for size in sizes:
            if size['available'] == True:
                if size["title"].replace('M','').isdigit() and size["title"].endswith('M'):
                    osize = size["title"].replace('M','.5')
                else:
                    osize = size["title"]
                if item['category'] in ['c','s'] and osize.replace('.','').isdigit() and float(osize) < 20:
                    osize = 'UK' + osize
                size_li.append(osize)

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//span[@class="was_price"]/span[@class="money"]/text()').extract()[0]
            saleprice = prices.xpath('.//span[contains(@class,"current_price")]/span[@class="money"]/text()').extract()[0]
        except:
            listprice = prices.xpath('.//span[contains(@class,"current_price")]/span[@class="money"]/text()').extract()[0]
            saleprice = prices.xpath('.//span[contains(@class,"current_price")]/span[@class="money"]/text()').extract()[0]

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _description(self, description1, item, **kwargs):
        description = description1.xpath('.//div[@class="product-page__description"]//text()').extract() + description1.xpath('.//div[@class="product-page__materials"]//text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip().replace('  ','')
            if not desc:
                continue
            desc_li.append(desc.replace('  ','').strip())
        description = '\n'.join(desc_li)
        item['description'] = description.replace(' \n \n','\n')
        color = description1.xpath('.//div[@class="product-page__color"]/text()').extract()
        color = '-'.join(color)
        if 'color:' in color.lower():
            item['color'] = color.lower().split('color:')[-1].split('-')[0].split('"')[0].upper().strip()
        else:
            item['color'] = ''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="gallery__image-container ratio-container"]/img/@data-src').extract()
        img_li = []
        for img in imgs:
            img = 'https:' + img if 'http' not in img else img
            img = img.replace('100x', '400x')
            if img not in img_li:
                img_li.append(img)

        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()[0].split('\n')
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info.lower() or 'length' in info.lower() or 'diameter' in info.lower() or '"H' in info or '"W' in info or '"D' in info or 'wide' in info.lower() or 'weight' in info.lower() or 'Approx' in info or 'Model' in info or 'height' in info.lower() or 'depth' in info.lower() or 'width' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace(',','.'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = 'nugnes1920'
    merchant = 'Nugnes 1920'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@id="shop-products"]/@data-max-page', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"product-card")]',
            designer = './@data-vendor',
            link = './a[contains(@class,"product-card__link")]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[contains(text(),"mwMotivatorObjects")]/text()', _parser.checkout)),
            ('designer', ('//html',_parser.designer)),            
            ('sku', ('//div[@class="product-page__sku"]//text()', _parser.sku)),
            ('images', ('//html', _parser.images)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="main"]//p[@class="product-page__price"]', _parser.prices))
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-page__materials"]//text()',

            ),
        designer = dict(

            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://us.nugnes1920.com/collections/accessories-man?page="
            ],
            b = [
                'https://us.nugnes1920.com/collections/bag-man?page=',
            ],
            c = [
                "https://us.nugnes1920.com/collections/clothing-man?page="
            ],
            s = [
                "https://us.nugnes1920.com/collections/shoes-man?page="
            ],
        ),
        f = dict(
            a = [
                "https://us.nugnes1920.com/collections/accessories-woman?page="
            ],
            b = [
                'https://us.nugnes1920.com/collections/bag-woman?page=',
            ],
            c = [
                "https://us.nugnes1920.com/collections/clothing-woman?page="
            ],
            s = [
                "https://us.nugnes1920.com/collections/shoes-woman?page="
            ],

        params = dict(
            page = 1,
            ),
        ),

        country_url_base = 'us.'
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = 'us.'
            ),
        CN = dict(
            area = 'AS',
            currency = 'CNY',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'asia.'
        ),
        JP = dict(
            area = 'AS',
            currency = 'JPY',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'asia.',
        ),
        KR = dict(
            area = 'AS',
            currency = 'KRW',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'asia.',
        ),
        SG = dict(
            area = 'AS',
            currency = 'SGD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'asia.',
        ),
        HK = dict(
            area = 'AS',
            currency = 'HKD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'asia.',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = 'uk.',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'world.',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'world.',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'www.',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'world.',
        ),

        )

        


