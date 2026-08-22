from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests


class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = int(data.split(' ')[0]) / 60 + 1
        return pages

    def _sku(self, data, item, **kwargs):
        sku = data.extract_first()
        sku = re.findall(r'\d+', sku)[0]
        item['sku'] = sku

    def _designer(self, data, item, **kwargs):
        designer = data.xpath('.//h2[@class="designer-name"]/a/text()').extract_first()
        # if not designer:
        #     designer = data.xpath('.//meta[@property="og:title"]/@content')
        item['designer'] = designer

    def _images(self, res, item, **kwargs):
        imgs = res.xpath('.//div[@class="thumb-frame"]/a/img/@src').extract()
        # cover = res.xpath('.//a[@class="cloud-zoom"]/img/@src').extract_first()
        # print(cover)
        # cover_base = cover.split('/')[-1]
        img_li = []
        for img in imgs:
            if img not in img_li:
                img_li.append(img)
        item['cover'] = img_li[0]
        item['images'] = img_li

    def _color(self, res, item, **kwargs):
        categ = res.xpath('.//div[@itemprop="breadcrumb"]/a[4]/text()').extract_first()
        color_data = res.xpath('.//div[@itemprop="breadcrumb"]/span/text()').extract_first()
        # color = color_data.split('-')[-1].split('"')[0] if color_data else ''
        color_f = color_data.split(categ[0:3])[0]
        if categ == 'Shoes':
            color = color_f.rsplit(" ")[-1]
        else:
            color = color_f.rsplit(" ")[-2]
        item["color"] = color.strip().upper() if color else ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, data, item, **kwargs):
        sizes = data.xpath('.//a[@class="variant-link"]/div')
        size_li = []
        if sizes:
            for siz in sizes:
                size_note = siz.xpath('./@class').extract_first()
                if 'unavailable' in size_note:
                    continue
                size = siz.xpath('./text()').extract_first().strip()
                size_li.append(size)
        else:
            sizes = data.xpath('.//select[@name="variants"]/option')
            for size in sizes:
                if size.xpath('./text()').extract_first() == 'Select size':
                    continue
                size_url = 'https://www.wolfandbadger.com' + size.xpath('./@value').extract_first()
                data = requests.get(size_url)
                size_status = etree.HTML(data.text).xpath('.//span[@class="low-stock-notice"]/text()')
                size_status = size_status[0] if size_status else ''
                if 'out of stock' in size_status:
                    continue
                size = etree.HTML(data.text).xpath('.//option[@selected="selected"]/text()')[0].strip()
                size_li.append(size)

        if item['category'] in ['a', 'b', 'e']:
            if not size_li:
                size_li = ['IT']
                
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):

        salePrice = prices.xpath('.//meta[@itemprop="price"]/@content').extract_first()
        listPrice = prices.xpath('.//strike/text()').extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else ''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="thumb-frame"]/a/img/@src').extract()
        cover = response.xpath('//a[@id="zoom1"]/img/@src').extract_first()
        cover_base = cover.split('/')[-1]
        img_li = []
        for img in imgs:
            img = cover.replace(cover_base, img.split('/')[-1])
            if img not in img_li:
                img_li.append(img)
        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and (
                    'model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower() or 'inches' in info.lower() or '"' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(
            response.xpath('//div[@class="productcount"]/text()').extract_first().lower().strip().split('item')[
                0].strip())
        return number


_parser = Parser()


class Config(MerchantConfig):
    name = 'wolf'
    merchant = 'Wolf & Badger'
    # url_split = False

    path = dict(
        base=dict(
        ),
        plist=dict(
            page_num=('//div[@class="productcount"]/text()', _parser.page_num),
            # list_url = _parser.list_url,
            # parse_item_url = _parser.parse_item_url,
            items='//div[@class="product-summary"]',
            designer='.//span[@class="designer-name-link"]/text()',
            link='./div[1]/a/@href',
        ),
        product=OrderedDict([
            ('checkout', ('//input[@value="Add to Bag"]', _parser.checkout)),
            ('sku', ('//script[@id="ometria-javascript-api-integration"]/@data-ometria-page-data', _parser.sku)),
            ('name', '//h1[@class="product-name"]/text()'),  # TODO: path & function
            ('designer', ('//html', _parser.designer)),
            ('images', ('//html', _parser.images)),
            ('color', ('//html', _parser.color)),
            ('description', ('//div[@id="notesPanel"]/div/text()', _parser.description)),  # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
        ]),
        look=dict(
        ),
        swatch=dict(
        ),
        image=dict(
            method=_parser.parse_images,
            # image_path = '//div[@class="thumb-frame"]/a/img/@src',
            # replace = ('125', '600'),
        ),
        size_info=dict(
            method=_parser.parse_size_info,
            size_info_path='//div[@id="sizePanel"]/div/text()',
        ),
        checknum=dict(
            method=_parser._parse_checknum,
        ),
    )

    list_urls = dict(
        m=dict(
            a=[
                "https://www.wolfandbadger.com/us/category/men/jewellery/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/belts/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/gloves/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/hats/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/handkerchiefs-pocket-squares/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/scarves/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/socks/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/sunglasses/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/ties-bowties/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/umbrellas/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/wallets/?p=",
                "https://www.wolfandbadger.com/us/category/men/accessories/watches/?p=",
            ],
            b=[
                "https://www.wolfandbadger.com/us/category/men/accessories/bags/?p=",
            ],
            c=[
                "https://www.wolfandbadger.com/us/category/men/clothing/?p=",
            ],
            s=[
                "https://www.wolfandbadger.com/us/category/men/accessories/shoes/?p="
            ],
        ),
        f=dict(
            a=[
                "https://www.wolfandbadger.com/us/category/women/accessories/belts/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/gloves/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/hair-accessories/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/hats/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/scarves/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/socks/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/sunglasses/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/technology/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/wallets/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/watches/?p=",
                "https://www.wolfandbadger.com/us/category/women/accessories/umbrellas/?p=",
                "https://www.wolfandbadger.com/us/category/women/jewellery/?p="
            ],
            b=[
                'https://www.wolfandbadger.com/us/category/women/accessories/bags/?p=',
            ],
            c=[
                'https://www.wolfandbadger.com/us/category/women/clothing/?p=',
            ],
            s=[
                'https://www.wolfandbadger.com/us/category/women/accessories/shoes/?p=',
            ],
            e=[
                'https://www.wolfandbadger.com/us/category/beauty/beauty/?p=',
                'https://www.wolfandbadger.com/us/category/beauty/grooming/?p=',
            ],

            params=dict(
                # TODO:
                page=1,
            ),
        ),

        country_url_base='/us/',
    )

    countries = dict(
        US=dict(
            language='EN',
            currency='USD',
            currency_sign='$',
            country_url='/us/',
        ),

        CN=dict(
            currency='CNY',
            discurrency='USD',
        ),

        KR=dict(
            currency='KRW',
            discurrency='USD',
        ),
        GB=dict(
            currency='GBP',
            currency_sign='\xa3',
            country_url='/uk/',
        ),
        AU=dict(
            currency='AUD',
            currency_sign='A$',
            country_url='/au/',
        ),
        DE=dict(
            currency='EUR',
            currency_sign='\xa3',
            country_url='/uk/',
            discurrency='GBP',
        ),

    )

