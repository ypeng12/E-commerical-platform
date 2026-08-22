from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        datas = json.loads(checkout.extract_first().split('var json_product = ')[-1].rsplit(';', 1)[0])
        item['tmp'] = datas
        for data in datas['variants']:
            if data['available']:
                return False
            else:
                return True

    def _sku(self, names, item, **kwargs):
        datas = item['tmp']

        item['sku'] = datas['variants'][0]['sku']
        item['name'] = datas['title'].split(' - ')[0].strip()
        item['color'] = datas['title'].split(' - ')[-1].strip()
        item['designer'] = 'STRATHBERRY'
        item['description'] = datas['description'].replace('<p>', '').replace('</p>', '').replace('<em>', '').replace('</em>', '')

        # if item['country'] == 'CN':
        #     item['originsaleprice'] = datas['offers'][0]['price']
        #     item['originlistprice'] = datas['offers'][0]['price']
        # else:
        #     item['originsaleprice'] = datas['offers']['price']
        #     item['originlistprice'] = datas['offers']['price']
        item['originsaleprice'] = str(datas['price'])[:-2] + '.' + str(datas['price'])[-2:]
        item['originlistprice'] = str(datas['price_max'])[:-2] + '.' + str(datas['price_max'])[-2:]
        self.prices(datas, item, **kwargs)

        item['originsizes'] = ['IT']
        self.sizes(datas, item, **kwargs)

    def _images(self, datas, item, **kwargs):
        data = item['tmp']

        item['images'] = []
        imgs = data['images']
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            item['images'].append(img)
        item['cover'] = item['images'][0]

    def _parse_item_url(self, response, **kwargs):
        if kwargs['country'].upper() not in ['US','JP']: 
            urls = response.xpath('//div[@id="product-loop"]//a[@class="view-collection"]/@href').extract()
            for url in urls:
                url = urljoin(response.url, url)
                result = getwebcontent(url)
                html = etree.HTML(result)
                if not html:
                    continue
                for quote in html.xpath('//div[@class="collection-swatches"]'):
                    href = quote.xpath('.//a/@href')
                    if href is None:
                        continue
                    for h in href:
                        url =  urljoin(response.url, h)
                        yield url,'Strathberry'
        else:
            pages = response.xpath('//span[@class="count"]/text()').extract()[0]
            page = int(pages.split(' ')[-1].split('.')[0])/40 +2
            for x in range(1,page):
                url = response.url.replace('page=1','page='+str(x))
                result = getwebcontent(url)
                html = etree.HTML(result)
                if not html:
                    continue
                for href in html.xpath('//div[@class="collection-swatches"]//a/@href'):
                    if href is None:
                        continue
                    url =  urljoin(response.url, href)
                    yield url,'Strathberry'


    def _parse_images(self, response, **kwargs):
        datas = response.xpath('//script[contains(text(),"var json_product")]/text()').extract_first()
        data = json.loads(datas.split('var json_product =')[-1].rsplit(';',1)[0].strip())
        images = []
        imgs = data['images']
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            images.append(img)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath('//ul[@class="description-atts"]/li')
        fits = []
        for info in infos:
            info = ''.join(info.xpath('.//text()').extract())
            if 'cm' in info:
                fits.append(info)       
        size_info = '\n'.join(fits)

        return size_info
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="count"]/text()').extract_first().strip().lower().split('of')[-1].replace(",",'').replace(".",'').strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = "strathberry"
    merchant = "Strathberry"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout', ('//script[@type="text/javascript"][contains(text(),"var json_product")]/text()', _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('images', ('//html', _parser.images)),
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
            size_info_path = '//html',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            b = [
                "https://us.strathberry.com/collections/the-strathberry-designer-collection?page="
            ]
        ),
        m = dict(
        params = dict(
            ),
        ),
        country_url_base = '//us.',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = 'us.strathberry.com'
        ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            discurrency = 'GBP',
            country_url = 'strathberry.cn'
        ),
        GB = dict(
            currency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            country_url = '//www.'
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            country_url = 'www.strathberry.com'
        )
        )

        


