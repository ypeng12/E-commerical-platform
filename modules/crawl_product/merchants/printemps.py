from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser,parseProdLink
from utils.cfg import *
import time
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first():
            return False
        else:
            return True

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['name'] = json_data['name'].split(' | ')[0].upper()
        item['color'] = json_data['name'].split(' | ')[-1]
        item['description'] = json_data['description']
        item['designer'] = json_data['brand']['name']

    def _prices(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first().split('window.dataLayerProxy.push(')[-1].rsplit(');', 1)[0])
        item['tmp'] = json_data
        item['originlistprice'] = str(json_data['ecommerce']['detail']['products'][0]['initPrice'])
        item['originsaleprice'] = str(json_data['ecommerce']['detail']['products'][0]['price'])

    def _sizes(self, res, item, **kwargs):
        json_data = item['tmp']
        osizes = []
        orisizes = json_data['ecommerce']['detail']['products'][0]['sizes']
        for osize in orisizes:
            if osize['quantity']:
                size = osize['size']
                osizes.append(size)
        item['originsizes'] = osizes

    def _images(self, res, item, **kwargs):
        imgs = res.extract()
        images_li = []
        for img in imgs:
            if img not in images_li:
                images_li.append(img)
        item['images'] = images_li
        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="product-swiper"]//div[@class="swiper-zoom-container"]/img/@data-src-zoo').extract()
        images = []
        for img in imgs:
            images.append(img)

        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="show-results-desktop"]/strong/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('products',''))
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        datas = response.xpath(size_info['size_info_path']).extract()
        infos = []
        for data in datas:
            if data.strip() and data.strip() not in infos:
                infos.append(data.strip())

        return infos 

    def _page_num(self, data, **kwargs):
        page_num = data // 60
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

_parser = Parser()


class Config(MerchantConfig):
    name = "printemps"
    merchant = 'Printemps.com'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="number-articles"]/span/span[@class="nb-value"]/text()',
            list_url = _parser.list_url,
            items = '//div[@class="swiper"]/div/div[@class="swiper-slide"]',
            designer = './a/img/@alt',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//div[@data-select-one-size="available"]/a[@data-action="add-cart"]', _parser.checkout)),
            ('sku', '//div[@id="trigger-guide-taille"]/@data-item-id'),
            ('name', ('//script[@type="application/ld+json"][contains(text(),"offers")]/text()', _parser.name)),
            ('prices', ('//script[contains(text(),"dataLayerGtm = [];")]/text()', _parser.prices)),
            ('sizes',('//html', _parser.sizes)),
            ('images',('//div[@id="product-swiper"]//div[@class="swiper-zoom-container"]/img/@data-src-zoom', _parser.images)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//script[contains(text(),"PRELOADED_STATE")]/text()',
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="accordion-body"]/ul[contains(@class,"card-body")]/li/span//text()',
            ),
        blog = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),

        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.printemps.com/uk/en/all-accessories-women/page/{}',
            ],
            b = [
                'https://www.printemps.com/uk/en/all-bags-women/page/{}'
            ],
            c = [
                'https://www.printemps.com/uk/en/all-clothing-women/page/{}'
            ],
            s = [
                'https://www.printemps.com/uk/en/all-shoes-women/page/{}'
            ],
        ),
        m = dict(
            a = [
                'https://www.printemps.com/uk/en/all-accessories-men/page/{}'
            ],
            b = [
                'https://www.printemps.com/uk/en/all-bags-men/page/{}'
            ],
            c = [
                'https://www.printemps.com/uk/en/all-clothing-men/page/{}'
            ],
            s = [
                'https://www.printemps.com/uk/en/all-shoes-men/page/{}'
            ],

        params = dict(
            page = 1,
            ),
        ),

        country_url_base = '/us/',
    )

    countries = dict(
        GB = dict(
            currency = 'GBP',
            country_url = 'www.printemps.com/uk/en/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = 'www.printemps.com/fr/fr/',
        ),

        )
