from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from lxml import etree
import requests
import json
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if 'Add to Cart' in checkout.extract_first():
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = int(5)
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?page=%s'%(i)
        return url

    def _sku(self, sku_data, item, **kwargs):
        json_data = sku_data.extract_first()
        data = json.loads(re.search(r'products: \[(.*?)\]',json_data,re.M).group(1))
        item['sku'] = data['id']
        item['name'] = data['name']
        item['designer'] = data['brand']

    def _images(self, images, item, **kwargs):
        imgs_data = images.extract()
        images = []
        cover = None
        for img in imgs_data:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
        images.sort()

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[contains(@id,"ComparePrice")]/span/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[contains(@id,"ProductPrice")]/span/text()').extract()[0]
        except:
            item['originsaleprice'] =prices.xpath('.//span[contains(@id,"ProductPrice")]/span/text()').extract_first()
            item['originlistprice'] =prices.xpath('.//span[contains(@id,"ProductPrice")]/span/text()').extract_first()

    def _parse_images(self, response, **kwargs):
        imgs_data = response.xpath('//div[@class="swiper-wrapper"]/div[contains(@class,"justify-center")]/img/@src').extract()
        images = []
        cover = None
        for img in imgs_data:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
        images.sort()

        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="page"][last()]/a/text()').extract_first().strip())*32
        return number
        
    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = 'oluxury'
    merchant = 'Oluxury'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[contains(@class,"product-item relative")]',
            designer = './/div[@class="grid-product__meta"]/div[contains(@class,"vendor")]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="product-addtocart-button"]/span/text()', _parser.checkout)),
            ('sku',('//script[contains(text(),"dataLayer.push({")]/text()',_parser.sku)),
            ('images',('//div[@class="swiper-wrapper"]/div[contains(@class,"justify-center")]/img/@src',_parser.images)),
            ('color','//span[@class="color-name"]/text()'), 
            ('description', ('//div[@class="product-single__description rte"]/p//text()',_parser.description)),
            ('sizes',('//script[contains(text(),"initConfigurableOptions")][position()>1]/text()',_parser.sizes)),
            ('prices', ('//div[@class="product-single__meta"]', _parser.prices)),
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
        m = dict(
            a = [
                "https://www.oluxury.com/eu_en/man/accessories.html?p={}"
            ],
            b = [
                "https://www.oluxury.com/eu_en/man/bags.html?p={}"
            ],
            c = [
                "https://www.oluxury.com/eu_en/man/clothing.html?p={}",
            ],
            s = [
                "https://www.oluxury.com/eu_en/man/shoes.html?p={}"
            ],
        ),
        f = dict(
            a = [
                "https://www.oluxury.com/eu_en/woman/accessories.html?p={}",
                ],
            b = [
                "https://www.oluxury.com/eu_en/woman/bags.html?p={}"
            ],
            c = [
                "https://www.oluxury.com/eu_en/woman/clothing/dresses.html?p={}",
            ],
            s = [
                "https://www.oluxury.com/eu_en/woman/shoes.html?p={}"
            ],
        ),
        u = dict(
            h = [
                "https://www.oluxury.com/eu_en/woman/homeware.html?p={}"
            ],
        )

    )


    countries = dict(
        US = dict(
            language = 'EN', 
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
        )

        


