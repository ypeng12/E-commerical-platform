from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):

    def _parse_multi_items(self, response, item, **kwargs):
        item['color'] = ''
        item['designer'] = 'AURATE'
        variants = response.xpath('//script[@type="application/json"]/text()').extract()

        for v in variants:
            if '"title"' in v:
                script = v
                break
        obj = json.loads(script)

        variants = obj['variants']
        color_varients = set()
        for v in variants:
            color_varients.add(v['option1']+'_'+v['option2'])

        for v in color_varients:
            itm = deepcopy(item)
            sizes = []
            for v2 in variants:
                if v2['available'] != True:
                    continue
                if v == v2['option1']+'_'+v2['option2'] :
                    itm['originsaleprice'] = str(v2['price'])[:-2]
                    itm['originlistprice'] = str(v2['price'])[:-2]
                    itm['sku'] = v2['sku'][:-3]
                    itm['color']= v2['option2']
                    price = v2['price']
                    if v2['option3']:
                        if v2['option3'] not in sizes:
                            sizes.append(v2['option3'])
                    else:
                        sizes = ['IT']
                        v2['option3'] = ''
                    self.prices(price, itm, **kwargs)
                    itm['name'] = v2['name'].replace(v2['option3'],'').replace('/','').strip()


                    
                    itm['images'] = []
                    for images in response.xpath('//div[@class="product-hero__slider"]/div'):
                        # print v2['name'].lower().split('-')[0].split('with')[-1]  
                        text = images.xpath('./@data-product-slide-alt').extract()[0].lower().replace(v2['name'].lower().split('-')[0].split('with')[-1].strip(),'')

                        if v2['option2'].lower()+' gold' in text:
                            itm['images'].append('https:'+images.xpath('./@data-product-slide-zoom').extract()[0])
                    if itm['images'] == []:
                        itm['images'] = item['images'][:5]
                    else:
                        itm['cover'] = item['images'][0]
            # itm['originsizes'] = ';'.join(sizes)
            self.sizes(sizes, itm, **kwargs)
            yield itm



    def _page_num(self, data, **kwargs):
        pages = int(data.strip())
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url  + str(i)
        return url
    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            item['images'].append(img)
        item['cover'] = item['images'][0]


    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if desc.strip() != '':
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.strip()


    def _sizes(self, sizes, item, **kwargs):
        if sizes == []:
            item['originsizes'] = ''
        else:
            item['originsizes'] = sizes


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//li[@class="u-mx-4"][last()]/a/text()').extract_first().strip())*32
        return number

_parser = Parser()



class Config(MerchantConfig):
    merchant = "AUrate"
    name = "aurate"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="u-mx-4"][last()]/a/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//html',
            designer = './/a[@class="brand-name"]/text()',
            link = './/a[contains(@class,"product-")]/@href',
            ),
        product = OrderedDict([
            ('name', '//h1[@class="e-h5 product-hero__title"]/text()'),  
            ('images', ('//div[@class="swiper-wrapper"]/div/img/@data-lazy-src', _parser.images)),
            ('description', ('//div[@class="c-product-specs"]//text()',_parser.description)),

            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(

            a = [
                "https://auratenewyork.com/collections/all?page=",

            ],
        ),
        m = dict(
            s = [
                
            ],

        params = dict(
            # TODO:
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            cookies= {'cart_currency':'USD','GlobalE_Data':'{"countryISO":"US","currencyCode":"USD","cultureCode":"en-GB","showPro":null}'}
            
        ),

        # CN = dict(
        #     language = 'EN', 
        #     currency = 'CNY',
        #     cookies= {'cart_currency':'USD','GlobalE_Data':'{"countryISO":"CN","currencyCode":"CNY","cultureCode":"zh-CHS","showPro":null}'}
            
        # ),
        )

        


