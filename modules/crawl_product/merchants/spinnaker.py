from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page = 30
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _sku(self, res, item, **kwargs):
        code = res.extract_first()
        item['sku'] = code if code.isdigit() else ''
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            images.append(img)

        item['images'] = images
        item['cover'] = images[0]

    def _sizes(self, res, item, **kwargs):
        sizes_li = res.xpath('./div[@class="field-size"]/label/text()').extract()
        sizes = []
        for size in sizes_li:
            if size:
                sizes.append(size.strip())
        item['originsizes'] = sizes

    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('./text()').extract_first()
        if listprice:
            saleprice = listprice
        else:
            listprice = res.xpath('./span[@class="detail__price--old"]/text()').extract_first()
            saleprice = res.xpath('./span[@class="detail__price--new"]/text()').extract_first()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"Product__SlideItem--image")]//noscript/img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = 'spinnaker'
    merchant = 'Spinnaker Boutique'

    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = '//div[@class="product__wrapper"]',
            designer = './span/@data-gtm-brand',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//button[@data-base="Add to shopping bag"]', _parser.checkout)),
            ('name','//div[@class="detail__infos"]/h2[@class="detail__subtitle"]/text()'),
            ('sku', ('//form[contains(@class,"js-contactus-form")]//input[@id="pkey"]/@value', _parser.sku)),
            ('designer','//div[@class="detail__infos"]/h1/span[@itemprop="name"]/a/text()'),
            ('images',('//div[contains(@class,"detail__photos-gallery")]//div[@class="swiper-slide"]/img/@data-zoom', _parser.images)),
            ('description', ('//div[@class="ProductMeta__Description"]//text()', _parser.description)),
            ('sizes',('//div[@class="detail__variants"]/div[@class="detail__sizes"]', _parser.sizes)),
            ('prices', ('//div[@class="detail__price"]/span[@itemprop="price"]', _parser.prices)),
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
        m = dict(
            a = [
                "https://www.spinnakerboutique.com/en-US/man/accessories?currPage={}"
            ],
            b = [
                "https://www.spinnakerboutique.com/en-US/man/bags?currPage={}"
            ],
            c = [
                "https://www.spinnakerboutique.com/en-US/man/clothing?currPage={}",
            ],
            s = [
                "https://www.spinnakerboutique.com/en-US/man/shoes?currPage={}",
            ],

        ),
        f = dict(
            a = [
                "https://www.spinnakerboutique.com/en-US/woman/accessories?currPage={}"
            ],
            b = [
                "https://www.spinnakerboutique.com/en-US/woman/bags?currPage={}"
            ],
            c = [
                "https://www.spinnakerboutique.com/en-US/woman/clothing?currPage={}",
            ],
            s = [
                "https://www.spinnakerboutique.com/en-US/woman/shoes?currPage={}",
            ],
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        )
    )

        


