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
        if "add to cart" in checkout.extract_first().lower():
            return False
        else:
            return True

    def page_num(self, data, **kwargs):
        nums = data.extract_first().strip()
        num = int(nums.split('of')[1])
        return num

    def list_url(self, i, response_url, **kwargs):
        return response_url.replace('?page=','?page={}'.format(i))

    def _sku(self, res, item, **kwargs):
        scripts = res.extract_first()
        data = json.loads(scripts.split('var BCData = ')[1].strip()[:-1])
        sku = data['product_attributes']['sku']
        item['sku'] = sku

    def _name(self, res, item, **kwargs):
        json_data = res.extract_first()
        name_data = json_data.strip().split('dataLayer.push(')[1].rsplit(');',1)[0]
        name = re.search(r'name\': "(.*?)"',name_data).group(1)
        item['name'] = name


    def _designer(self, data, item, **kwargs):
        item['designer'] = 'DR. BARBARA STURM'

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, res, item, **kwargs):
        description = res.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.extract_first()
        listprice = prices.extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[@class="swiper-container swiper-product-pc"]/div/div/img/@src').extract()
        images = []
        for img in img_li:
            img = 'https:' + img.split('?')[0]
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and 'Dimensions' in info.strip():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()


class Config(MerchantConfig):
    name = 'drsturm'
    merchant = "Dr. Barbara Sturm"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="pagination-item"]/a/@aria-label',_parser.page_num),
            list_url = _parser.list_url,
            items = '//figure[@class="card-figure"]',
            designer = './a/div/img/@alt',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="form-action"]/input/@value', _parser.checkout)),
            ('sku', ('//script[contains(text(),"var BCData =")]/text()',_parser.sku)),
            ('name', ('//script[contains(text(),"ataLayer.push({")]/text()',_parser.name)),
            ('designer', ('//noscript',_parser.designer)),
            ('images', ('//div[@class="productView-thumbnail-desktop"]/a/@href', _parser.images)),
            ('description', ('//noscript/ul/li/text()',_parser.description)), # TODO:
            ('prices', ('//span[@class="price price--withTax"]/text()', _parser.prices)),
            ('sizes', ('//html', _parser.sizes))
            ]),
        look = dict(
            ),
        swatch = dict(
            
            ),
        image = dict(
            image_path = '//div[@class="productView-thumbnail-desktop"]/a/@href',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@itemprop="description"]//text()',   
            ),
        )
    list_urls = dict(
        m = dict(
            e = [
                'https://www.drsturm.com/skincare/shop-by-me/men/?sort=featured&page='
            ],
        ),
        f = dict(
            e = [
                'https://www.drsturm.com/skincare/shop-by-me/women/?sort=featured&page='
            ],
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            country_url = 'drsturm.com',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            # country_url = '',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = 'de.drsturm.com',
        ),

        )
        


