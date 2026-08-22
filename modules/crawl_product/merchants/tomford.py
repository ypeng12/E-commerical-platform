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
        if checkout:
            return False
        else:
            return True
        
    def _page_num(self, data, **kwargs):
        page_num = data.split()[-1].strip()
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*12
        url = response_url.replace('10000', '%s'%num)
        return url

    def _color(self, data, item, **kwargs):
        item['color'] = data.extract_first().strip().upper().replace(' ', '')

    def _sku(self, sku_data, item, **kwargs):
        link = sku_data.extract_first()
        if link and '_OS_A' in link:
            item['sku'] = link.split('/')[-1].split('_OS_A')[0]
        else:
            item['sku'] = ''

    def _designer(self, designer_data, item, **kwargs):
        item['designer'] = 'TOM FORD'
          
    def _images(self, images, item, **kwargs):
        item['images'] = []
        imgs = images.extract()
        for img in imgs:
            image = img.split('?')[0] + '?$pdp_hero_dsk$&bg=rgb(255,255,255)'
            item['images'].append(image)
        
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.xpath('.//ul/li/text()').extract() + description.xpath('./text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []        
        sizes = sizes_data.extract()
        if len(sizes) > 0:
            for size in sizes:
                item['originsizes'].append(size.replace('%2e','.').strip())
        elif item['category'] in ['a', 'b', 'e']:
            if not item['originsizes']:
                item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        regularprice = prices.extract()
        item['originlistprice'] = regularprice[0].strip()
        item['originsaleprice'] = item['originlistprice']

    def _parse_images(self, response, **kwargs):
        images = []
        imgs = response.xpath('//ul[@id="thumbnails"]/li//img/@src').extract()
        for img in imgs:
            image = img.split('?')[0] + '?$pdp_hero_dsk$&bg=rgb(255,255,255)'
            images.append(image) 
        return images  

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path'])
        swatches = []
        for data in datas:
            pid = data.xpath("./@href").extract()[0].split('pid=')[-1].split('&')[0]+data.xpath("./@title").extract()[0].upper().strip()
            if 'NOT AVAILABLE' in pid:
                pid = data.xpath("./@href").extract()[0].split('pid=')[-1].split('&')[0]+data.xpath("./@title").extract()[0].upper().split('COLOR')[-1].split('IS NOT AVAILABLE')[0].strip()
            swatch = pid.replace(' ','')
            swatches.append(swatch)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = 'tomford'
    merchant = 'TOM FORD'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="paging-current-page"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@class="grid-tile"]',
            designer = './div/a/@data-brand',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add-to-cart"]', _parser.checkout)),
            ('color',('//div[contains(@class,"attribute color")]//span[@itemprop="color"]/text()', _parser.color)),
            ('sku', ('//meta[@property="og:image"]/@content',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),    # TODO: path & function
            ('designer', ('//html', _parser.designer)),
            ('images', ('//ul[@id="thumbnails"]/li//img/@src', _parser.images)),
            ('description', ('//div[@class="panel-body"]',_parser.description)), # TODO:
            ('sizes', ('//select[@class="variation-select input-select pdp-size-select"]/option[@data-btclass=""]/text()', _parser.sizes)),
            ('prices', ('//span[@itemprop="price"]/text()', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//ul[contains(@class,"swatches Color")]/li/a',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="panel-body"]/ul/li/text()',
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.tomford.com/men/accessories/?sz=12&start=10000',
                'https://www.tomford.com/men/eyewear/?sz=12&start=10000'
            ],
            b = [
                'https://www.tomford.com/men/bags/?sz=12&start=10000'
            ],
            c = [
                'https://www.tomford.com/men/ready-to-wear/?sz=12&start=10000'
            ],
            s = [
                'https://www.tomford.com/men/shoes/?sz=12&start=10000'
            ],
            e = [
                "https://www.tomford.com/beauty/men/?sz=12&start=10000"
            ],
        ),
        f = dict(
            a = [
                'https://www.tomford.com/women/accessories/?sz=12&start=10000',
                'https://www.tomford.com/women/eyewear/?sz=12&start=10000'
            ],
            b = [
                'https://www.tomford.com/women/handbags/?sz=12&start=10000'
            ],
            c = [
                'https://www.tomford.com/women/ready-to-wear/?sz=12&start=10000'
            ],
            s = [
                'https://www.tomford.com/women/shoes/?sz=12&start=10000'
            ],
            e = [
                "https://www.tomford.com/beauty/fragrance/?sz=12&start=10000",
                "https://www.tomford.com/beauty/lips/?sz=12&start=10000",
                "https://www.tomford.com/beauty/face/?sz=12&start=10000",
                "https://www.tomford.com/beauty/eyes/?sz=12&start=10000"
            ],

        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
                language = 'EN',
                currency = 'USD',
            ),
        )

        


