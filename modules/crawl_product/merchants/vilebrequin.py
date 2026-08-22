from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'VILEBREQUIN'

    def _images(self, images, item, **kwargs):
        images = images.extract()
        img_li = []
        for img in images:
            if 'http' not in img:
                img = 'https://www.vilebrequin.com' + img
            if img not in img_li:
                img_li.append(img)   
        img_li = [x.replace('82x82', '652x652') for x in img_li]  
        item['cover'] = img_li[0]
        item['images'] = img_li
        
    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []
        if item['category'] in ['a','b']:
            if not sizes:
                size_li.append('IT')            
        if sizes:
            for size in sizes:
                if size.strip() not in size_li:
                    size_li.append(size.strip())
        item['originsizes'] = size_li

    def _prices(self, data, item, **kwargs):
        if item['country'].upper() == 'US':
            price = data.xpath('//div[@id="pdpMain"]/script/text()').extract_first().split("price': '")[-1].split("'")[0]
            item['originlistprice'] = price
            item['originsaleprice'] = price
        else:
            pid = item['sku'].split('-')[0]
            color_id = item['sku'].split('-')[-1]
            base_url = 'https://www.vilebrequin.com/eu/en/product-variation?pid=%s&dwvar_%s_color=%s'%(pid,pid,color_id)
            res = requests.get(base_url)
            price = float(res.text.split('data-priceValue="')[-1].split('"')[0])
            
            config = Config()
            country = item['country'].upper()
            currency = config.countries[item['country'].upper()]['currency']
            currency_url = 'https://www.vilebrequin.com/on/demandware.store/Sites-VBQ-EU-Site/en_GB/ContextChooser-Apply'
            data = {
                'country': '%s'%country,
                'currency': '%s'%currency,
                'format': 'ajax',
            }
            res = requests.post(currency_url, data=data)
            rate = float(res.cookies['FiftyOne_Akamai'].split('|')[-1].strip())

            item['originlistprice'] = str(price * rate)
            item['originsaleprice'] = str(price * rate)

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@data-gtm="product-thumbnail"]/img/@src').extract()
        img_li = []
        for img in images:
            if 'http' not in img:
                img = 'https://www.vilebrequin.com' + img
            if img not in img_li:
                img_li.append(img)   
        img_li = [x.replace('82x82', '652x652') for x in img_li]  

        return img_li
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="js-filter-products-number"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number
      
_parser = Parser()



class Config(MerchantConfig):
    name = 'vilebrequin'
    merchant = 'Vilebrequin'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="js-filter-products-number"]/text()',
            items = '//ul[@class="category-subset-row row"]/li',
            designer = './/div[@class="sc-dyGzUR kCMbOt sc-hBbWxd cqWPzI"]/text()',
            link = './/div[@class="product-name"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//ul[@class="size-list product-variation-list gl_clear-fix"]/li/a[not(contains(@title,"Check availability in our stores"))]', _parser.checkout)),
            ('sku', '//input[@id="js-productModel"]/@value'),
            ('name', '//h1[@class="product-detail-name"]/text()'),    # TODO: path & function
            ('designer', ('//html',_parser.designer)),
            ('images', ('//div[@data-gtm="product-thumbnail"]/img/@src', _parser.images)),
            ('color','//a[@class="swatchanchor gl_color-button selected"]/@data-variation'),
            ('description', ('//div[@class="product-description-tab-column col-md-4 col-md-offset-1 col-xs-12 col-xs-offset-0"]/p//text()',_parser.description)),
            ('sizes', ('//ul[@class="size-list product-variation-list gl_clear-fix"]/li/a[not(contains(@title,"Check availability in our stores"))]/text()', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
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
            size_info_path = '//ul[@class="product-description-content-list"]/li/text()',
            ),
        designer = dict(

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )



    list_urls = dict(
        f = dict(
            a = [
                'https://www.vilebrequin.com/us/en/women-accessories-sunglasses/?va=',
                'https://www.vilebrequin.com/us/en/women-accessories-towels/?va=',
                'https://www.vilebrequin.com/us/en/women-accessories-pareos/?va=',
                'https://www.vilebrequin.com/us/en/women-accessories-scarves/?va=',
                'https://www.vilebrequin.com/us/en/women-accessories-hats/?va=',
                'https://www.vilebrequin.com/us/en/women-accessories-watches/?va=',
                'https://www.vilebrequin.com/us/en/accessories-outdoor-accessories/?va=',
            ],
            b = [
                'https://www.vilebrequin.com/us/en/women-accessories-bags/?va=',
                'https://www.vilebrequin.com/us/en/women-accessories-pouches/?va=',
            ],
            c = [
                'https://www.vilebrequin.com/us/en/women-swimwear/?va=',
                'https://www.vilebrequin.com/us/en/women-clothing/?va=',


            ],
            s = [
                'https://www.vilebrequin.com/us/en/women-accessories-shoes/?va='
            ],
        ),
        m = dict(
            a = [
                'https://www.vilebrequin.com/us/en/men-accessories-sunglasses/?va=',
                'https://www.vilebrequin.com/us/en/men-accessories-towels/?va=',
                'https://www.vilebrequin.com/us/en/men-accessories-hats/?va=',
                'https://www.vilebrequin.com/us/en/men-accessories-scarves/?va=',
                'https://www.vilebrequin.com/us/en/men-accessories-belts/?va=',
                'https://www.vilebrequin.com/us/en/men-accessories-watches/?va=',
                'https://www.vilebrequin.com/us/en/accessories-outdoor-accessories/?va=',
            ],
            b = [
                'https://www.vilebrequin.com/us/en/men-accessories-bags/?va=',
                'https://www.vilebrequin.com/us/en/men-accessories-pouches/?va=',
            ],
            c = [
                'https://www.vilebrequin.com/us/en/men-swimwear/?va=',
                'https://www.vilebrequin.com/us/en/men-clothing/?va=',
                'https://www.vilebrequin.com/us/en/men-accessories-boxers/?va=',
            ],
            s = [
                'https://www.vilebrequin.com/us/en/men-accessories-shoes/?va=',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/us/en/',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = '/us/en/',
            currency_sign = '$',
            ),
        CN = dict(
            currency = 'CNY',
            country_url = '/eu/en/',
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '/eu/en/',

        ),
        KR = dict(
            currency = 'KRW',
            country_url = '/eu/en/',

        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/eu/en/',
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '/eu/en/',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/eu/en/',
        ),
        # RU = dict(
        #     currency = 'RUB',
        #     country_url = '/eu/en/',
        # ),
        CA = dict(
            currency = 'CAD',
            country_url = '/eu/en/',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '/eu/en/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/eu/en/',
        ),
        NO = dict(
            area = 'NOK',
            country_url = '/eu/en/',
        ),

        )

        


