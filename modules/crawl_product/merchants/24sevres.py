# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser
from utils.cfg import *
from utils import utils
from lxml import etree
import requests
import time

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = 100
        return pages

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            item['error'] = 'ignore' # just checkout
            return False
        else:
            return True

    def _sku(self, scripts, item, **kwargs):
        data = json.loads(scripts.extract_first())

        sku = data['props']['initialState']['pdp']['productFormated']['shortSKU']
        item['sku'] = sku if len(sku) == 11 else ''
        item['name'] = data['props']['initialState']['pdp']['productFormated']['name']
        item['designer'] = data['props']['initialState']['pdp']['productFormated']['brand']['name']
        item['description'] = data['props']['initialState']['pdp']['productFormated']['description']
        color = data['props']['initialState']['pdp']['productFormated']['productInformation']['brandColor']
        item['color'] = color.upper() if color and color != 'no  color' else ''
        item['tmp'] = data

    def _images(self, res, item, **kwargs):
        img = res.xpath('.//source[contains(@srcset,"555x625")]/@srcset').extract_first()
        # img_link = img.rsplit('/',1)[0]

        # pictures = item['tmp']['props']['initialState']['pdp']['productFormated']['pictures']
        # images = []
        # for picture in pictures:
        #   image = img_link + '/' + picture['path']
        #   if image not in images:
        #       images.append(image)

        # item['images'] = images
        # item['cover'] = img
        item['images'] = [img]
        item['cover'] = img

    def _sizes(self, sizes, item, **kwargs):
        data = item['tmp']
        orisizes = []
        orisizes2 = []
        osizes = data['props']['initialState']['pdp']['productFormated']['sizeAvailable']
        for osize in osizes:
            if osize['hasOffer']:
                size = osize['sizeLabel'] if osize['sizeLabel'] else 'IT'
                orisizes.append(size)
        # for sizecode, osize in list(osizes.items()):
        #     if osize[0]['stock']:
        #         size = osize[0]['label'] if len(osize) == 1 else osize[0]['label'] + ' / ' + osize[1]['label']
        #         size2 = osize[0]['label'] if osize[0]['reference'] in ['IT','EU','US','UK'] else osize[-1]['label']
        #         orisizes.append(size)
        #         orisizes2.append(size2)
        if not orisizes and item['category'] in ['a','b','e']:
            orisizes = ['IT']
        item['originsizes'] = orisizes
        item['originsizes2'] = orisizes2 if orisizes2 else orisizes

    def _prices(self, prices, item, **kwargs):
        data = item['tmp']
        item['originlistprice'] = str(float(data['props']['initialState']['pdp']['productFormated']['shippingExpress'][0]['priceInclVat2']) / 100)
        try:
            item['originsaleprice'] = str(float(data['props']['initialState']['pdp']['productFormated']['shippingExpress'][0]['discountPriceInclVat']) / 100)
        except:
            item['originsaleprice'] = item['originlistprice']

    def _parse_size_info(self, response, size_info, **kwargs):
        size_infos = response.xpath(size_info['size_info_path'])
        fit = []
        for i in size_infos:
            key = i.xpath('./strong/text()').extract_first()
            value = i.xpath('.//span/text()').extract_first()
            if key and value and key not in ['Product code','Made in','Details','Color','Care instructions','Ingredients']:
                dimensions = key + ': ' +value
                fit.append(dimensions)
        size_info = '\n'.join(fit)

        return size_info

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = json.loads(response.xpath(swatch_path['swatch_path']).extract_first())
        swatches = []
        for child in datas['_children']:
            if len(child['sku']) == 13:
                sku = child['sku'][:-3]
            elif len(child['sku']) == 15:
                sku = child['sku']
            swatches.append(sku)
        return swatches

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//source[contains(@srcset,"555x625")]/@srcset').extract_first()
        images = [imgs]

        return images

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h1[@id="title-article"]/text()').extract_first()
        key = response.url.split('/en-us/')[-1]

        # judge_language
        link = 'https://fanyi.baidu.com/langdetect'
        data = {'query': title}
        res = requests.post(link, data=data)
        infos_dict = json.loads(res.text)

        if infos_dict['lan'] != 'en' and '24 Sèvres' not in title:
            return

        try:
            date = response.xpath('//div[@class="col-xs-6 event-dates"]/text()').extract_first().split('|')[-1].replace(',','').strip()
            dates = ['Y','M','D']
            if len(date.split(' ')) == 2:
                date = date + ' 2019'
            for t in date.split(' '):
                if len(t) == 4 and t.isdigit():
                    dates[0] = t
                elif months_num.get(t.title()):
                    dates[1] = months_num.get(t.title())
                else:
                    dates[2] = t.lower().replace('th','')
            timeStruct = time.strptime('-'.join(dates), "%Y-%m-%d")
            publish_datetime = time.strftime("%Y-%m-%d", timeStruct)
        except:
            publish_datetime = None

        html_origin = response.xpath('//div[@class="main-content store"]').extract_first().encode('utf-8')
        html = etree.HTML(html_origin)
        cover = html.xpath('//img/@src')[0]
        
        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs_set = []

        for node in response.xpath('//div[@class="wrapper-padding"]/div/*'):                            

            header = node.xpath('./h2/text() | .//p[@class="citation"]/text()').extract_first()
            if header:
                headers = {"type": "header"}
                headers['value'] = header
                html_parsed['items'].append(headers)

            imgs = node.xpath('./source/img/@src').extract()
            for img in imgs:
                if img and img not in imgs_set:
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images)
                    imgs_set.append(img)

            texts = node.xpath('./text()').extract() #  | ./div/text()  publish time
            for text in texts:          
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text.replace('\n','')
                html_parsed['items'].append(texts)

            for nod in node.xpath('./div[@class="row"]/*'):
                img = nod.xpath('.//img/@src').extract_first()
                if img and img not in imgs_set:
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images)
                    imgs_set.append(img)

                texts = nod.xpath('.//p').extract()
                for text in texts:
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text.replace('\n','')
                    html_parsed['items'].append(texts)

            for nod in node.xpath('./div'):
                img = nod.xpath('./picture/source/img/@src').extract_first()
                if img and img not in imgs_set:
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images)
                    imgs_set.append(img)

                texts = nod.xpath('./p').extract()
                for text in texts:
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text.replace('\n','')
                    html_parsed['items'].append(texts)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

_parser = Parser()


class Config(MerchantConfig):
    name = "24sevres"
    merchant = "24S"
    url_split = False


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@id="resultsCount"]/text()', _parser.page_num),
            items = '//div[@class="row"]/article',
            designer = './/h5[@class="brand-name function-bold"]/text()',
            link = './/a[@class="item"]/@href',
            ),
        product = OrderedDict([
            ('checkout',('//button[@class="btn btn-s btn-second item-add"]', _parser.checkout)),
            ('sku', ('//script[@id="__NEXT_DATA__"]/text()', _parser.sku)),
            ('images',('//html',_parser.images)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//html',_parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            swatch_path='//div[@id="product-tools"]/@data-variants-tree',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//ul[@class="element-list"]/li',
            ),
        blog = dict(
            official_uid=61858,
            blog_page_num = '//script[contains(text(),"totalPages")]/text()',
            link = '//div[@class="row upcoming-events-block other-articles"]/article//a/@href',         
            method = _parser.parse_blog,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                # "https://www.24s.com/en-us/women/accessories?page=",
                "https://www.24s.com/en-us/women/ultimates/accessories?page=",
                ],
            b = [
                # "https://www.24s.com/en-us/women/bags?page="
                "https://www.24s.com/en-us/women/ultimates/bags?page=",
                ],
            c = [
                # "https://www.24s.com/en-us/women/ready-to-wear?page=",
                "https://www.24s.com/en-us/women/ultimates/ready-to-wear?page=",
            ],
            s = [
                # "https://www.24s.com/en-us/women/shoes?page=",
                "https://www.24s.com/en-us/women/ultimates/shoes?page=",
            ],
            e = [
                "https://www.24s.com/en-us/women/beauty?page=",
            ]
        ),
        m = dict(
            a = [
                "https://www.24s.com/en-us/men/accessories/small-leather-goods?page=",
                "https://www.24s.com/en-us/men/accessories/belts-and-braces?page=",
                "https://www.24s.com/en-us/men/accessories/scarves?page=",
                "https://www.24s.com/en-us/men/accessories/gloves?page=",
                "https://www.24s.com/en-us/men/accessories/hats?page=",
                "https://www.24s.com/en-us/men/accessories/ties-and-bowties?page=",
                "https://www.24s.com/en-us/men/accessories/jewelry?page=",
                "https://www.24s.com/en-us/men/accessories/sunglasses?page=",
            ],
            b = [
                "https://www.24s.com/en-us/men/accessories/luggage?page=",
                "https://www.24s.com/en-us/men/accessories/bags?page=",
            ],
            c = [
                "https://www.24s.com/en-us/men/ready-to-wear?page=",
                "https://www.24s.com/en-us/men/accessories/socks?page=",
            ],
            s = [
                "https://www.24s.com/en-us/men/shoes?page=",
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    blog_url = dict(
        EN = ['https://www.24s.com/en-us/le-bon-marche/news-and-events/category/fashion?p=']
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '/en-us/',
            ),
        CN = dict(
            area = 'CN',
            currency = 'CNY',
            country_url = '/en-cn/',
        ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            country_url = '/en-ca/',
        ),
        AU = dict(
            area = 'AU',
            currency = 'AUD',
            country_url = '/en-au/',
        ),
        HK = dict(
            area = 'AU',
            currency = 'HKD',
            country_url = '/en-hk/',
        ),
        JP = dict(
            area = 'AU',
            currency = 'JPY',
            country_url = '/en-jp/',
        ),
        KR = dict(
            area = 'AU',
            currency = 'KRW',
            country_url = '/en-kr/',
        ),
        SG = dict(
            area = 'AU',
            currency = 'SGD',
            country_url = '/en-sg/',
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/en-gb/',
        ),
        DE = dict(
            language = 'DE',
            area = 'GB',
            currency = 'EUR',
            country_url = '/de-de/',
        ),
        NO = dict(
            area = 'GB',
            currency = 'NOK',
            country_url = '/en-no/',
        )
        )
