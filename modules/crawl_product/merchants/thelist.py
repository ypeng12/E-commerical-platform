from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
from utils.ladystyle import blog_parser

class Parser(MerchantParser):    

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, scripts, item, **kwargs):
        prd_script = ''
        for script in scripts.extract():
            if 'var dlObjects' in script:
                prd_script = script
                break
        prd_dict = json.loads(prd_script.split(' var dlObjects = [')[-1].split('];')[0])
        item['sku'] = prd_dict['ecommerce']['detail']['products'][0]['id'].upper()
        item['name'] = prd_dict['ecommerce']['detail']['products'][0]['name']
        item['designer'] = prd_dict['ecommerce']['detail']['products'][0]['brand'].upper()        

    def _images(self, scripts, item, **kwargs):
        prd_script = ''
        for script in scripts.extract():
            if 'jsonConfig' in script:
                prd_script = script
                break

        img_li = []
        if prd_script:
            prd_dict = json.loads(prd_script.split('"jsonConfig":')[-1].split('"jsonSwatchConfig"')[0].strip()[:-1])        
            for key,value in list(prd_dict['images'].items()):
                for img in value[:-1]:
                    if img['img'] not in img_li:
                        img_li.append(img['img'])
                break
            
            item['tmp'] = prd_dict
        else:
            img_script = ''
            for script in scripts.extract():
                if 'isMain":true' in script:
                    img_script = script
                    break
            imgs = json.loads('[' + img_script.split('"data": [')[-1].split('],')[0].strip() + ']')            
            for img in imgs[:-1]:
                if img['img'] not in img_li:
                    img_li.append(img['img'])
            item['tmp'] = ''

        item['cover'] = img_li[0] if img_li else ''
        item['images'] = img_li
        
    def _description(self, description, item, **kwargs):    
        desc_li = []
        for desc in description.extract():
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        ptype = sizes.xpath('.//div[@class="one-line Type"]/p/text()').extract_first()

        if ptype and ptype == 'Vintage':
            condition = sizes.xpath('.//div[contains(@class,"Rating")]/p/text()').extract_first()
            if condition and condition == 'Used':
                item['condition'] = 'u'
            else:
                item['condition'] = 'p'

        prd_dict = item['tmp']
        if prd_dict:
            size_li = []
            size_options =  list(prd_dict['attributes'].values())[0]['options']
            for option in size_options:
                if option['products']:
                    size_li.append(option['label'])
                
            item['originsizes'] = size_li
        else:
            if item['category'] in ['a','b']:
                item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        prd_dict = item['tmp']
        if prd_dict:
            item['originsaleprice'] = list(prd_dict['optionPrices'].values())[0]['finalPrice']['amount']
            item['originlistprice'] = list(prd_dict['optionPrices'].values())[0]['oldPrice']['amount']
        else:
            item['originsaleprice'] = prices.xpath('//span[@data-price-type="finalPrice"]/@data-price-amount').extract_first()
            item['originlistprice'] = prices.xpath('//span[@data-price-type="oldPrice"]/@data-price-amount').extract_first()

    def _blog_page_num(self, data, **kwargs):
        return 6

    def _json_blog_links(self, response, **kwargs):
        url = response.url.split('&p=')[0]
        page = response.url.split('&p=')[-1]
        data = {
            'action':'jnews_module_ajax_jnews_block_23',
            'data[attribute][number_post]':'4',
            'data[attribute][pagination_number_post]':'4',
            'data[current_page]':'%s'%page,
            'data[attribute][include_category]':'38,25,39',
        }
        res = requests.post(url, data)
        content = json.loads(res.text)['content']
        blog_html = etree.HTML(content)
        urls = blog_html.xpath('//article/div/a/@href')
        
        return urls

    def _parse_blog(self, response, **kwargs):
        html_origin = response.xpath('//div[@class="container"]').extract_first().encode('utf-8')
        title = response.xpath('//h1[@class="jeg_post_title"]/text()').extract_first()
        key = response.url.split('?')[0].split('/')[-2] if response.url.split('?')[0].endswith('/') else response.url.split('?')[0].split('/')[-1]
        cover = response.xpath('//div[@class="jeg_featured featured_image"]/a/@href').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        images = {"type": "image","alt": ""}
        images['src'] = cover
        html_parsed['items'].append(images)
        imgs_set = []

        for node in response.xpath('//div[contains(@class,"content-inner")]/*'):
            node_html = node.xpath('.').extract_first()
            if node_html.startswith('<h1') or node_html.startswith('<h2'):
                header = node.xpath('./text()').extract_first()
                headers = {"type": "header"}
                headers['value'] = header
                html_parsed['items'].append(headers)
            if node_html.startswith('<p') or node_html.startswith('<h4'):
                texts = node.xpath('./text() | ./strong/text()').extract()
                if texts:
                    text = ''.join(texts)
                    if text.strip():
                        texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                        texts['value'] = text.strip()
                        html_parsed['items'].append(texts)
                img = node.xpath('./img/@src').extract_first()
                if img and img not in imgs_set:
                    imgs_set.append(img)
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json


_parser = Parser()


class Config(MerchantConfig):
    name = "thelist"
    merchant = "THE LIST"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            items = '//div[@class="product-image"]',
            designer = '//div[@class="b-product_tile_containersdafsafs"]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="buy-now"]', _parser.checkout)),
            ('sku', ('//script/text()',_parser.sku)),
            # ('name', ('//html',_parser.sku) ),
            # ('designer', ('//div[@class="l-footer-copyrqight"]/span/text()',_parser.designer)),
            ('images', ('//script/text()', _parser.images)),
            ('color','//div[@class="one-line Color"]/p/text()'),
            ('description', ('//p[@class="product-description"]/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(
            ),
        blog = dict(
            official_uid=237043,
            blog_page_num = ('//html',_parser.blog_page_num),
            json_blog_links = _parser.json_blog_links,
            method = _parser.parse_blog,
            ),
        )
    list_urls = dict(
        f = dict(
            a = [            
            ],
        ),

        m = dict(
            c = [                
            ],
            s = [
                
            ],

        params = dict(
            # TODO:
            ),
        ),
    )

    blog_url = dict(
        EN = ['http://stories.gothelist.com/?ajax-request=jnews&p=']
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '.com/gen/',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict( 
            currency = 'KRW',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            discurrency = 'EUR',
            country_url = '.com/eu/',
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
            area = 'EU',
            currency = 'EUR',
            country_url = '.com/eu/',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = '.com/eu/',
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'EUR',
            country_url = '.com/eu/',
        )

        )

        


