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
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        num_data = int(data.extract_first().strip().lower().split("of")[-1].split("results")[0].replace(',',''))/50 +1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('/page/')[0] + '/page/%s'%(i)
        return url

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().split("code:**")[-1].split('**')[0].strip().upper()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()[1:]
        size_li = []
        if item['category'] in ['a','b']:
            if not sizes:
                size_li.append('IT')
            else:
                size_li = sizes
        else:
            for size in sizes:
                if size.strip() not in size_li:
                    size_li.append(size.strip())
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="list_price"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0]
        except:
            item['originlistprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0]
    def _color(self, color, item, **kwargs):
        item['color'] = ''


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//*[@class="woocommerce-product-gallery__image"]/a/@href').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = img.replace('//','https://')
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        print(response.xpath('//p[@class="woocommerce-result-count"]/text()').extract_first().strip().lower().split("of")[-1].split("results")[0].replace(',',''))
        number = int(response.xpath('//p[@class="woocommerce-result-count"]/text()').extract_first().strip().lower().split("of")[-1].split("results")[0].replace(',',''))
        return number
    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'Dimensions' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or '(LxWxH)' in info or 'height' in info.lower() or ' x ' in info or ' mm.' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 

_parser = Parser()



class Config(MerchantConfig):
    name = 'coveti'
    merchant = 'Coveti'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="woocommerce-result-count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//*[@data-source="main_loop"]//div[@class="product-information"]',
            designer = './div[@class="woodmart-product-brands-links"]/a/text()',
            link = './h3/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"add_to_cart")]', _parser.checkout)),
            ('images',('//*[@class="woocommerce-product-gallery__image"]/a/@href',_parser.images)), 
            ('sku',('//span[@class="product_id"]/text()',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('designer','//div[@class="woodmart-product-brands-links"]/a/text()'),
            ('color',('//@data-gtm-variant',_parser.color)),
            ('description', ('//div[@id="tab-description"]//div[@class="woodmart-scroll-content"]/div/div[1]//div[@class="wpb_wrapper"]//p/text()|//div[@id="tab-description"]//div[@class="woodmart-scroll-content"]//text()',_parser.description)),
            ('prices', ('//div[@class="nosto_product"]', _parser.prices)),
            ('sizes',('//select[@id="pa_size"]/option/text()',_parser.sizes)),
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
            size_info_path = '//div[@id="tab-description"]//div[@class="woodmart-scroll-content"]/div/div[1]//div[@class="wpb_wrapper"]//p/text()|//div[@id="tab-description"]//div[@class="woodmart-scroll-content"]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://coveti.com/product-category/men/men-jewellery/page/1",
                "https://coveti.com/product-category/men/men-accessories/page/1"
            ],
            b = [
                "https://coveti.com/product-category/men/men-bags/page/1"
            ],
            c = [
                'https://coveti.com/product-category/men/clothing-men/page/1'
            ],
            s = [
                "https://coveti.com/product-category/men/men-shoes/page/1",
                ],
        ),
        f = dict(
            a = [
                "https://coveti.com/product-category/women/women-jewellery/page/1",
                "https://coveti.com/product-category/women/women-accessories/page/1"
            ],
            b = [
                "https://coveti.com/product-category/women/women-bags/page/1"
            ],
            c = [
                'https://coveti.com/product-category/women/women-clothing/page/1'
            ],
            s = [
                "https://coveti.com/product-category/women/women-shoes/page/1",
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
#      
        )

        


