from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from lxml import etree
import requests
import json
from copy import deepcopy
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = int(data)
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?page=%s'%(i)
        return url

    def _sku(self, sku_data, item, **kwargs):
        data = json.loads(sku_data.extract_first().split('__st=')[-1].rsplit(';',1)[0])
        item['sku'] = data['rid']

    def _images(self, images, item, **kwargs):
        imgs_data = images.extract_first()
        images = re.search(r'images: (\[".*?"\]{1})',imgs_data).group(1)
        imgs = json.loads(images)
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[contains(@id,"ComparePrice")]/span//text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[contains(@id,"ProductPrice")]/span//text()').extract()[0]
        except:
            item['originsaleprice'] =prices.xpath('.//span[contains(@id,"ProductPrice")]/span//text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[contains(@id,"ProductPrice")]/span//text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs_data = response.xpath('//script[contains(text(),"window.KiwiSizing")]/text()').extract_first()
        images = re.search(r'images: (\[".*?"\]{1})',imgs_data).group(1)
        imgs = json.loads(images)
        images_li = []
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images_li.append(img)

        return images_li

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//div[contains(@class,"page-content")]//h1[@class="section-header__title"]/text()').extract_first().strip()
        html_origin = response.xpath('//div[contains(@class,"page-content")]').extract_first().encode('utf-8')
        key = response.url.split('?')[0].split('/')[-1]
        cover = response.xpath('//div[@itemprop="articleBody"]//img/@src').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs_set = []

        images = {"type": "image","alt": ""}
        images['src'] = cover
        html_parsed['items'].append(images)
        imgs_set.append(cover)

        for div in response.xpath('//div[contains(@class,"page-content")]//div[@itemprop="articleBody"]'):
            text = div.xpath('./div/p/span/text()').extract()
            text = '\n'.join(text)
            if text:
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text.strip()
                html_parsed['items'].append(texts)

            imgs = div.xpath('.//img/@src').extract()
            for img in imgs:
                images = {"type": "image","alt": ""}
                if img not in imgs_set:
                    images['src'] = img
                    html_parsed['items'].append(images)
                    imgs_set.append(img)

            # urls = div.xpath('.//div[@class="product-tile__body--link"]/a/@href').extract()

            products = {"type": "products","pids":[]}
            # for url in urls:
            #     prod = parseProdLink(url)
            #     if prod[0]:
            #         for product in prod[0]:
            #             pid = product.id
            #             products['pids'].append(pid)
            if products['pids']:
                html_parsed['items'].append(products)


        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="page"][last()]/a/text()').extract_first().strip())*32
        return number
        
    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()



class Config(MerchantConfig):
    name = 'baltini'
    merchant = 'Baltini'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="page"][last()]/a/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="grid-product__content"]',
            designer = './/div[@class="grid-product__meta"]/div[contains(@class,"vendor")]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@id,"AddToCart")]', _parser.checkout)),
            ('sku',('//script[contains(text(),"__st=")]/text()',_parser.sku)),
            ('name','//h1[contains(@class,"product-single__title-alternate")]/text()'),
            ('designer','//div[@class="h1"]/text()'),
            ('images',('//script[contains(text(),"window.KiwiSizing")]/text()',_parser.images)),
            ('color','//span[@class="color-name"]/text()'), 
            ('description', ('//div[@class="product-single__description rte"]/p//text()',_parser.description)),
            ('sizes',('//fieldset//input/@value',_parser.sizes)),
            ('prices', ('//div[@class="product-single__meta"]', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        blog = dict(
            official_uid = 11,
            blog_list_url = _parser.blog_list_url,
            link = '//div[@class="article__grid-meta"]/a/@href',
            method = _parser.parse_blog,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-single__description rte"]/p//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.baltini.com/collections/accessories-1?page="
            ],
            b = [
                "https://www.baltini.com/collections/bags-2?page="
            ],
            c = [
                "https://www.baltini.com/collections/clothing?page=",
            ],
            s = [
                "https://www.baltini.com/collections/shoes-1?page="
            ],
        ),
        f = dict(
            a = [
                "https://www.baltini.com/collections/accessories?page=",
                ],
            b = [
                "https://www.baltini.com/collections/bags?page="
            ],

            c = [
                "https://www.baltini.com/collections/womens-clothing?page=",
            ],
            s = [
                "https://www.baltini.com/collections/shoes?page="
            ],

        params = dict(
            ),
        ),

    )

    blog_url = dict(
        EN = [
            'https://www.baltini.com/blogs/magazine'
        ],
        ZH = [
            'https://zh.baltini.com/zh/blogs/magazine'
        ]
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
        )

        


