from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract_first()
        if "In stock" in checkout:
            return False
        else:
            return True

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract_first()
        listprice = prices.xpath('.//span[@data-price-type="oldPrice"]/span/text()').extract_first()
        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in images.extract():
            if image not in image_li:
                image_li.append(image)
        item["images"] = image_li

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first().strip()
        item['designer'] = 'GENNY'

    def _sizes(self,res,item,**kwargs):
    	size_num = json.loads(res.xpath('//script[contains(text(),"spConfig")]/text()').extract_first())
    	size_check = json.loads(res.xpath('//script[contains(text(),"mgsAjaxCartStockOption")]/text()').extract_first())
    	checks = size_check["*"]["mgsAjaxCartStockOption"]
    	size_nums = size_num['#product_addtocart_form']['configurable']['spConfig']['attributes']['171']['options']
    	sizes_li = []
    	sizes = []
    	for size in checks:
    		if checks[size]["is_in_stock"] == '1':
    			sizes_li.append(size)
    	for num in size_nums:
    		if num['products']:
    			if num['products'][0] in sizes_li:
    				sizes.append(num['label'])
    	item['originsizes'] = sizes

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@id="owl-carousel-gallery"]//div/@data-zoom').extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return image_li
    
    def _page_num(self, data, **kwargs):
    	data = data.extract()[-1]
    	return int(4)

    def _list_url(self, i, response_url, **kwargs):
    	return response_url + '{}'.format(i)

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
    name = "genny"
    merchant = "GENNY"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//ul[@aria-labelledby="paging-label"]/li//text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="products list items product-items"]/li//div[@class="product-top"]',
            designer = 'GENNY',
            link = './a[@class="full-link"]/@href',
            ),
        product=OrderedDict([
            ('checkout',('//div[@class="stock available"]/span/text()',_parser.checkout)),
            ('sku','//div[@class="product attribute sku"]/div[@itemprop="sku"]/text()'),
            ('name','//h1[@class="page-title "]/span/text()'),
            ('color',('//div[@class="product__inner container-full--medium-up"]',_parser.color)),
            ('description',('//div[@class="item content active"]/text()',_parser.description)),
            ('price', ('//span[@class="price-container "]', _parser.prices)),
            ('images', ('//div[@id="owl-carousel-gallery"]//div/@data-zoom', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="item content"]/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.genny.com/wd_en/accessories/borse.html?p=',
                'https://www.genny.com/wd_en/accessories/bijoux.html?p=',
                'https://www.genny.com/wd_en/accessories/gloves.html?p=',
                'https://www.genny.com/wd_en/accessories/sunglasses.html?p=',
            ],
            c = [
                'https://www.genny.com/wd_en/ready-to-wear/dresses.html?p=',
                'https://www.genny.com/wd_en/ready-to-wear/tops-knitwear.html?p=',
                'https://www.genny.com/wd_en/ready-to-wear/trousers.html?p=',
                'https://www.genny.com/wd_en/ready-to-wear/outerwear.html?p=',
                'https://www.genny.com/wd_en/ready-to-wear/beachwear.html?p=',
            ],
            s = [
                'https://www.genny.com/wd_en/accessories/shoes.html?p='
            ]
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )