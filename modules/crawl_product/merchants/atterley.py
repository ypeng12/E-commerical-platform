# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        page_num = 20
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('/?')[0] + '?page={}'.format(str(i))
        return url

    def _checkout(self, checkout, item, **kwargs):
        available = checkout.extract_first()
        if available and available == 'InStock':
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        item['tmp'] = data.extract_first()
        item['sku'] = item['tmp'].split('parentSku:"')[1].split('"',1)[0].strip().upper()

        if 'sku' in kwargs:
            item['sku'] = kwargs['sku']

    def _designer(self, res, item, **kwargs):
        item['designer'] = res.extract_first()
        if not item['designer']:
            item['error'] = "parse designer issue"

    def _images(self, scripts, item, **kwargs):
        prd_script = ''
        images = []
        prd_script = item['tmp']
        if prd_script:
            img_li = prd_script.split("media_gallery:")[1].split(',special_price_original')[0].split(',vendor_statu')[0].replace('_image','_img')
            for img in eval(img_li.replace('null', '""').replace('vid','"vid"').replace('pos','"pos"').replace('typ','"typ"').replace('lab','"lab"').replace('image','"image"')):
                img = 'https://d3312htug2rvv.cloudfront.net/img/600/744/resize/' + img['image'].replace('_img','_image') if 'http' not in img['image'] else img['image']
                images.append(img)
        
        if images:
            item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
            if 'Colour' in desc:
                item['color'] = desc.split(':')[-1].strip().upper()
                break
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        prd_script = item['tmp']
        size_li = []
        skus_li = []
        native_size_pid = {}

        if 'configurable_options' in prd_script and 'configurable_children' in prd_script:
            size_skus = prd_script.split('configurable_options:[')[1].split('configurable_children:[')[1].split('],max_regular_price')[0]
            for size_sku in size_skus.split(',{'):
                if 'sku' not in size_sku:
                    continue
                skus_li.append(size_sku.split('sku:"')[1].split('"')[0].replace('#','%23').replace('+','%2B'))
                try:
                    native_size_pid[size_sku.split('id:"')[1].split('"')[0]] = size_sku.split('native_size:')[1].split(',')[0]
                except:
                    pass
            skus = ','.join(skus_li)
            base_url = "https://kti7uu5d0h.execute-api.eu-west-1.amazonaws.com/atterley/stock/list?skus={skus}".format(skus=skus)

            res = requests.get(base_url)
            size_stocks = json.loads(res.text)

            stcok_ids = []
            for stock in size_stocks['result']:
                if stock['is_in_stock']:
                    stcok_ids.append(native_size_pid[stock['item_id']])

            for stcok_id in stcok_ids:
                xpath_rule = './/button[@id="%s"]/span/text()' %str(stcok_id)
                size = sizes_data.xpath(xpath_rule).extract_first()
                if size:
                    size_li.append(size)

            if item['category'] in ['a','b'] and size_li==[]:
                size_li = ['IT']
            elif item['category'] in ['c','s']:
                sizes = []
                for size in size_li:
                    if size.replace('.','').isdigit() and float(size) < 20:
                        size = 'UK'+size
                    sizes.append(size)
                size_li = sizes
        else:
            size_li = ['One Size']

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//*[@class="old-price"]/span/text()').extract()[0]
            saleprice = prices.xpath('.//*[@class="special-price"]/span/text()').extract()[0]
        except:
            listprice = prices.xpath('.//*[@class="price"]//text() | .//*[@class="price-same"]/text() | .//*[@class="old-price"]/span/text()').extract()[0]
            saleprice = listprice
        rate = 1
        country_currency = {
            'US':'USD',
            'CA':'CAD',
            'AU':'AUD',
            'HK':'HKD',
            'DE':'EUR',
        }

        if item['country'] in list(country_currency.keys()):
            res = requests.get('https://www.atterley.com/currency_rate')
            currency_rates = json.loads(res.text)
            rate = currency_rates['currencyRates'][country_currency[item['country']]]['value']

        if listprice:
            item['originsaleprice'] = str(round(float(saleprice.replace('£','').replace(',','')) * float(rate), 2))
            item['originlistprice'] = str(round(float(listprice.replace('£','').replace(',','')) * float(rate), 2))
        else:
            item['originsaleprice'] = str(round(float(saleprice.replace('£','').replace(',','')) * float(rate), 2))
            item['originlistprice'] = str(round(float(saleprice.replace('£','').replace(',','')) * float(rate), 2))

    def _parse_images(self, response, **kwargs):
        prd_script = ''
        images = []
        for script in response.xpath('//script/text()').extract():
            if '__INITIAL_STATE__' in script:
                prd_script = script
                break
        if prd_script:
            img_li = prd_script.split("media_gallery:")[1].split(',special_price_original')[0].split(',vendor_statu')[0].replace('_image','_img')
            for img in eval(img_li.replace('null', '""').replace('vid','"vid"').replace('image','"image"').replace('pos','"pos"').replace('typ','"typ"').replace('lab','"lab"')):
                img = 'https://d3312htug2rvv.cloudfront.net/img/600/744/resize/' + img['image'].replace('_img','_image') if 'http' not in img['image'] else img['image']
                images.append(img)

        imgs = [images[-1]] + images[:-1]
        return imgs

    def _blog_page_num(self, data, **kwargs):
        page_num = data.split('page/')[-1].split('/')[0]
        return int(page_num)

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url.replace('1000', str(i))
        return url

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//div[@class="holiday-inner"]/h1/text()').extract_first()
        key = response.url.split('editorial/')[-1].split('/')[0]
        html_origin = response.xpath('//div[@class="col-main"]/div[@class="container"]').extract_first()
        cover = response.xpath('//div[@class="holiday-shop"]/img/@src').extract_first()

        img_li = []
        html_parsed = {
            "type": "article",
            "items": []
        }

        for node in response.xpath('//div[@class="col-main"]/div[@class="container"]/div'):
            node_type = node.xpath('./@class').extract_first()

            if node_type in ['row', 'classic-combination']:
                imgs = node.xpath('.//img/@src').extract()
                images = {"type": "image","alt": ""}
                for img in imgs:
                    if img not in img_li:
                        img_li.append(img)
                        images['src'] = img
                        html_parsed['items'].append(images)
                header = node.xpath('.//div[@class="cnt-block"]/h2/text()').extract_first()
                if header:
                    headers = {"type": "header"}
                    headers['value'] = header
                    html_parsed['items'].append(headers)

                text_li = node.xpath('.//div[@class="cnt-block"]/p | .//div[@class="cnt-block"]/a | .//div[@class="cnt-block"]/div').extract()
                for text in text_li:
                    texts = {"type": "html"}
                    texts['value'] = text.replace("style=", "origin_style=")
                    html_parsed['items'].append(texts)

            elif node_type in ['row product-outer']:                
                products = {"type": "products","pids":[]}
                links = node.xpath('.//figure/a/@href').extract()
                for link in links:
                    prod = parseProdLink(link)
                    for product in prod[0]:
                        pid = product.id
                        if pid not in products['pids']:
                            products['pids'].append(pid)
                if products not in html_parsed['items'] and products['pids']:
                    html_parsed['items'].append(products)

        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed


_parser = Parser()


class Config(MerchantConfig):
    name = 'atterley'
    merchant = "Atterley"
    merchant_headers = {'User-Agent':'ModeSensBotAtterley20210402'}

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[contains(@class,"product-listing")]',
            designer = './/h3[@class="list-product-brand"]/text()',
            link = './/figure/a/@href',
            ),
        product = OrderedDict([
            # sku: //meta[@itemprop="mpn"]/@content
            ('checkout', ('//meta[@itemprop="availability"]/@content', _parser.checkout)),
            ('sku', ('//script[contains(text(),"__INITIAL_STATE__")]/text()', _parser.sku)),
            ('name', '//meta[@name="twitter:title"]/@content'),
            ('designer', ('//div[@itemprop="brand"]/meta/@content', _parser.designer)),
            ('images', ('//html', _parser.images)),
            ('description', ('//meta[@name="twitter:description"]/@content',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="price serif"]', _parser.prices))
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
            official_uid=271036,
            blog_page_num = ('//a[@title="Previous"]/@href', _parser.blog_page_num),
            blog_list_url = _parser.blog_list_url,
            link = '//ul[@class="row post-list"]/li/div/div/a/@href',         
            method = _parser.parse_blog,
            )
        )

    blog_url = dict(
        EN = ['https://www.atterley.com/women/editorial/page/1000/']
    )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.atterley.com/men/accessories/belts/?page=",
                "https://www.atterley.com/men/accessories/gloves/?page=",
                "https://www.atterley.com/men/accessories/hats/?page=",
                "https://www.atterley.com/men/accessories/jewellery-watches/?page=",
                'https://www.atterley.com/men/accessories/scarves/?page=',
                'https://www.atterley.com/men/accessories/sunglasses/?page=',
            ],
            b = [
                'https://www.atterley.com/men/accessories/bags/?page=',
            ],
            c = [
                "https://www.atterley.com/men/clothing/?page=",
                "https://www.atterley.com/men/sale/sale-clothing/?page=",
            ],
            s = [
                'https://www.atterley.com/men/shoes/?page='
            ],
        ),
        f = dict(
            a = [
                'https://www.atterley.com/women/accessories/belts-1/?page=',
                "https://www.atterley.com/women/accessories/gloves-1/?page=",
                "https://www.atterley.com/women/accessories/hats-1/?page=",
                "https://www.atterley.com/women/accessories/jewellery-watches/?page=",
                "https://www.atterley.com/women/accessories/scarves-1/?page=",
                "https://www.atterley.com/women/accessories/sunglasses-1/?page=",
            ],
            b = [
                'https://www.atterley.com/women/accessories/bags-1/?page='
            ],
            c = [
                'https://www.atterley.com/women/clothes/?page=',
            ],
            s = [
                "https://www.atterley.com/women/shoes/?page=",
            ],

        params = dict(
            page = 1,
            )
        )
    )


    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {
                'currency':'USD',
            }
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        HK = dict(
            currency = 'HKD',
            cookies = {
                'currency':'HKD',
            }
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        GB = dict(
            currency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        CA = dict(
            currency = 'CAD',
            cookies = {
                'currency':'CAD',
            }
        ),
        AU = dict(
            currency = 'AUD',
            cookies = {
                'currency':'AUD',
            }
        ),
        DE = dict(
            currency = 'EUR',
            cookies = {
                'currency':'EUR',
            }
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            cookies = {
                'currency':'GBP',
            }
        )
        )
        


