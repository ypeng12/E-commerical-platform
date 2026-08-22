from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False
        
    
    def _page_num(self, data, **kwargs):
        page_num = int(data.strip().split(" ")[0].strip())/30

        return page_num +1
    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0]+'?p=' +str(i)

        return url

    def _color(self, data, item, **kwargs):
        color = data.extract_first()
        if color:
            item['color'] = color.upper()
        else:
            item['color'] = ""

    def _sku(self, pids, item, **kwargs):
        pid = pids.xpath('.//input[@name="product"]/@value').extract_first()
        item['sku'] = pid + '_' + item['color'].upper()


    def _images(self, data, item, **kwargs):

        img_li = data.xpath('//img[@class="lazyimg"]/@data-src').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        try:
            item['cover'] = images[0]
            item['images'] = images
        except:
            images = data.xpath('.//img[@class="lazyimg"]/@data-src').extract()
            item['cover'] = images[0]
            item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, data, item, **kwargs):
        size_dict = json.loads(data.xpath('.//script[contains(text(),"Magento_Swatches/js/swatch-renderer")]/text()').extract_first())
        sizes = list(size_dict['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']['attributes'].values())[0]['options']
        size_li = []
        for size in sizes:
            size_li.append(size['label'])

        item['originsizes'] = size_li
        if item['category'] in ['a','b','e'] and not size_li:
            size_li.append('IT')
            item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="price"]/text()').extract()
        listPrice = prices.xpath('.//span[@class="old-price price"]/text()').extract()

        item['originsaleprice'] = ''.join(salePrice[0].strip().replace('USD','').split()) if salePrice else ''
        item['originlistprice'] = ''.join(listPrice[0].strip().replace('USD','').split()) if listPrice else ''

    def _parse_images(self, data, **kwargs):
        img_li = data.xpath('//img[@class="lazyimg"]/@data-src').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)

        return images

    def _parse_swatches(self, response, swatch_path, **kwargs):
        pids = response.xpath(swatch_path['current_path']).extract()
        pids = pids[0].split('/product/')[-1].split('/')[0]
        colors = response.xpath(swatch_path['path']).extract()
        swatches = []
        for c in colors:
            c = c.replace('  ',' ').strip()
            pid = pids + '_' + c.upper()
            swatches.append(pid)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.replace('-','').strip() not in fits and ('Model' in info or 'cm' in info or 'Length' in info or 'height' in info):
                fits.append(info.replace('-','').strip())
        size_info = '\n'.join(fits)
        return size_info   

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="count-pr"]/text()').extract_first().strip().split(" ")[0].strip())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'bnkr'
    merchant = 'BNKR'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="count-pr"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-item-info"]',
            designer = './/h3/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[text()="Sold out"]', _parser.checkout)),
            ('color',('//strong[@class="color-text"]/text()',_parser.color)),
            ('sku', ('//html', _parser.sku)),
            ('name', '//*[@itemprop="name"]/text()'),
            ('designer', '//div[@class="product brand-label"]/p/text()'),
            ('images', ('//html', _parser.images)),
            ('description', ('//div[@id="product.info.description.cms"]//p/text()',_parser.description)), # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            current_path='//form[@class="product-view"]/@action',
            path='//ul[@id="ul-attribute92"]/li/span/text()',
            image_path = '//div[@data-colour="%s"]/img/@src'
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//ul[@class="accordion"]/li[1]//text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
                "https://us.fashionbunker.com/shop/accessories?p=1"
            ],
            b = [
            ],
            c = [
                "https://us.fashionbunker.com/shop/clothing?p=1",
                "https://us.fashionbunker.com/sale/sale-dresses?p=1",
                "https://us.fashionbunker.com/sale/sale-tops?p=1",
                "https://us.fashionbunker.com/sale/sale-skirts?p=1",
                "https://us.fashionbunker.com/sale/sale-bottoms?p=1",
                "https://us.fashionbunker.com/sale/sale-outerwear?p=1"
            ],
            s = [
                'https://us.fashionbunker.com/shop/shoes?p=1',
                'https://us.fashionbunker.com/sale/sale-shoes?p=1'
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = 'us.fashionbunker.com/',
            currency_sign = '$',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            country_url = 'fashionbunker.com.cn/',
            
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            
        ),
        KR = dict( 
            currency = 'KRW',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
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
            language = 'DE',
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
        


