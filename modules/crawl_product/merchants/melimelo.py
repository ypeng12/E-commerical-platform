from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if not checkout.extract():
            return True
        else:
            return False

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            image = 'https:' + img.replace('.jpg','_650x.jpg')
            item['images'].append(image)
        item['cover'] = item['images'][0]
        item['designer'] = 'MELI MELO'

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if desc.strip() != '':
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.strip().replace('Description\n','')


    def _sizes(self, sizes, item, **kwargs):
        item['color'] = item['name'].split('|')[-1].upper().strip()

        item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):
        try:
            saleprice = prices.xpath('//span[@id="ProductPrice-product-template"]/span/text()').extract()[0]
            listprice = prices.xpath('//del[@id="ComparePrice-product-template"]/span/span/text()').extract()[0]
        except:
            saleprice = prices.xpath('//span[@id="ProductPrice-product-template"]/span/text()').extract()[0]
            listprice = prices.xpath('//span[@id="ProductPrice-product-template"]/span/text()').extract()[0]

        item['originsaleprice'] = saleprice.strip()
        item['originlistprice'] = listprice.strip()

    def _parse_item_url(self, response, **kwargs):
        page = 3
        for x in range(1,page):
            url = response.url.replace('page=1','page='+str(x))
            result = getwebcontent(url)
            html = etree.HTML(result)
            if not html:
                continue
            for href in html.xpath('//a[@class="un-loop-thumbnail"]/@href'):
                if not href:
                    continue
                url =  urljoin(response.url, href)
                yield url,'MELI MELO'

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//figure[@id="product-images-product-template"]//div/a/@href').extract()
        images = []
        for img in imgs:
            image = 'https:' + img.replace('.jpg','_650x.jpg')
            images.append(image)

        return images


_parser = Parser()



class Config(MerchantConfig):
    name = "melimelo"
    merchant = "meli melo"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout', ('//span[@id="AddToCartText-product-template"]', _parser.checkout)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('sku', '//div[@id="yotpo-product-page"]/div/@data-product-id'),
            ('images', ('//figure[@id="product-images-product-template"]//div/a/@href', _parser.images)),
            ('description', ('//div[@id="tab-description"]/div[@class="row"]//text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
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
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.melimelo.com/collections/meli-melo-accessories?page=",
            ],
            b = [
                "https://www.melimelo.com/collections/nyc-x-meli-melo?page=",
                "https://www.melimelo.com/collections/designer-handbags?page=",
            ],
        ),
        m = dict(
            b = [
                "https://www.melimelo.com/collections/mens?page="
            ],

        params = dict(
            # TODO:
            ),
        ),
        country_url_base = '',
    )


    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        CN = dict(
            area = 'CN',
            currency = 'CNY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            currency_sign = '\xa3',
        ),
        JP = dict(
            area = 'JP',
            currency = 'JPY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        SG = dict(
            area = 'SG',
            currency = 'SGD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        HK = dict(
            area = 'HK',
            currency = 'HKD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        AU = dict(
            area = 'AU',
            currency = 'AUD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        DE = dict(
            area = 'DE',
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),

        )

        


