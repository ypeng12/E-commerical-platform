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
        data = json.loads(checkout.xpath('//script[@type="application/ld+json"]/text()').extract_first()) if checkout.extract_first() else None
        soldout = checkout.xpath('//span[@class="headline-5 pr1-sm"]/text()').extract_first()
        if soldout and 'sold out' in soldout.lower():
            return True
        if data and 'offers' in data and 'availability' in data['offers'] and 'instock' in data['offers']['availability'].lower():
            item['tmp'] = data
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = data.split('totalPages')[-1].split(':',1)[-1].split(',')[0]
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=1','?page=%s'%i)
        return url

    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = sku_data.extract_first().split('Style:')[-1].replace('-','_').strip().upper()

    def _name(self, data, item, **kwargs):
        item['name'] = item['tmp']['name'].strip()
        item['designer'] = item['tmp']['brand']['name'].strip().upper()

    def _description(self, description, item, **kwargs):
        descs = description.extract() 
        desc_li = []
        for desc in descs:
            if not desc.strip():
                continue
            if 'Shown:' in desc:
                item['color'] = desc.split('Shown:')[-1].strip()
            desc_li.append(desc.strip())
        item['description'] = '\n'.join(desc_li)

    def _prices(self, prices, item, **kwargs):
        # item['originlistprice'] = item['tmp']['offers']['highPrice']
        # item['originsaleprice'] = item['tmp']['offers']['lowPrice']
        listprice = prices.xpath('.//div[@data-test="product-price"]/text()').extract_first()
        saleprice = prices.xpath('.//div[@data-test="product-price-reduced"]/text()').extract_first()
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice if saleprice else listprice

    def _sizes(self, sizes_data, item, **kwargs):
        osizes = []
        size_data = json.loads(sizes_data.extract_first().split('INITIAL_REDUX_STATE=')[-1].rsplit(';',1)[0].strip())
        products = size_data['Threads']['products']
        for key,value in list(products.items()):
            if key.replace('-','_') == item['sku']:
                break
        avail_skus = []
        for avail in value['availableSkus']:
            avail_skus.append(avail['id'])

        for sku in value['skus']:
            if sku['skuId'] in avail_skus:
                osizes.append(sku['nikeSize']) #sku['localizedSize']
        item['originsizes'] = osizes
        item['tmp'] = value
        if 'sku' in kwargs and kwargs['sku'] != item['sku']:
            item['originsizes'] = []
            item['sku'] = kwargs['sku']

    def _images(self, images, item, **kwargs):
        item['images'] = []
        for node in item['tmp']['nodes'][0]['nodes']:
            if node['subType'] == 'image':
                image = node['properties']['squarishURL']
                item['images'].append(image)

        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        images = []
        script = response.xpath('//script[contains(text(),"INITIAL_REDUX_STATE=")]/text()').extract_first()
        data = json.loads(script.split('INITIAL_REDUX_STATE=')[-1].rsplit(';',1)[0].strip())

        products = data['Threads']['products']
        for key,value in list(products.items()):
            if key.replace('-','_') == kwargs['sku']:
                break

        for node in value['nodes'][0]['nodes']:
            if node['subType'] == 'image':
                image = node['properties']['squarishURL']
                images.append(image)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//script[contains(text(),"totalPages")]/text()').extract_first().strip().split('totalResources')[-1].split(':',1)[-1].split(',')[0])
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        size_data = json.loads(response.xpath(size_info['size_info_path']).extract_first().split('INITIAL_REDUX_STATE=')[-1].rsplit(';',1)[0].strip())
        sku = (response.meta['sku'].replace('_','-'))
        products = size_data['Threads']['products']
        infos = products[sku]['description']
        html = etree.HTML(infos)
        infos = (html.xpath('//text()'))
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or '" H"' in info or '" W"' in info or '" D' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = 'nike'
    merchant = "Nike"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//main/section/div/div',
            designer = './div/a/@data-brand',
            link = './/a[@class="product-card__link-overlay"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//li[contains(text(),"Style:")]/text()',_parser.sku)),
            ('name', ('//span[@class="prod-name"]/text()',_parser.name)),
            ('description', ('//*[contains(@class,"description-preview")]//text()',_parser.description)),
            ('prices', ('//div[contains(@class,"product-price__wrapper css")]', _parser.prices)),
            ('sizes', ('//script[contains(text(),"INITIAL_REDUX_STATE=")]/text()', _parser.sizes)),
            ('images', ('//html', _parser.images)),
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
            size_info_path = '//script[contains(text(),"INITIAL_REDUX_STATE=")]/text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.nike.com/w/watches-2axv8'
                'https://www.nike.com/w/womens-hats-visors-headbands-52r49z5e1x6'
            ],
            b = [
                'https://www.nike.com/w/womens-bags-backpacks-5e1x6z9xy71'
            ],
            c = [
                'https://www.nike.com/w/womens-clothing-5e1x6z6ymx6'
            ],
            s = [
                'https://www.nike.com/w/womens-shoes-5e1x6zy7ok'
            ],
        ),
        m = dict(
            a = [
                'https://www.nike.com/w/watches-2axv8',
                'https://www.nike.com/w/mens-hats-visors-headbands-52r49znik1'
            ],
            b = [
                'https://www.nike.com/w/mens-bags-backpacks-9xy71znik1'
            ],
            c = [
                'https://www.nike.com/w/mens-clothing-6ymx6znik1'
            ],
            s = [
                'https://www.nike.com/w/mens-shoes-nik1zy7ok'
            ],
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        )
    )


