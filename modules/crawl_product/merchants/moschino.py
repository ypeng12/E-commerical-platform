from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _name(self, data, item, **kwargs):
        item['name'] = data.xpath('.//h1[@id="product-name"]/text()').extract_first()
        item['designer'] = data.xpath('.//div[@data-brand]/@data-brand').extract_first()

    def _sku(self, scripts, item, **kwargs):
        sku_script = ''
        scripts = scripts.extract()
        for script in scripts:
            if 'product_id' in script:
                sku_script = script
                break
        if sku_script:
            item['sku'] = sku_script.split('product_id":')[-1].split(',')[0]

    def _prices(self, prices, item, **kwargs):
        try:
            item['originsaleprice'] = prices.xpath('.//span[contains(@id,"product-price")]/text()').extract()[0].replace('USD','').strip()
            item['originlistprice'] = prices.xpath('.//span[contains(@id,"old-price")]/text()').extract()[0].replace('USD','').strip()
        except:
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].replace('USD','').strip()
            item['originlistprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].replace('USD','').strip()

    def _images(self, response, item, **kwargs):
        sku = response.xpath('.//span[@class="supplier_article_code"]/text()').extract_first()
        images1 = response.xpath('.//div[@class="thumb"]//img//@data-src').extract()
        if len(images1) == 0:
            images1 = response.xpath('.//figure[@class="image-item"]//img//@data-src').extract()
        imgset = set()
        cover = None
        for img in images1:
            if sku[-4:] in img or '-'+sku[-3:]+'-' in img:
                img = img.replace('/300x383/','/900x1148/').replace('/300x450/','/900x1148/')
                imgset.add(img)
                if '-1_' in img or '-1.' in img:
                    cover = img
        rImages = list(imgset)
        rImages = sorted(rImages)
        item['cover'] = cover
        item['images'] = rImages
        
    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@data-tab-content="tabs-0"]/p[1]/text()').extract() + description.xpath('.//div[@data-tab-content="tabs-0"]//ul/li/text()').extract() +description.xpath('.//div[@id="tab-fit-content"]//text()').extract()
        desc_li = []
        for desc in description:
            if desc.strip() != ' ' or desc.strip() != '' or desc.strip() != '\n':
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.strip().replace('\n\n','').replace(':\n',': ').replace('cm','cm ')

    def _sizes(self, sizes, item, **kwargs):
        orisizes = sizes.xpath('.//ul[@id="configurable_swatch_size"]//a/@title').extract()
        item['originsizes'] = []
        for osize in orisizes:
            item['originsizes'].append(osize)

    def _page_num(self, pages, **kwargs): 
        page_num = 1
        return page_num

    def _parse_item_url(self, response, **kwargs):
        products = json.loads(response.body)
        url = None
        for p in products['products']:
            url = response.url.split('vanilla')[0] + p['request_path']   
            yield url,'MOSCHINO'

    def _parse_images(self, response, **kwargs):
        sku = kwargs['sku']
        images1 = response.xpath('//div[@class="thumb"]//img//@data-src').extract()
        if len(images1) == 0:
            images1 = response.xpath('//figure[@class="image-item"]//img//@data-src').extract()
        imgset = set()
        cover = None
        for img in images1:
            if sku[-4:] in img or '-'+sku[-3:]+'-' in img:
                img = img.replace('/300x383/','/900x1148/')
                imgset.add(img)
                if '-1_' in img or '-1.' in img:
                    cover = img
        rImages = list(imgset)
        rImages = sorted(rImages)
        return rImages


    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.body)
        number = len(obj['products'])
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = "moschino"
    merchant = "MOSCHINO"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="products"]/@data-ytos-opt',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            items = '//a[@class="images-wrapper"]',
            designer = '@data-ytos-track-product-data',
            link = '@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="product-addtocart-button"]', _parser.checkout)),
            ('sku',('//script/text()', _parser.sku)),
            ('name', ('//html',_parser.name)),
            ('images', ('//html', _parser.images)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//div[@class="buying-actions"]//div[@class="price-box"]', _parser.prices)), 
            ('color', '//ul[@id="configurable_swatch_color"]//span[last()]/text()'),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/81?p=",
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/287?p="
            ],
            b = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/67?p=",
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/203?p="
            ],
            c = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/33?p=",
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/391?p=",
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/391?p=",
            ],
            s = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/55?p=",
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/215?p=",
            ],

        ),
        m = dict(
            a = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/149?p="
            ],
            b = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/143?p=" 
            ],
            c = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/117?p="
            ],
            s = [
                "https://www.moschino.com/us_en/vanilla/catalog/category/id/133?p="
            ],


        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/us_en/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/us_en/',
            ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            area = 'EU',
            country_url = '/jp_en/',
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = '\xa5',
            area = 'EU',
            thousand_sign = ' ',
            discurrency = 'EUR',
            country_url = '/ru_en/',
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            discurrency = 'USD',
            language = 'ZH',
            country_url = '/hk_zh/',
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = 'USD',
            country_url = '/row2_en/',
        ),
        GB = dict(
            currency = 'GBP',
            area = 'EU',
            country_url = '/gb_en/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/ca_en/',
        ),
        AU = dict(
            currency = 'AUD',
            area = 'EU',
            discurrency = 'USD',
            country_url = '/au_en/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            language = 'DE',
            country_url = '/de_de/',
            currency_sign = 'EUR \xa0',
            thousand_sign = '.',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = '/sc_en/',
        ),

        )

        


