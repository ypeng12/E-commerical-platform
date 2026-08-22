from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy
class Parser(MerchantParser):
    
    def _checkout(self, checkout, item, **kwargs):
        if not checkout:
            return True
        else:
            return False

    def _parse_multi_items(self, response, item, **kwargs):
        item['designer'] = response.url.split('?c=')[-1].replace('_',' ')
        item['url'] = response.url.split('?')[0]
        item['originsizes'] = 'IT;'
        item['sizes'] = 'IT'
        if item['color'] == '':
            try:
                item['color'] = response.xpath('//div[@class="sgh-pdp__filter__display"]/text()').extract()[0].upper().strip()
            except:
                item['color'] = ''
        yield item
        colors = response.xpath('//ul[@class="list-unstyled color-list clearfix"]//a/@href').extract()
        for href in colors:
            if href == item['url']:
                continue
            item_color = deepcopy(item)
            result = getwebcontent(href)
            item_color['url'] = href
            html = etree.HTML(result)
            _parser.prices(html, item_color, **kwargs)
            img_li = html.xpath('.//*[@itemprop="image"]/@src') + html.xpath('.//img[@alt="PDP Product Image"]/@src')
            images = []
            for img in img_li:
                if img not in images:
                    if 'http' not in img:
                        img = img.replace('//','https://')
                    images.append(img)
            item_color['cover'] = images[0]
            item_color['images'] = images
            try: 
                item_color['color'] = html.xpath('//ul[@class="list-unstyled color-list clearfix"]//a[@class="selected"]/@title')[0].upper()
            except:
                item_color['color'] = ''
            item_color['sku'] = html.xpath('//p[@class="code"]/text()')[0].strip().split('#')[-1].strip()
            yield item_color

    def _prices(self, prices, item, **kwargs):
        try :
            try:
                item['originlistprice'] = prices.xpath('.//span[@id="listPrice"]/text()').extract()[0].strip()
                item['originsaleprice'] = prices.xpath('.//span[@id="offerPrice"]/text()').extract()[0].strip()
            except:
                item['originsaleprice'] = prices.xpath('.//span[@id="price"]/text()').extract()[0].strip()
                item['originlistprice'] = item['originsaleprice']
        except:
            try:
                item['originlistprice'] = prices.xpath('.//span[@id="listPrice"]/text()')[0].strip()
                item['originsaleprice'] = prices.xpath('.//span[@id="offerPrice"]/text()')[0].strip()
            except:
                item['originsaleprice'] = prices.xpath('.//span[@id="price"]/text()')[0].strip()
                item['originlistprice'] = item['originsaleprice']

    def _images(self, images, item, **kwargs):
        img_li = images.xpath('.//*[@itemprop="image"]/@src').extract() + images.xpath('.//img[@alt="PDP Product Image"]/@src').extract()
        images = []
        for img in img_li:
            if img not in images:
                if 'http:' not in img:
                    img = img.replace('//','https://')
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _name(self, data, item, **kwargs):
        item['name'] = data.extract()[0].split('|')[0].strip().replace('  ','')

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        item['sku'] = sku_data.strip().split('#')[-1].strip()

    def _parse_images(self, response, **kwargs):

        img_li = images.xpath('.//*[@itemprop="image"]/@src').extract() + images.xpath('.//img[@alt="PDP Product Image"]/@src').extract()
        images = []
        for img in img_li:
            if img not in images:
                if 'http:' not in img:
                    img = img.replace('//','https://')
                images.append(img)

        return images

    def _parse_item_url(self, response, **kwargs):
        try:
            pages = int(response.xpath('//span[@class="number-results"]/text()').extract()[0].strip().split('Results')[0].strip())/17
        except:
            pages = 1
        for i in range(1, pages+1):
            url = response.url.replace('default/1/18','default/%s/18'%(i*17))
            result = getwebcontent(url) 
            html = etree.HTML(result)
            for quote in html.xpath('//a[contains(@class,"main-img lazy-container")]'):
                href = quote.xpath('./@href')[0]
                if href is None:
                    continue
                designer=quote.xpath('.//p[@class="brand"]/text()')[0].upper()
                href = href +'?c='+designer.replace(' ','_')
                yield href, designer

_parser = Parser()



class Config(MerchantConfig):
    name = "sunglasshut"
    merchant = "Sunglass Hut"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//div[@class="pagination"]/text()',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            # items = '//ul[contains(@class,"products")]/li',
            # designer = './/div/@data-brand',
            # link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//p[@class="code"]/text()', _parser.checkout)),
            ('sku', ('//p[@class="code"]/text()',_parser.sku)),
            ('name', ('//title/text()',_parser.name)),  
            # ('designer', '//h1[@class="product-brand"]//text()'),
            ('color','//ul[@class="list-unstyled color-list clearfix"]//a[@class="selected"]/@title'),
            ('images', ('//html', _parser.images)),
            ('description', '//*[@class="content"]/p//text()'),
            # ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
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
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.sunglasshut.com/us/womens-sunglasses/default/1/18?pageType="
            ],
        ),
        m = dict(
            a = [
                "https://www.sunglasshut.com/us/mens-sunglasses/default/1/18?pageType="  
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

    )

    parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = '/us/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = '/ca/',
        ),

        GB = dict(
            country_url = '/uk/',
            currency = 'GBP',
            currency_sign = "\u00A3"

        ),
        AU = dict(
            country_url = '/au/',
            currency = 'AUD',
            discurrency = 'USD',

        ),

        DE = dict(
            translate = [('/us/womens-sunglasses/','/de/damen-sonnenbrillen/'),('/us/mens-sunglasses/','/de/herren-sonnenbrillen/')],
            currency = 'EUR',
            currency_sign = '\u20ac',
            language = 'DE',
            thousand_sign = '.',
        ),

        )



