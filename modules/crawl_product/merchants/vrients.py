from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.ladystyle import blog_parser

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_data = 50
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = i
        url = urljoin(response_url.split('?')[0], '?p=%s&vrients=tag'%num)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().split(':')[-1].upper()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        
        images2 = images.xpath('.//script[@id="imagesslider"]/text()').extract_first()
        images2= images2.split('src="')
        imgs = images.xpath('.//div[@class="product-img-box"]//img/@src').extract() + images2
        images = []
        for img in imgs:
            if '"' in img:
                img = img.split('"')[0]

            if img not in images and "http" in img:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('.//div[@id="description"]/p/text()').extract()
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
        listprice = prices.xpath('.//div[@class="product-view"]//p[@class="old-price"]/span/text()').extract()
        saleprice = prices.xpath('.//div[@class="product-view"]//p[@class="special-price"]/span/text()').extract()
        
        if not saleprice:
            listprice = prices.xpath('.//div[@class="product-view"]//span[@class="regular-price"]/span/text()').extract()
            saleprice = listprice

        item['originlistprice'] = listprice[0]
        item['originsaleprice'] = saleprice[0]

    def _color(self, color, item, **kwargs):
        color = color.extract_first().upper()
        item['color'] = color

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//script[@id="imagesslider"]/text()').extract_first()
        cover = response.xpath('//img[@itemprop="image"]/@data-src').extract_first()
        imgs = map(lambda x:x.split('"')[0],imgs.split('src="'))[1:]
        images = [cover]
        for img in imgs:
            if img not in images:
                images.append(img)

        return images

    def _parse_blog(self, response, **kwargs):
        html_origin = response.xpath('//section[@class="post-content"]').extract_first().encode('utf-8')
        title = response.xpath('//hgroup/h1/text()').extract_first()
        key = response.url.split('?')[0].split('/')[-1]
        cover = response.xpath('//section[@class="post-content"]/div[not(@class="share-post")]//img/@src').extract_first()
        cover = cover if cover else ''

        html_parsed = {
            "type": "article",
            "items": []
        }
        img_li = []

        header = response.xpath('//hgroup/h2/text()').extract_first()
        if header:
            headers = {"type": "header"}
            headers['value'] = header
            html_parsed['items'].append(headers)

        for node in response.xpath('//div[contains(@class,"ct-field ct-field-area")]/*'):
            node_html = node.xpath('.').extract_first()
            if node_html.startswith('<p') and node_html != '<p>&nbsp;</p>':
                texts = {"type": "html"} if '<a' not in node_html else {"type": "html_ext"}
                texts['value'] = node_html.strip()
                html_parsed['items'].append(texts)
            elif node_html.startswith('<img'):
                img = node.xpath('./@src').extract_first()
                if img and img not in img_li:
                    img_li.append(img)
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json
        

_parser = Parser()


class Config(MerchantConfig):
    name = 'vrients'
    merchant = 'Vrients'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[contains(@class,"products-grid")]//li',
            designer = './/html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="add-to-cart"]', _parser.checkout)),
            ('images',('//html',_parser.images)), 
            ('sku',('//span[@itemprop="sku"]/text()',_parser.sku)),
            ('name', '//div[@class="product-subname"]/text()'),
            ('designer','//span[@itemprop="brand"]/text()'),
            ('color',('//span[@itemprop="color"]/text()',_parser.color)),
            ('description', ('//html',_parser.description)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//div[@class="input-box"]//ul/li/a/@title',_parser.sizes)),
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
        blog = dict(
            official_uid=359322,
            blog_page_num = '//a[@class="last link-page"]/text()',
            link = '//a[@class="image-link"]/@href',
            method = _parser.parse_blog,
            ),
        )

    blog_url = dict(
        EN = ['https://www.vrients.com/usa/blog?p=']
    )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.vrients.com/usa/accessories.html',

            ],

            c = [
                'https://www.vrients.com/usa/apparel.html?p=2'
            ],
            s = [
                'https://www.vrients.com/usa/footwear.html'
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
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            cur_rate = 1, 
            country_url = '/usa/',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'EUR',
            currency_sign = "EUR",
            country_url = '/china/',
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = "JPY",
            country_url = '/china/',
        ),
        KR = dict(
            currency = 'KRW',
            thousand_sign = '.',
            discurrency = 'EUR',
            currency_sign = "EUR",
            country_url = '/world/',      
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            currency_sign = "EUR",
            country_url = '/world/',    
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = "HKD",
            country_url = '/hongkong/',     

        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = "GBP",
            country_url = '/uk/',   
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            currency_sign = "EUR",
            country_url = '/russia/', 
        ),
        CA = dict(
            currency = 'CAD',            
            discurrency = 'USD',
            currency_sign = "USD",
            country_url = '/canada/', 
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            currency_sign = "EUR",
            country_url = '/australia/',        
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = "EUR",
            country_url = '/europe/',              
        ),
        NO = dict(
            currency = 'NOK',
            thousand_sign = '.',
            discurrency = 'EUR',
            currency_sign = "EUR",
            country_url = '/norway/',  
        ),
#      
        )

        


