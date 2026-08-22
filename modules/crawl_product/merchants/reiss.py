from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract()
        if not checkout:
            return True
        else:
            return False

    def _images(self, images, item, **kwargs):
        image_li = []
        for image in images.extract():
            if image not in image_li:
                image_li.append(image)
        item["images"] = image_li

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath("./span[1]/text()").extract_first()
        saleprice = prices.xpath("./span[2]/text()").extract_first()
        if saleprice is not None:
            item["originsaleprice"] = saleprice.strip().strip("now")
        else:
            item["originsaleprice"] = listprice
        item["originlistprice"] = listprice

    def _sku(self,res,item,**kwargs):
        item["sku"] = res.extract_first()

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first()
        item['designer'] = 'REISS'

    def _color(self,color,item,**kwargs):
        item["color"] = color.xpath('./span[1]/text()').extract_first()
        if not item['color']:
            item['color'] = color.xpath('./h1[1]/text()').extract_first().strip()

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first().strip()

    def _sizes(self,res,item,**kwargs):
        sizes = res.xpath('//span[@class="radio-squared__btn select-size-option"]/span[not(@class="radio-squared__holder  out-of-stock")]/span/text()').extract()
        if sizes == []:
            size_text_li = res.xpath('//select[@id="sylius_cart_item_variant"]//option[not(@selected="selected")]/text()').extract()
            size_text = [size_text for size_text in size_text_li if '(Out of Stock)' not in size_text]
            sizes = []
            for size in size_text:
                if '(Low Stock)' in size:
                    size = size.split('(')[0].strip()
                sizes.append(size)
        item["originsizes"] = [size.strip() for size in sizes]

    def _parse_images(self, response, **kwargs):
        images = response.xpath("//button[@class='product-gallery-nav__item']/img/@src").extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return images_li

    def _list_url(self, i, response_url, **kwargs):
        return response_url

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
    name = "reiss"
    merchant = "Reiss"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a[@class="last"]/text()',
            list_url = _parser.list_url,
            items = '//div[@class="product-list grid--table js-side-drawer-anim no--margin"]//article',
            designer = 'REISS',
            link = './a[@class="subnav__item__link]/@href',
            ),

        product=OrderedDict([
            ('checkout',('//div[@class="grid__item grid-12--small"][1]//span/text()',_parser.checkout)),
            ('sku', ('//div[@class="grid__item grid-6--small grid-6--medium grid-7--large text--right"]/span/span[contains(@itemprop,"product")]/text()', _parser.sku)),
            ('name', ('//div[@class="product__inner container-full--medium-up"]/h2/text()', _parser.name)),
            ('color',('//div[@class="product__inner container-full--medium-up"]',_parser.color)),
            ('description','//div[@id="design"]/div[@class="accordion-body"]/p/text()'),
            ('price', ('//div[@class="product__prices"]', _parser.prices)),
            ('images', ('//button[@class="product-gallery-nav__item"]/img/@src', _parser.images)),
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
            size_info_path = '//div[@id="care"]/div[@class="accordion-body"]/p/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.reiss.com/us/womens/accessories/'
            ],
            c = [
                'https://www.reiss.com/us/womens/all-products/',
            ],
            s = [
                'https://www.reiss.com/us/womens/shoes/'
            ]
        ),
        m = dict(
            a = [
                'https://www.reiss.com/us/mens/accessories/'
            ],
            c = [
                'https://www.reiss.com/us/mens/all-products/',
            ],
            s = [
                'https://www.reiss.com/us/mens/shoes/'
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )