from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if 'Add to bag' in checkout.extract_first():
            return False
        else:
            return True

    def _sku(self, sku_data, item, **kwargs):
        sku_data = json.loads(sku_data.extract_first())
        sku = str(sku_data['sku'])
        if sku.lower() in item['url'].lower():
            item['sku'] = sku.upper()
        else:
            item['error'] = 'sku error'

        item['name'] = sku_data['name'].upper()
        item['designer'] = sku_data['brand']['name'].upper()
        item['color'] = sku_data['color']
        item['description'] = sku_data['description']
          
    def _images(self, res, item, **kwargs):
        images = res.extract()
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append('https://www.alexandalexa.com' + img)
        item['images'] = img_li
        item['cover'] = img_li[0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.replace("\xa0",' - ').replace('\nMore details\nLess details','')
        item['color'] = item['color'].upper()

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        for size in sizes_data.extract():
            out_sizes = ["out of stock","select","notify me"]
            if any([out in size.lower() for out in out_sizes]):
                continue
            item['originsizes'].append(size.strip())

        if item['category'] in ['a','b'] and not item['originsizes']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//p[@class="c-price__value--current"]/text()').extract()
        listPrice = prices.xpath('.//span[@class="c-price__value--old"]/text()').extract()

        if not listPrice:
            listPrice = salePrice

        item['originsaleprice'] = salePrice[0].strip()
        item['originlistprice'] = listPrice[0].strip()

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="img"]/img/@srcset')
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return images_li

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[contains(@class,"relatedItem")]/@data-ytos-related').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return
        item['main_prd'] = response.meta.get('sku')
        item['cover'] = response.xpath('//div[@class="productImages"]/ul/li/img/@src').extract_first()
        item['products']= [('COD'+str(x)) for x in outfits]
        yield item


    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas_1 = response.xpath(swatch_path['path'])
        ajaxurl = 'http://www.alexandermcqueen.com/yTos/api/Plugins/ItemPluginApi/GetCombinationsAsync/?siteCode=ALEXANDERMCQUEEN_US&code10='+kwargs['sku'].replace('COD','')
        res = getwebcontent(ajaxurl)
        obj = json.loads(res)
        datas = obj['Colors']
        swatches = []

        for data in datas:
            pid = data['Code10']
            swatch = 'COD'+pid
            swatches.append(swatch)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):

        infos = response.xpath(size_info['size_info_path'])
        label = infos.xpath('./span[@class="label"]/text()').extract_first()
        label = label + ':' if label else ''
        fits = []
        for info in infos.xpath('.//div[@class="localizedAttributes"]/div'):
            row_infos = info.xpath('./span/text()').extract()
            row_fits = []
            for row_info in row_infos:
                if row_info.strip() and row_info.strip() not in row_fits:
                    row_fits.append(row_info.strip())
            row_info = ' '.join(row_fits) + ','
            if row_info not in fits:
                fits.append(row_info)
        size_info = label + ' '.join(fits)
        size_info = size_info[:-1]
        return size_info
        
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="c-filters__count"]//text()').extract_first().lower().split('items')[0].replace(' ','').strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'mcqueen'
    merchant = 'McQueen'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//html',
            # list_url = _parser.list_url,
            items = '//article',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-action="addProductToCart"]/span[@data-ref="addToCartHelpSRHover"]/text()', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('images', ('//div[@class="c-productcarousel"]/ul/li/button/img/@data-src', _parser.images)),
            # ('description', ('//p[@class="product-artno"]//text()',_parser.description)), # TODO:
            ('sizes', ('//select[@data-action="selectProductSize"]/option[contains(@data-attr-value,"")]/text()', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=62605,            
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[contains(@class,"relatedItem")]//a/img',
            img_base = 'https://cdn.yoox.biz/items/%(img_code)s/%(sku)s_10_g_f.jpg'
            ),
        image = dict(
            # image_path = '//div[@data-bind="productImages"]//li/button/img/@src',
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="fittingWrapper"]',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.alexandermcqueen.com/en-us/men/accessories?start=0&sz=1000',
            ],
            b = [
                'https://www.alexandermcqueen.com/en-us/men/bags?start=0&sz=1000'
            ],
            c = [
                'https://www.alexandermcqueen.com/en-us/men/ready-to-wear?start=0&sz=1000'
            ],
            s = [
                'https://www.alexandermcqueen.com/en-us/men/shoes?start=0&sz=1000'
            ],
        ),
        f = dict(
            a = [
                'https://www.alexandermcqueen.com/en-us/women/accessories?start=0&sz=1000',
            ],
            b = [
                'https://www.alexandermcqueen.com/en-us/women/handbags?start=0&sz=1000'
            ],
            c = [
                'https://www.alexandermcqueen.com/en-us/women/ready-to-wear?start=0&sz=1000'
            ],
            s = [
                'https://www.alexandermcqueen.com/en-us/women/shoes?start=0&sz=1000'
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
            country_url = '/en-us/',
        ),
        # CN = dict(
        #     area='CN',
        #     language = 'ZH', 
        #     currency = 'CNY',
        #     currency_sign = u'\xa3',
        #     country_url = '.cn/cn/',
        # ),
        # JP = dict(
        #     area='AS',
        #     language = 'JP',
        #     currency = 'JPY',
        #     currency_sign = u'\xa3',
        #     country_url = '.com/jp/',
        # ),
        # KR = dict( 
        #     area='AS',
        #     currency = 'KRW',
        #     currency_sign = u'\xe2',
        #     # thousand_sign = '.',
        #     country_url = '.com/kr/',

        # ),
        # HK = dict(
        #     area='AS',
        #     currency = 'HKD',
        #     country_url = '.com/hk/',
        #     currency_sign = 'HK$',
        # ),
        # SG = dict(
        #     area='AS',
        #     currency = 'SGD',
        #     # discurrency = 'USD',
        #     country_url = '.com/sg/',
        #     currency_sign = 'SG$',
        #     # thousand_sign = '.',
        # ),
        GB = dict(
            area='EU',
            currency = 'GBP',
            country_url = '/en-gb/',
            currency_sign = '\xa3',
        ),
        # CA = dict(
        #     currency = 'CAD',
        #     country_url = '.com/ca/',
        #     discurrency = 'USD',
        # ),
        # AU = dict(
        #     area='EU',
        #     currency = 'AUD',
        #     country_url = '.com/au/',
        #     currency_sign = u'AU$',

        # ),
        # DE = dict(
        #     area='EU',
        #     currency = 'EUR',
        #     thousand_sign = '.',
        #     country_url = '.com/de/',
        # ),
        # NO = dict(
        #     area='EU',
        #     currency = 'NOK',
        #     country_url = '.com/no/',
        #     discurrency = 'EUR',
        #     thousand_sign = '.',
        # ),
        # RU = dict(
        #     area='EU',
        #     language = 'RU',
        #     currency = 'RUB',
        #     country_url = '.com/ru/',
        #     currency_sign = u'EUR',
        #     thousand_sign = u'\xa0',
        #     discurrency = 'EUR',
        # ),
        )

        


