from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.ladystyle import blog_parser,parseProdLink
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

    def _sku(self, sku_data, item, **kwargs):
        data = json.loads(sku_data.extract_first().split('[')[0])
        item['sku'] = data['ecomm_prodid']
        item['designer'] = 'SOMETHING NAVY'

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
        
    def _description(self, desc, item, **kwargs):
        
        details = desc.extract()
        desc_li = ['Details & Care']
        for desc in details:
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
        price = prices.extract_first()
        item['originlistprice'] = price
        item['originsaleprice'] = price

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)

        return images

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h1/text()').extract_first()
        link = response.url.split('?')[0]
        key = link.split('/')[-1] if link[-1] != '/' else link.split('/')[-2]
        html_origin = response.xpath('//div[@class="article-main"]').extract_first().encode('utf-8')
        img = response.xpath('//meta[@property="og:image"]/@content').extract_first()
        cover = 'https:' + img if 'http' not in img else img

        html_parsed = {
            "type": "article",
            "items": []
        }

        images = {"type": "image","alt": ""}
        images['src'] = cover
        html_parsed['items'].append(images)

        imgs_set = []

        for node in response.xpath('//div[@class="article-main"]//div[@class="article-intro"]'):
            header = node.xpath('.//div[@class="block-blurb type-e"]/span/p/text()').extract_first()
            if header:
                headers = {"type": "header"}
                headers['value'] = header
                html_parsed['items'].append(headers)

            texts = node.xpath('.//div[@class="block-text type-f"]/span/p').extract()
            for text in texts:          
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text.replace('\n','')
                html_parsed['items'].append(texts)

        for node in response.xpath('//div[@class="article-main"]/div[@class="article-modules"]/div'):
            header = node.xpath('.//h4/text()').extract_first()
            if header:
                headers = {"type": "header"}
                headers['value'] = header
                html_parsed['items'].append(headers)

            imgs = node.xpath('.//div/@data-src').extract()
            for img in imgs:
                image = img if 'http' in img else 'https:' + img
                if image in imgs_set:
                    continue
                images = {"type": "image","alt": ""}
                images['src'] = image
                html_parsed['items'].append(images)
                imgs_set.append(img)

            texts = node.xpath('.//div[@class="block-text type-f"]').extract()
            for text in texts:
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text.replace('\n','')
                html_parsed['items'].append(texts)

            links = node.xpath('.//div[@class="block-interior"]/a/@href').extract()
            products = {"type": "products","pids":[]}
            for link in [urljoin(response.url, x) for x in links]:
                prod = parseProdLink(link)
                if prod[0]:
                    for product in prod[0]:
                        pid = product.id
                        products['pids'].append(pid)
            if products['pids']:
                html_parsed['items'].append(products)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json


_parser = Parser()


class Config(MerchantConfig):
    name = 'somethingnavy'
    merchant = 'Something Navy'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="search-results-nav__info"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/html',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[text()="Add to Bag"]', _parser.checkout)),
            ('sku',('//div[contains(text(),"ecomm_prodid")]/text()',_parser.sku)),
            ('name', '//h1/text()'),
            ('color', '//div[@class="color-value no-mobile"]/span/text()'),
            ('description', ('//div/h3[contains(text(),"Details & Care")]/../div/div/ul/li/text()',_parser.description)),
            ('images',('//meta[@property="og:image"]/@content',_parser.images)),
            ('prices', ('//div[@class="desktop-only"]/klarna-placement/@data-purchase-amount', _parser.prices)),
            ('sizes',('//div[@class="swatches options-size"]/div/span/text()',_parser.sizes)),
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
            official_uid = 2892,
            link = '//div[@class="block article-grid-item grid-item"]//a[@class="block-link"]/@href',
            blog_list_url = _parser.blog_list_url,
            method = _parser.parse_blog,
            )
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
            ]
        )
    )

    blog_url = dict(
        EN = [
            'https://www.somethingnavy.com/something-else/'
        ]
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            )
        )

        


