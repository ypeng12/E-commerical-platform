# -*- coding: utf-8 -*-
import re
import time
import requests
import json
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout1 = json.loads(checkout.xpath('.//script[@type="application/ld+json"]/text()').extract_first())
        item['tmp'] = checkout1
        if "InStock" in checkout1["offers"]["availability"]:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        obj = json.loads(data)
        page_num = obj['options']['totalPages']
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        if item['tmp']['sku'] in item['tmp']['image'][0]:
            item['sku'] = item['tmp']['sku']
        elif item['tmp']['sku'][0:-2] in item['tmp']['image'][0]:
            item['sku'] = item['tmp']['sku'][0:-2]

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'STELLA MCCARTNEY'
          
    def _images(self, images, item, **kwargs):
        img_li = item['tmp']['image']
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _color(self, res, item, **kwargs):
        color_json = res.xpath('//div[@role="main"]/script[contains(text(),"window.pdpProduct = ")]/text()').extract_first()
        color_data = json.loads(color_json.split("window.pdpProduct = ")[1].rsplit("}]")[0] + "}]")
        item['color'] = color_data[0]["productColor"]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['name'] = item['tmp']['name']
        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        block_sizes = sizes_data.xpath('./span[@class="unselectable"]/text()').extract()
        all_sizes = set(sizes_data.xpath('./span[@class="selectable"]/text()').extract())
        sizes_li = []
        for sizes in all_sizes:
            if sizes not in block_sizes:
                sizes_li.append(sizes)
        item['originsizes'] = sizes_li
        if item['category'] in ['a','b']:
            if not item['originsizes']:
                item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = item['tmp']['offers']['price']
        item['originlistprice'] = item['tmp']['offers']['price']

    def _parse_look(self, item, look_path, response, **kwargs):
        # self.logger.info('==== %s', response.url)
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
        item['cover'] = response.xpath('//img[@data-origin]/@data-origin').extract_first()

        item['products']= [(str(x)[:-2]) for x in outfits]
        yield item


    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas_1 = response.xpath(swatch_path['path'])
        sku = response.url.split('.html')[0].split('_cod')[-1]
        ajaxurl = 'https://www.stellamccartney.com/yTos/api/Plugins/ClickAndReservePluginApi/GetCombinationsWorldWide/?siteCode=SMC_US&code10='+sku
        res = getwebcontent(ajaxurl)
        obj = json.loads(res)
        datas = obj['ColorsRetail']
        swatches = []
        for data in datas:
            swatch = data['Code10']
            swatches.append(swatch)

        if len(swatches)>1:
            return swatches

    def _parse_images(self,response,**kwargs):
        images_json = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        img_li = images_json['image']
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() not in fits and ('cm' in info.lower() or 'model' in info.lower()):
                fits.append(info.strip())        
        size_info = '\n'.join(fits)

        return size_info

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h2//text()').extract_first().strip()
        html_origin = response.xpath('//div[@id="maincontent"]').extract_first().encode('utf-8')
        key = response.url.split('.html')[0].split('/')[-1]
        cover = response.xpath('//div[@class="hero-slide__media"]//picture/img/@data-src').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs_set = []

        images = {"type": "image","alt": ""}
        images['src'] = cover
        html_parsed['items'].append(images)
        imgs_set.append(cover)

        for div in response.xpath('//div[@id="maincontent"]/div/div'):
            text = div.xpath('.//p//text()').extract()
            text = '\n'.join(text)
            if text:
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text.strip()
                html_parsed['items'].append(texts)

            imgs = div.xpath('.//picture/img/@data-src').extract()
            for img in imgs:
                images = {"type": "image","alt": ""}
                image = 'https:' + img if 'http' not in img else img
                if image not in imgs_set:
                    images['src'] = image
                    html_parsed['items'].append(images)
                    imgs_set.append(image)

            urls = div.xpath('.//div[@class="product-tile__body--link"]/a/@href').extract()

            products = {"type": "products","pids":[]}
            for url in urls:
                link = 'https://www.stellamccartney.com%s' %url
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

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="totalResultsCount"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'stella'
    merchant = "STELLA McCARTNEY"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//ul[@class="products "]/@data-ytos-opt',_parser.page_num),
            items = '//li[@class="products-item   "]',
            designer = './/span[@class="designer"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('designer', ('//html',_parser.designer)),
            ('images', ('//html', _parser.images)),
            ('color',('//html',_parser.color)),
            ('description', ('//div[@class="content-body"]/ul/li/text()',_parser.description)),
            ('sizes', ('//div[@class="attribute__values d-flex flex-wrap"]/button[@data-attribute="size"]', _parser.sizes)),
            ('prices', ('//*[@id="itemInfo"]//div[@class="itemPrice"]', _parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='sku',
            key_type='sku',
            url_base='https://www.stellamccartney.com/item/index?cod10=%(sku)ssj&siteCode=STELLAMCCARTNEY_US',
            official_uid=63340,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[contains(@class,"relatedItem")]//a/img',
            img_base = 'https://www.stellamccartney.com/%(img_code)s/%(sku)s_10_c.jpg'
            ),
        image = dict(
            method = _parser.parse_images,
        ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="attributesUpdater fitting "]/span[@class="value"]/text()',
            ),
        blog = dict(
            official_uid = 63340,
            blog_list_url = _parser.blog_list_url,
            link = '//div[@class="region row articles-landing__container-list"]/div//a/@href',
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.stellamccartney.com/us/online/stella-mccartney-men/men/men-wallets?page=',
            ],
            b = [
                'https://www.stellamccartney.com/us/online/stella-mccartney-men/men/men-s-bags?page='
            ],
            c = [
                'https://www.stellamccartney.com/us/online/stella-mccartney-men/men/men-s-ready-to-wear?page='
            ],
            s = [
                'https://www.stellamccartney.com/us/online/stella-mccartney-men/men/men-s-shoes?page='
            ],
        ),
        f = dict(
            a = [
                'https://www.stellamccartney.com/us/online/stella-mccartney/women/accessories?page='
            ],
            b = [
                'https://www.stellamccartney.com/us/online/stella-mccartney/women/handbags?page='
            ],
            c = [
                'https://www.stellamccartney.com/us/online/stella-mccartney/women/ready-to-wear?page='
            ],
            s = [
                'https://www.stellamccartney.com/us/online/stella-mccartney/women/shoes?page='
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    blog_url = dict(
        EN = [
        'https://www.stellamccartney.com/us/en/stellas-world/stellas-world.html'
        # 'https://store.stellamccartney.cn/experience/cn/',
        ]
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '.com/us/',
        ),
        CN = dict(
            area = 'CN',
            language = 'ZH',
            currency = 'CNY',
            country_url = '.cn/cn/',
            translate = [
                ('www.','store.'),
                ('women/shoes','%E5%A5%B3%E5%A3%AB/%E9%9E%8B%E5%AD%90'),
                ('women/handbags','%E5%A5%B3%E5%A3%AB/%E6%89%8B%E8%A2%8B'),
                ('women/ready-to-wear','%E5%A5%B3%E5%A3%AB/%E6%88%90%E8%A1%A3'),
                ('women/accessories','%E5%A5%B3%E5%A3%AB/%E9%85%8D%E9%A5%B0'),
                ('men/men-s-ready-to-wear','%E7%94%B7%E5%A3%AB/%E7%94%B7%E5%A3%AB%E6%88%90%E8%A1%A3'),
                ('men/men-s-shoes','%E7%94%B7%E5%A3%AB/%E7%94%B7%E5%A3%AB%E9%9E%8B%E5%B1%A5'),
                ('men/men-s-bags','%E7%94%B7%E5%A3%AB/%E7%94%B7%E5%A3%AB%E5%8C%85%E8%A2%8B'),
                ('men/men-wallets','%E7%94%B7%E5%A3%AB/men-wallets'),
            ],
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '.com/gb/',
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '.com/jp/',
        ),
        KR = dict( 
            currency = 'KRW',
            country_url = '.com/kr/',
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '.com/hk/',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            country_url = '.com/sg/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '.com/ca/',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '.com/au/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '.com/de/',
            thousand_sign = '.',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = '.com/no/',
            thousand_sign = '.',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            country_url = '.com/ru/',
            thousand_sign = ' ',
        )

        )
        


