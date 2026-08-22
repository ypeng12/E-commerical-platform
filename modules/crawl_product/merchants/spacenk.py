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
    def _page_num(self, data, **kwargs):
        page_num = 1
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?page='+str(i)
        return url
    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['images'] = []
        cover = None
        for img in images:   
            if 'http' not in img:
                img = 'https:' + img
            if img not in item['images']:
                item['images'].append(img)


        item['cover'] = item['images'][0] if item['images'] else ''



    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].strip().split(' ')[0].upper()


    def _description(self, description, item, **kwargs):
        description = description.xpath('.//section[@id="pdp-accordion"]/div[1]//text()').extract() + description.xpath('.//section[@id="pdp-accordion"]/div[2]//text()').extract()
        desc_li = []
        for desc in description:
            if desc.strip() != '':
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.replace('\n\n','\n').replace('\n\n','\n').replace('\t','').strip()
        item['designer'] = item["designer"].upper()
    def _sizes(self, sizes, item, **kwargs):
        osizes = sizes.extract()
        sizes = []
        for osize in osizes:
            sizes.append(osize.strip())
        item['originsizes'] = sizes
        if len(sizes) == 0:
            item['originsizes'] = ['OneSize']
        

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span/@data-price').extract()
        listprice = prices.xpath('.//span/@data-price').extract()
        if len(salePrice) == 0:
            salePrice = prices.xpath('./div/text()').extract()
            item['originsaleprice'] = salePrice[0].split('-')[0].strip()
            item['originlistprice'] = salePrice[0].split('-')[-1].strip()
        elif salePrice:
            item['originsaleprice'] = salePrice[0].strip()
            item['originlistprice'] = listprice[0].strip()
        else:
            item['originsaleprice'] = ''
            item['originlistprice'] = ''


    


_parser = Parser()


class Config(MerchantConfig):
    name = 'spacenk'
    merchant = 'SpaceNK'
    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[@id="search-result-items"]//div[@class="product-tile"]',
            designer = './/span[@itemprop="brand"]/span[@itemprop="name"]/text()',
            link = './/div[@class="product-swatches"]//a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//*[@id="add-to-cart"]', _parser.checkout)),
            ('images',('//div[contains(@class,"product-main-image")]//div[@class="product-thumbnails_item"]/a/img/@src | //img[@class="js-primary-image primary-image"]/@src',_parser.images)), 
            ('sku',('//span/@data-master-product-id',_parser.sku)),
            ('name', '//h1[@class="product-name"]/text()'),
            ('designer', '//*[@class="product-brand"]//text()'),
            ('description', ('//html',_parser.description)),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
            ('sizes',('//ul[@id="va-size"]/li/a/span[@class="js-size-value"]/@data-size-value',_parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[contains(@class,"product-main-image")]//div[@class="product-thumbnails_item"]/a/img/@src | //img[@class="js-primary-image primary-image"]/@src',
            ),
        size_info = dict(

            ),
        )

    list_urls = dict(
        f = dict(
            e = [
                "https://www.spacenk.com/us/en_US/skincare-3/",
                "https://www.spacenk.com/us/en_US/makeup-2/",
                "https://www.spacenk.com/us/en_US/haircare-1/",
                "https://www.spacenk.com/us/en_US/bath-body-1/",
                "https://www.spacenk.com/us/en_US/fragrance-1/",
                "https://www.spacenk.com/us/en_US/accessories/",
                "https://www.spacenk.com/us/en_US/sun-tan/",
                "https://www.spacenk.com/us/en_US/travel-size/"
            ],

        ),
        m = dict(
            a = [
            ],

        params = dict(
            # TODO:
            ),
        ),

    )


    countries = dict(
        US = dict(
            currency = 'USD',
            language = 'EN', 
            area = 'US',
            country_url = '/us/en_US/'

            ),
        JP = dict(
            currency = 'JPY',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','//haircare//'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3"
            

        ),
        CN = dict(
            currency = 'CNY',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/zh_CN/',
            language = 'ZH',
            translate = [
            ('/skincare-3/','/%E6%8A%A4%E8%82%A4%E5%93%81/'),
            ('/makeup-2/','/%E5%8C%96%E5%A6%86%E5%93%81/'),
            ('/haircare-1/','/%E6%8A%A4%E5%8F%91%E7%94%A8%E5%93%81/'),
            ('/bath-body-1/','/%E6%B2%90%E6%B5%B4%E5%92%8C%E7%BE%8E%E4%BD%93/'),
            ('/fragrance-1/','/%E9%A6%99%E6%B0%B4%E9%A6%99%E6%B0%9B/'),
            ('/accessories/','/%E9%85%8D%E5%A5%97%E7%94%A8%E5%93%81/'),
            ('/sun-tan/','/%E9%A6%99%E6%B0%B4%E9%A6%99%E6%B0%9B/'),
            ('/travel-size/','/%E9%98%B2%E6%99%92%E5%92%8C%E7%BE%8E%E9%BB%91/'),
            ],
            currency_sign = "\u00A3",

        ),
        KR = dict(
            currency = 'KRW',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','//haircare//'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",
        ),
        SG = dict(
            currency = 'SGD',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','//haircare//'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",

        ),
        HK = dict(
            currency = 'HKD',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','//haircare//'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",

        ),
        GB = dict(
            currency = 'GBP',
            area = 'EU',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','/haircare/'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",

        ),

        CA = dict(
            currency = 'CAD',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','/haircare/'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",

        ),
        AU = dict(
            currency = 'AUD',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','/haircare/'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",
        ),
        DE = dict(
            currency = 'EUR',
            area = 'EU',
            language = 'DE',
            discurrency = 'GBP',
            country_url = '/uk/de/',
            translate = [
            ('/skincare-3/','/hautpflege/'),
            ('/makeup-2/','/make-up/'),
            ('/haircare-1/','/haarpflege/'),
            ('/bath-body-1/','/bad--und-k%C3%B6rperpflege/'),
            ('/fragrance-1/','/duft/'),
            ('/accessories/','/accessoires/'),
            ('/sun-tan/','/sonnenpflege/'),
            ],
            currency_sign = "\u00A3",

        ),
        NO = dict(
            currency = 'NOK',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','/haircare/'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",
        ),
        RU = dict(
            currency = 'RUB',
            area = 'EU',
            discurrency = 'GBP',
            country_url = '/uk/en_GB/',
            translate = [
            ('/skincare-3/','/skincare/'),
            ('/makeup-2/','/makeup/'),
            ('/haircare-1/','/haircare/'),
            ('/bath-body-1/','/bath-body/'),
            ('/fragrance-1/','/fragrance/'),
            ],
            currency_sign = "\u00A3",
        ),
        )

        


