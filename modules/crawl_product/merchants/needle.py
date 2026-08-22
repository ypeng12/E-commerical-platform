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
        num_data = int(data.extract_first().strip().lower().split("of")[-1].split("results")[0].replace(',',''))/50 +1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '%s'%(i)
        return url

    def _sku(self, sku_data, item, **kwargs):
        json_data = json.loads(sku_data.extract_first().split("Shopify.product = ")[-1].rsplit(';', 1)[0])
        item['sku'] = json_data['variants'][0]['sku'].rsplit('-', 1)[0]
        item['name'] = json_data['title']
        item['designer'] = json_data['vendor']
        description = etree.HTML(json_data['description'])
        if description:
            desc_li = description.xpath('//p/text()')
        item['description'] = '\n'.join(desc_li)
        item['color'] = json_data['variants'][0]['option1']
        item['tmp'] = json_data

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['images']
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        json_sizes = item['tmp']['variants']
        size_li = []            
        for size in json_sizes:
            if size['available']:
                size_li.append(size['option2'].strip())
        if not size_li and item['category'] in ['a','b']:
            size_li.append('IT')
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        prices = item['tmp']
        if prices['compare_at_price']:
            item['originlistprice'] = str(prices['compare_at_price'])[:-2] + '.' + str(prices['compare_at_price'])[-2:]
            item['originsaleprice'] = str(prices['price'])[:-2] + '.' + str(prices['price'])[-2:]
        else:
            item['originlistprice'] = str(prices['price'])[:-2] + '.' + str(prices['price'])[-2:]
            item['originsaleprice'] = str(prices['price'])[:-2] + '.' + str(prices['price'])[-2:]

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="thumbnail-image"]/div/img/@src').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)

        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="woocommerce-result-count"]/text()').extract_first().strip().lower().split("of")[-1].split("results")[0].replace(',',''))
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'Dimensions' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or '(LxWxH)' in info or 'height' in info.lower() or ' x ' in info or ' mm.' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 

_parser = Parser()


class Config(MerchantConfig):
    name = 'needle'
    merchant = 'Needle & Thread'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="woocommerce-result-count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//*[@data-source="main_loop"]//div[@class="product-information"]',
            designer = './div[@class="woodmart-product-brands-links"]/a/text()',
            link = './h3/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product-single__actions"]/input[@value="Add to bag"]', _parser.checkout)), 
            ('sku',('//script[contains(text(),"Shopify.product = ")]/text()',_parser.sku)),
            ('images',('//*[@class="woocommerce-product-gallery__image"]/a/@href',_parser.images)),
            ('prices', ('//div[@class="nosto_product"]', _parser.prices)),
            ('sizes',('//select[@id="pa_size"]/option/text()',_parser.sizes)),
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
            size_info_path = '//div[@id="tab-description"]//div[@class="woodmart-scroll-content"]/div/div[1]//div[@class="wpb_wrapper"]//p/text()|//div[@id="tab-description"]//div[@class="woodmart-scroll-content"]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            c = [
                'https://us.needleandthread.com/collections/all-womenswear?page='
            ],
        ),
        g = dict(
            c = [
                'https://us.needleandthread.com/collections/kids?page='
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
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
        )
#      
        )

        


