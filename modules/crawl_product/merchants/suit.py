from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json

class Parser(MerchantParser):
    def _checkout(self,res,item,**kwargs):
        if res.extract():
            return True
        else:
            return False

    def _page_num(self,pages,**kwargs):
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=', '?page=%s'%i)
        return url

    def _name(self,res,item,**kwargs):
        name_info = res.extract()
        print(name_info)

    def _description(self,res,item,**kwargs):
        descs = res.extract()
        desc_str = []
        for desc in descs:
            if desc.strip():
                desc_str.append(desc.strip())
        item['description'] = '\n'.join(desc_str)

    def _images(self, images, item, **kwargs):
        images = images.extract()
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append("https:" + img if "https" not in img else img)
        item['images'] = img_li
        item['cover'] = item['images'][0]

    def _prices(self,res,item,**kwargs):
        listprice = res.xpath('./span[@class="money"]/text()').extract_first()
        saleprice = res.xpath('.//span[@class="product-page__current_price "]/span[@class="money"]/text()').extract_first()
        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _sizes(self,res,item,**kwargs):
        sizes_info = json.loads(res.extract_first())
        sizes_li = []
        for size in sizes_info['variants']:
            if size['available']:
                sizes_li.append(size["option1"])
        item["originsizes"] = sizes_li

        sku_json = sizes_info["variants"][0]
        item["sku"] = (sku_json["sku"].split(sku_json["option1"])[0][0:-1]).upper().replace("-","&")
        item["color"] = sku_json["sku"].split("-")[1].upper()

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="gallery"]/div/img/@src').extract()
        images_li = []
        for image in images:
            if image not in images_li:
                images_li.append("https:" + image if "https" not in image else image)
        return images_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(sizes_info['size_info_path'].extract())
        fits = []
        for info in infos:
            if info not in fits:
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "suit"
    merchant = "Suit"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="products-grid"]/@data-max-page',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-card "]',
            designer = './@data-vendor',
            link = './div/a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//span[@class="sold_out"]',_parser.checkout)),
            ('name','//div[@class="product-page__column--top product-page__main-info"]/h1/text()'),
            ('designer','//div[@class="product-page__column--top product-page__main-info"]/h3/a/text()'),
            ('description',('//div[@class="product-page__description"]/text()',_parser.description)),
            ('images',('//div[@class="gallery"]/div/img/@src',_parser.images)),
            ('prices',('//p[@class="product-page__price"]',_parser.prices)),
            ('sizes', ('//div[@class="clearfix product_form init smart-payment-button--false product_form_options product_form-- "]/@data-product | //div[@class="clearfix product_form init smart-payment-button--false  product_form-- "]/@data-product', _parser.sizes))
        ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            image_path = '//div[@class="gallery"]/div/img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//ul[@class="product-page__additional-info"]/li',
            ),
        checknum = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.slamjam.com/en_US/woman/accessories?page="
            ],
            c = [
                "https://row.suitnegozi.com/collections/dress-woman?page=",
            ],
            s = [
                "https://www.slamjam.com/en_US/woman/footwear?page="
            ]
        ),
        m = dict(
            a = [
                "https://www.slamjam.com/en_US/man/accessories?page="
            ],
            c = [
                "https://www.slamjam.com/en_US/man/clothing?page=",
                "https://www.slamjam.com/en_US/man/uniforms?page="
            ],
            s = [
                "https://www.slamjam.com/en_US/man/footwear?page="
            ],
            h = [
                "https://www.slamjam.com/en_US/man/lifestyle?page="
            ]
        )
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,
            country_url = 'en_US',
            ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'en_GB',
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = "A$",
            country_url = 'en_AU',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'en_IT',
        ),
    )