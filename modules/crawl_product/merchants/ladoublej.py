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
        num_data = data.strip().split("of")[-1].strip()
        count = int(num_data)
        page_num = count / 20 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = i
        url = response_url.split('?')[0] + '?page=%s'%num
        return url

    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = sku_data.extract_first().upper()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)
        item['images'] = images
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.xpath('//div[@class="b-variation"]//li[@id="'+item["sku"]+'"]//a[@class="js-swatchanchor js-togglerhover b-swatches_size-link  "]/@title').extract()
        if not sizes:
            sizes = ['IT']
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())
        
    def _prices(self, res, item, **kwargs):
        tmp_data = json.loads(res.extract_first().split('app.trackerData = ')[1].split('app.trackerData.userInfo')[0].strip().rsplit(';')[0])
        item['originlistprice'] = tmp_data['productPrice']
        item['originsaleprice'] = tmp_data['productPrice']

    def _color(self, color, item, **kwargs):
        color = color.extract_first().upper().strip().replace("\n",'')
        item['color'] = color
        item['designer'] = 'LA DOUBLEJ'

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//img[contains(@class,"js-producttile_image")]/@data-src').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'measurement' in info.lower() or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()



class Config(MerchantConfig):
    name = 'ladoublej'
    merchant = 'La DoubleJ'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[contains(@class,"l-search_result-paging-controls-loaded"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//a[contains(@class,"js-producttile_link")]',
            designer = './/html',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@title="Add to bag"]', _parser.checkout)),
            ('images',('//img[contains(@class,"js-producttile_image")]/@data-src',_parser.images)), 
            ('sku',('//div[@class="js-product_number h-hidden"]/span/text()',_parser.sku)),
            ('name', '//span[@class="b-product_name"]/text()'),
            ('color',('//li[contains(@class,"js-swatches_color-item-selected")]/a/@title',_parser.color)),
            ('description', ('//div[@class="b-product_tabs js-product_tabs"]/div/div//text()',_parser.description)),
            ('prices', ('//script[@class="js-gtm-do_not_wrap"][contains(text(),"var app = app || ")]/text()', _parser.prices)),
            ('sizes',('//html',_parser.sizes)),
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
            size_info_path = '//div[@class="b-product_fit_information"]//li/text()',
            ),
        )

    list_urls = dict(
        m = dict(


        ),
        f = dict(
            a = [
                'https://www.ladoublej.com/default/ldj-editions/accessories/',
                "https://www.ladoublej.com/default/ldj-editions-accessories-jewelry/",
            ],
            b = [
                "https://www.ladoublej.com/default/ldj-editions/accessories/bags/",
            ],
            c = [
            	"https://www.ladoublej.com/default/ldj-editions/clothing/dresses/?page=3",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/shirts-and-tops/?page=1",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/shorts-and-pants/",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/knitwear/",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/swimwear/",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/activewear/",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/coats/",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/pajamas/",
            	"https://www.ladoublej.com/default/ldj-editions/clothing/goddess-collection/"
            ],
            s = [
            	"https://www.ladoublej.com/default/ldj-editions/shoes/",
            ],
            e = [
            	"https://www.ladoublej.com/default/acqua-di-parma/"
            ],



        params = dict(
            page = 1,
            ),
        ),

    )


    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {
                'countrySelected':'true',
                'preferredCountry':'US',
                'preferredLanguage':'en'
            }
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = {
                'countrySelected':'true',
                'preferredCountry':'GB',
                'preferredLanguage':'en'
            }

        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {
                'countrySelected':'true',
                'preferredCountry':'DE',
                'preferredLanguage':'en'
            },

        )
#      
        )

        


