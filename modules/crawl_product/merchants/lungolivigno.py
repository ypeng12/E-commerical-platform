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
        if checkout:
            return False
        else:
            return True
    def _page_num(self, data, **kwargs):
        page_num = 100
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?currPage')[0] + '?currPage=%s'%(i)
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
            if "1_" in img:
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc.strip())

        item['description'] = '\n'.join(desc_li)
        item['color'] = ""
        if "colour" in item['description'].lower():
            item['color'] = item['description'].lower().split("Colour")[-1].split('\n')[0]
        if "manufacture code" in item['description'].lower():
            item['sku'] = item['description'].lower().split("manufacture code:")[-1].split('\n')[0].upper().strip().replace(' ','')

    def _sku(self, sku_data, item, **kwargs):
        for sku in sku_data[1:]:
            if sku.xpath('./strong[contains(text(),"Color:")]'):
                item['color'] = sku.xpath('./text()').extract_first().strip()
            if sku.xpath('./strong[contains(text(),"Product ID:")]'):
                item['sku'] = sku.xpath('./text()').extract_first().strip() +"_" +item["color"]
        item["color"] = item["color"].upper()
        item['designer'] = item['designer'].upper()
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:
            if size.strip() not in item['originsizes']:
                item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('./span[@class="old"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath("./@content").extract()[0]
        except:

            item['originsaleprice'] =prices.xpath("./@content").extract_first()
            item['originlistprice'] =prices.xpath("./@content").extract_first()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="slick-slide slide"]//img/@src').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)

        return images
        



    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace(',','.'))
        size_info = '\n'.join(fits)
        return size_info 

_parser = Parser()



class Config(MerchantConfig):
    name = 'lungolivigno'
    merchant = 'Lungolivigno Fashion'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//ul[@class="page-numbers"]//li[last()-1]//text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@class="product in-stock js-product"]//div[@class="data"]',
            designer = './/span[@class="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//a[@class="add btn js-add-product js-gtm-detail-add-to-cart"]', _parser.checkout)),
            ('name','//h2[@itemprop="name"]/@data-gtm-name'),
            ('designer','//h1[@itemprop="brand"]/@data-gtm-brand'),
            ('images',('//div[@class="slick-slide slide"]//img/@src',_parser.images)),
            ('color','//div[@class="product-swatch-wrap active enabled"]//@data-color-text'), 
            ('sku',('//div[@class="product-single__description rte"]/p',_parser.sku)),
            ('description', ('//div[@id="description-tab"]//text()',_parser.description)),
            ('sizes',('//div[contains(@class,"sizes multi-selections")]//li/label/text()',_parser.sizes)),
            ('prices', ('//span[@itemprop="price"]', _parser.prices)),
            

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
            size_info_path = '//div[@id="description-tab"]//text()',

            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.lungolivignofashion.com/en-US/men/accessories?currPage="
            ],
            b = [
                "https://www.lungolivignofashion.com/en-US/men/bags?currPage="
            ],

            c = [
                "https://www.lungolivignofashion.com/en-US/men/clothing?currPage=",
            ],
            s = [
                "https://www.lungolivignofashion.com/en-US/men/shoes?currPage="
            ],

        ),
        f = dict(
            a = [
                "https://www.lungolivignofashion.com/en-US/women/accessories?currPage="
            ],
            b = [
                "https://www.lungolivignofashion.com/en-US/women/bags?currPage="
            ],

            c = [
                "https://www.lungolivignofashion.com/en-US/women/clothing?currPage=",
            ],
            s = [
                "https://www.lungolivignofashion.com/en-US/women/shoes?currPage="
            ],




        params = dict(
            # TODO:

            ),
        ),

    )


    countries = dict(



        US = dict(
            language = 'EN', 
            currency = 'USD',
            ),

        

        )

        


