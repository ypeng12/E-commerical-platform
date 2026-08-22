from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        sku = checkout.xpath('.//meta[@itemprop="sku"]/@content').extract_first()
        color_path = './/option[@data-sku="%s"]/text()' %sku
        color = checkout.xpath(color_path).extract_first()

        if not sku or not color:
            return True
        else:
            return False

    def _color(self, datas, item, **kwargs):
        color_path = './/option[@data-sku="%s"]/text()' %item['sku']
        item['color'] = datas.xpath(color_path).extract_first().split('-')[0].split('/')[0].strip()

    def _images(self, datas, item, **kwargs):
        image_path = './/div[@class="thumbWrap"]/div/a/img[@alt="%s"]/@src' %item['color']
        imgs = datas.xpath(image_path).extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            images.append(img.replace('_small',''))
        item['images'] = images
        item['cover'] = item['images'][0] if item['images'] else ''
        item['designer'] = 'SENREVE'

    def _description(self, description, item, **kwargs):
        description = description.extract_first()
        item['description'] = description.strip()

    def _sizes(self, sizes, item, **kwargs):
        preorders = sizes.extract_first().split('backorder-wrap no-message')[-1].split(')',1)[0]
        if 'Pre-order' in preorders:
            item['originsizes'] = ['IT:p']
        else:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.extract()
        listprice = prices.extract()
        
        item['originsaleprice'] = saleprice[0].strip()
        item['originlistprice'] = listprice[0].strip()

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        option = ''
        prd_script = ''
        scripts = response.xpath('//script/text()').extract()
        for script in scripts:
            if 'Shopify.product' in script:
                prd_script = script
                break        
        prds = json.loads(prd_script.split('Shopify.product = ')[-1].split('};')[0].strip() + '}')
        for prd in prds['variants']:
            if prd['sku'] == kwargs['sku']:
                option = prd['option2'] if prd['option2'] else prd['option1']
                break        
        image_path = '//img[@alt="%s"]/@data-src' %option        
        imgs = response.xpath(image_path).extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            if img not in images:
                images.append(img)

        return images

_parser = Parser()



class Config(MerchantConfig):
    name = "senreve"
    merchant = "SENREVE"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            items = '//a[@class="grid-product__image-link"]',
            designer = './/span[@class="product-designer"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('name', '//h1[@itemprop="name"]/text()'),  
            ('sku','//meta[@itemprop="sku"]/@content'),
            ('color',('//html', _parser.color)),
            ('images', ('//html', _parser.images)),
            ('description', ('//meta[@name="description"]/@content',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//span[@id="ProductPrice"]/@content', _parser.prices)),
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
            size_info_path = '//label[contains(text(),"DIMENSIONS")]/following-sibling::ul/li/text()',
            ),
        )

    list_urls = dict(
        f = dict(

            b = [
                "https://www.senreve.com/collections/shop?p="
            ],
        ),
        m = dict(
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
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
        ),

        )

        


