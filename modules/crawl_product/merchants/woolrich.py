from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json

class Parser(MerchantParser):
    def _checkout(self,res,item,**kwargs):
        if res.extract():
            return False
        else:
            return True

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('sz=','sz=%s')%(28)
        return url

    def _page_num(self, data, **kwargs):
        page = data//28
        return page

    def _prices(self,res,item,**kwargs):
        saleprice = res.xpath('//div[@class="price"]//span[@class="sales "]/span/text() | //span[@class="sales discounted"]/span/text()').extract_first().strip()
        try:
            listprice = res.xpath('.//div[@class="price"]//span[@class="strike-through list"]/span/text()').extract()
        except:
            item['originlistprice'] = saleprice
        for price in listprice:
            if price.strip():
                item['originlistprice'] = price.strip()
        item['originsaleprice'] = saleprice

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)
        item['designer'] = 'WOOLRICH'

    def _images(self,res,item,**kwargs):
        imgs = res.extract()
        images = []
        cover = None
        for img in imgs:
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]

    def _sizes(self,res,item,**kwargs):
        sizes = res.extract()
        size_li = []
        for size in sizes:
            if size not in size_li:
                size_li.append(size.strip()) 
        item['originsizes'] = size_li
        
    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="product-images"]/div//picture/img/@data-src').extract()
        images_li = []
        for image in images_li:
                images_li.append(img)
        return images_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "woolrich"
    merchant = "Woolrich"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="result-number"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-tile-body"]',
            designer = './a/@data-component',
            link = './a/@href',
        ),
        product=OrderedDict([
            ('checkout',('//div[@class="size-attribute-wrapper"]/div/button[not(contains(@class,"not-available"))]',_parser.checkout)),
            ('sku', '//button[@class="add-to-wish-list"]/@data-option-pid | //div[@class="product-detail-container product-wrapper"]/@data-pid'),
            ('name','//h1[@class="product-heading"]/span[@class="product-heading-name"]/text()'),
            ('description',('//div[@class="product-short-description"]/ul/li/text()',_parser.description)),
            ('price',('//html',_parser.prices)),
            ('color','//span[@class="product-heading-color"]/text()'),
            ('image',('//div[@class="product-images"]/div//picture/img/@data-src',_parser.images)),
            ('sizes', ('//div[@class="size-attribute-wrapper"]/div/button[not(contains(@class,"not-available"))]/text()', _parser.sizes)),

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
            size_info_path = '//div[@class="accordion-content"]/div[@class="fit-info"]',
            ),
        blog = dict(
        ),
        checknum = dict(
            ),
    )

    blog_url = dict(
        EN = ['https://www.woolrich.com/us/en/brand-mission-values/brand-mission-values.html']
    )

    list_urls = dict(
        f = dict(
            c = [
                "https://www.woolrich.com/us/en/women/?cgid=WOMEN&sz=",
            ],
        ),
        m = dict(
            c = [
                "https://www.woolrich.com/us/en/men/?cgid=MEN&sz=",
            ],
        u = dict(
            h = [
                "https://www.woolrich.com/us/en/blankets/?cgid=MEN&sz="
            ],
        )
        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US=dict(
            currency = 'US',
            currency_sign = '$'
        ),
    )