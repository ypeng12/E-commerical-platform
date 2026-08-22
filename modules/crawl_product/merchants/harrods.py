from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser,parseProdLink
from utils.cfg import *
import time
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        add_to_bag = checkout.xpath('.//*[text()="Add to bag"]')
        out_of_stock = checkout.xpath('.//*[@data-test="buyingControl-outOfStock"]')
        if out_of_stock or not add_to_bag:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract_first().split('__PRELOADED_STATE__ =')[-1].strip())
        code = list(data['entities']['products'].keys())[0]
        product = data['entities']['products'][code]
        item['sku'] = code if code.isdigit() else ''
        item['name'] = product['name']
        item['description'] = product['description']
        item['designer'] = list(data['entities']['brands'].values())[0]['name'].upper()
        item['tmp'] = product

    def _prices(self, prices, item, **kwargs):
        item['originlistprice'] = item['tmp']['price']['formatted']['includingTaxesWithoutDiscount']
        item['originsaleprice'] = item['tmp']['price']['formatted']['includingTaxes']

    def _sizes(self, sizes, item, **kwargs):
        orisizes = item['tmp']['sizes']
        osizes = []
        item['originsizes'] = []
        for osize in orisizes:
            if not osize['isOutOfStock']:
                size = osize['name']
                if item['category'] in ['c', 's'] and size.replace('.','').isdigit() and float(size) < 20:
                    size = 'UK ' + size
                osizes.append(size)
        item['originsizes'] = osizes

    def _color(self,colors, item, **kwargs):
        try:
            item['color'] = item['tmp']['colors'][-1]['color']['name']
        except:
            item['color'] = ''

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['images']
        item['images'] = []
        for img in imgs:
            image = img['sources']['600']
            item['images'].append(image)
        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[contains(text(),"PRELOADED_STATE")]/text()').extract_first().split('__PRELOADED_STATE__ =')[-1].strip())
        imgs = list(data['entities']['products'].values())[0]['images']

        images = []
        for img in imgs:
            image = img['sources']['600']
            images.append(image)

        return images

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h2[@data-test="title"]/text()').extract_first()
        html_origin = response.xpath('//main[@id="siteContent"]').extract_first()
        key = response.url.split('?')[0].split('/')[-1]
        cover = response.xpath('//img[@loading="lazy"]/@src').extract_first()
        cover = urljoin(response.url, cover)

        # try:
        #     date = response.xpath('//div[@class="sn-story_date"]//text()').extract()[-1].strip()
        #     dates = []
        #     for t in date.split(' '):
        #         t = months_num.get(t,t)
        #         dates.append(t)
        #     dates.reverse()

        #     timeStruct = time.strptime('-'.join(dates), "%Y-%m-%d")
        #     publish_datetime = time.strftime("%Y-%m-%d", timeStruct)
        # except:
        #     publish_datetime = None

        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs_set = []

        for node in response.xpath('//main[@id="siteContent"]/*'):
            imgs = node.xpath('.//picture//img/@src | .//video//source/@src').extract()
            for img in imgs:
                images = {"type": "image","alt": ""}
                image = urljoin(response.url, img)
                if image not in imgs_set:
                    images['src'] = image
                    html_parsed['items'].append(images)
                    imgs_set.append(image)

            header = node.xpath('.//h2/text()').extract_first()
            if header:
                headers = {"type": "header"}
                headers['value'] = header
                html_parsed['items'].append(headers)

            htmls = node.xpath('.//div/text() | .//span[@data-test="credit-role"]/text() | .//p[not(@itemprop="name")]').extract()
            for text in htmls:
                texts = {"type": "html"}
                texts['value'] = text
                html_parsed['items'].append(texts)

            links = node.xpath('.//div[contains(@data-test,"ProductCard")]/a/@href').extract()

            products = {"type": "products","pids":[]}
            for link in links:
                prod = parseProdLink(link)
                if prod[0]:
                    for product in prod[0]:
                        pid = product.id
                        products['pids'].append(pid)
            if products['pids']:
                html_parsed['items'].append(products)

        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])
        return title, cover, key, html_origin, html_parsed

    def _parse_look(self, item, look_path, response, **kwargs):
        script = response.xpath('//script[contains(text(),"__PRELOADED_STATE__")]/text()').extract_first()
        data = json.loads(script.split('__PRELOADED_STATE__ =')[-1].strip())

        setId = data['entities']['products'][kwargs['sku']]['recommendedSet']

        link = look_path['url_base'] + str(setId)
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US',
            'referer': 'https://www.harrods.com/',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        }

        result = requests.get(link,headers=headers)
        data2 = json.loads(result.text)
        products = data2['products']['entries']

        if not products:
            return

        outfits = []

        for product in products:
            outfits.append(product['id'])

        item['main_prd'] = response.meta.get('sku')

        item['products'] = outfits
        item['cover'] = ''

        if not item['cover']:
            return

        yield item
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="show-results-desktop"]/strong/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('products',''))
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        data = json.loads(response.xpath(size_info['size_info_path']).extract_first().split('__PRELOADED_STATE__ =')[-1].strip())
        code = list(data['entities']['products'].keys())[0]
        product = data['entities']['products'][code]
        address = code + "_Dimensions_en_pub"
        try:
            infos = data['entities']['products']['contents'][address]["components"][0]["components"][0]["contents"]
        except:
            infos = ''
        return infos 

_parser = Parser()


class Config(MerchantConfig):
    name = "harrods"
    merchant = 'Harrods'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//ul[contains(@class,"control_paging-list")]/li[last()]/a/text()',
            items = '//li[@class="product-grid_item"]',
            designer = './/span[@class="product-card_brand"]/text()',
            link = './/a[@class="product-card_link js-product-card_link"]/@href',
            ),
        product = OrderedDict([
            ('checkout',('//html', _parser.checkout)),
            ('sku',('//script[contains(text(),"PRELOADED_STATE")]/text()', _parser.sku)),
            ('color',('//html',_parser.color)),
            ('prices', ('//html', _parser.prices)),
            ('sizes',('//html',_parser.sizes)),
            ('images',('//html',_parser.images)),
            ]),
        look = dict(
            # can not get full model image
            # merchant_id='Harrods',
            # official_uid=24081,
            # url_type='link',
            # key_type='sku',
            # type='html',
            # method = _parser.parse_look,
            # url_base='https://www.harrods.com/en-us/api/recommendedsets/',
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//script[contains(text(),"PRELOADED_STATE")]/text()',
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//script[contains(text(),"PRELOADED_STATE")]/text()',

            ),
        blog = dict(
            official_uid = 24081,
            blog_list_url = _parser.blog_list_url,
            link = '//ul[@class="sn-hero-banner-carousel_list js-gallery"]/li/a/@href | //ul[@class="nav_style-notes-list"]/li/a/@href | //ul[@class="story-links_list"]/li/a/@href',
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),

        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.harrods.com/en-us/shopping/women-accessories-belts',
                'https://www.harrods.com/en-us/shopping/women-accessories-hats',
                'https://www.harrods.com/en-us/shopping/women-accessories-sunglasses',
                'https://www.harrods.com/en-us/shopping/women-accessories-wallets-purses',
            ],
            b = [
                'https://www.harrods.com/en-us/shopping/women-bags',
                'https://www.harrods.com/en-us/shopping/luggage'
            ],
            c = [
                'https://www.harrods.com/en-us/shopping/women-clothing'
            ],
            s = [
                'https://www.harrods.com/en-us/shopping/women-shoes'
            ],
            e = [
                'https://www.harrods.com/en-us/shopping/beauty-perfume-womens-perfume'
            ],
        ),
        m = dict(
            a = [
                'https://www.harrods.com/en-us/shopping/men-accessories-belts',
                'https://www.harrods.com/en-us/shopping/men-accessories-cufflinks',
                'https://www.harrods.com/en-us/shopping/men-accessories-sunglasses',
                'https://www.harrods.com/en-us/shopping/men-accessories-ties',
                'https://www.harrods.com/en-us/shopping/men-accessories-wallets'
            ],
            b = [
                'https://www.harrods.com/en-us/shopping/men-bags'
            ],
            c = [
                'https://www.harrods.com/en-us/shopping/women-clothing'
            ],
            s = [
                'https://www.harrods.com/en-us/shopping/men-shoes'
            ],
            e = [
                'https://www.harrods.com/en-us/shopping/beauty-perfume-mens-perfume'
            ],


        params = dict(
            page = 1,
            ),
        ),

        country_url_base = '/us/',
    )

    blog_url = dict(
        EN = ['https://www.harrods.com/en-gb/style-notes?icid=megamenu_style-notes']
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = '$',
            country_url = 'harrods.com/en-us/',
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = 'harrods.com/en-cn/',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'harrods.com/en-gb/',
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'harrods.com/en-hk/',
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = 'harrods.com/en-jp/',
        ),
        KR = dict(
            currency = 'KR',
            currency_sign = '\u20a9',
            country_url = 'harrods.com/en-kr/',
        ),
        SG = dict(
            currency = 'SGD',
            currency_sign = '$',
            country_url = 'harrods.com/en-sg/',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = 'harrods.com/en-de/',
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = '\u20bd',
            thousand_sign = '\xa0',
            country_url = 'harrods.com/en-ru/',
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = '$',
            country_url = 'harrods.com/en-ca/',
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = '$',
            country_url = 'harrods.com/en-au/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            thousand_sign = '\xa0',
            country_url = 'harrods.com/en-no/',
        ),

        )
