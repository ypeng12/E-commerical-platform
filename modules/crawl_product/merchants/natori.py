from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout:
            return True
        else:
            return False

    def _sku(self,res,item,**kwargs):
        data = json.loads(res.xpath('//script[contains(text(),"var BCData =")]/text()').extract_first().split('var BCData = ')[1].rsplit(';',1)[0])
        color = res.xpath('//span[@class="form-option-text"]/text()').extract_first()
        item['tmp'] = data
        if color:
            item['sku'] = data['product_attributes']['sku'] + '_' + color.upper()
        else:
            item['sku'] = data['product_attributes']['sku']

    def _images(self, res, item, **kwargs):
        images = res.extract()
        images_li = []
        for image in images:
            if image not in images_li:
                images_li.append(image)
        item['images'] = images_li
        item['cover'] = images_li[0]

    def _prices(self, res, item, **kwargs):
        saleprice = item['tmp']['product_attributes']['price']['without_tax']['formatted']
        if "rrp_without_tax" in item['tmp']['product_attributes']['price'].keys():
            listprice = item['tmp']['product_attributes']['price']['rrp_without_tax']['formatted']
        else:
            listprice = saleprice
        item["originlistprice"] = listprice
        item["originsaleprice"] = saleprice

    def _sizes(self,res,item,**kwargs):
        size_ids = res.xpath('./select/option/@value').extract()
        avail_size_id = item['tmp']['product_attributes']['available_variant_values']
        size_li = []
        for size_id in size_ids:
            if size_id and int(size_id) in avail_size_id:
                osize = res.xpath('./select/option[@value="{}"]/text()'.format(size_id)).extract_first()
                size_li.append(osize.strip())
        item["originsizes"] = size_li

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="application/ld+json"][contains(text(),"image")]/text()').extract_first())
        return data['image']

    def _page_num(self, data, **kwargs):
        return nums

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

_parser = Parser()

class Config(MerchantConfig):
    name = "natori"
    merchant = "Natori"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination"]/ul/li/a/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="card-body"]/div[@class="card-body-left"]',
            designer = './p/text()',
            link = './h4/a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//div[@class="form-action"]/input/@value="Add to Bag"',_parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('name', '//div[@class="container"]/ul/li/span[@class="breadcrumb-label"]/text()'),
            ('color', ('//span[@class="form-option-text"]/text()')),
            ('designer', '//div[@class="productView-product"]/h2[@class="productView-brand"]/a//text()'),
            ('description', '//article[@itemprop="description"]//div[@id="Description_Description"]/text()'),
            ('images', ('//ul[@class="productView-thumbnails-dummy"]/li[@class="productView-thumbnail" ]/a/@href', _parser.images)),
            ('price', ('//div[@class="b-product_price js-product_price"]', _parser.prices)),
            ('sizes', ('//div[@class="productView-option-size"]/div[@data-product-attribute="set-select"]', _parser.sizes)),
        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.natori.com/fine-jewelry/fine-jewelry/?page={}',
            ],
            b = [
                'https://www.natori.com/accessories/accessories/bags/?page={}'
            ],
            c = [
                'https://www.natori.com/clothing/ready-to-wear/?page={}',
                'https://www.natori.com/clothing/collections/josie-athleisure/?page={}',
                'https://www.natori.com/footwear/footwear/?page={}',
            ],
            s = [
                'https://us.herno.com/en/women/accessories/shoes/?page={}'
            ]
        ),
        m = dict(
            c = [
                'https://www.natori.com/men/men/?page={}',
            ],
        ),
        u = dict(
            h = [
                'https://www.natori.com/home/bed-bath/?page={}'
            ]
        ),

    )

    countries = dict(
        US=dict(
            currency='USD',
        ),
        GB=dict(
            currency='GBP',
            cookies={
            'GlobalE_Data':'{"countryISO":"GB","currencyCode":"GBP","cultureCode":"en-GB","showPro":null}'
            },
        ),
    )