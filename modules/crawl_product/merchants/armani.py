from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        name = data.xpath('//span[@class="inner modelName"]//text()|.//h1[@class="item-name"]//span/text()').extract()
        for n in name:
            if n.strip().replace('\n',"").replace("\r","") != "":
                item["name"] = n.strip()
        
        item['sku'] = item['url'].split('_cod')[-1].split('.')[0]
        item['sku'] = item['sku'].upper()
        if 'GIORGIO' in item['url'].upper():
            item['designer'] = "GIORGIO ARMANI"
        else:
            item['designer'] = 'EMPORIO ARMANI'
    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['images'] = []
        cover = None
        for img in images:
            img = img.replace("_14_","_12_")
            item['images'].append(img)
            if '_f.jpg' in img:
                cover = img

        if cover:
            item['cover'] = cover
        else:
            item['cover'] = item['images'][0] if item['images'] else ''

        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        country_url = '_'+item['url'].split('.com/')[-1].split('/')[0].upper() 
        item['originsizes'] = []
        # try:
        #     ajax= 'https://www.armani.com/yTos/api/Plugins/ItemPluginApi/GetCombinationsAsync/?siteCode=ARMANICOM_US&code10='
        #     ajax = ajax.replace('_US',country_url)+item['sku'].upper()
            
        #     result = getwebcontent(ajax)
        #     print(result)
        #     obj = json.loads(result)
        # except: 
        #     item['originsizes'] = ''
        #     item['error'] = 'Out Of Stock'


        result = sizes.xpath("//script[contains(text(),'http://schema.org')]/text()").extract_first()
        obj = json.loads(result)
        
        
        try:
            for color in obj:
                if color['productID'] == item['sku'].upper():
                    item['color'] =  color['description'].upper()
                    sizes = color['offers']
        except:
            item['color'] = ''
        item['originsizes'] = []
        try:

            for size in sizes:
                item['originsizes'].append(str(size['sku'].split("/")[-1]).strip())
        except:
            item['originsizes'] = ''
            item['error'] = 'Out Of Stock'
        item['sku'] = item['sku'][:-2]
        
    def _prices(self, prices, item, **kwargs):
        
        saleprice = prices.xpath('.//div[@class="item-price"]//span[@class="discounted price"]/span[contains(@class, "value")]/text()').extract()
        listprice = prices.xpath('.//div[@class="item-price"]//span[@class="full price"]/span[contains(@class, "value")]/text()').extract()
        if len(saleprice)==0:
            listprice = prices.xpath('.//div[@class="item-price"]//span[@class="price"]/span[contains(@class, "value")]/text()').extract()
            saleprice = listprice

        try:
            item['originsaleprice'] = saleprice[0].strip().replace("\u00A0",'')
            item['originlistprice'] = listprice[0].strip().replace("\u00A0",'')

        except:
                item['originsaleprice'] = ''
                item['originlistprice'] = ''
                item['error'] = 'Out of Stock'
        if item['originlistprice'] == '':
            item['originlistprice'] = ''
            item['originsaleprice'] = ''
            item['error'] = 'Out of Stock'
    def _page_num(self, pages, **kwargs): 
        item_num = pages
        try:
            page_num = int(item_num)/24 + 1
        except:
            page_num =1
        return page_num


    def _parse_item_url(self, response, **kwargs):
        url = response.url
        products = 1
        pages = 999
        for i in range(1, pages):
            if i != 1:
                products = int(response.xpath('//article[contains(@class, "item")]/@data-ytos-track-product-data').extract()[-1].split('{"product_position":')[-1].split(',')[0])
                if (i*999)>products+2:
                    pages = i
                    break
                url = response.url.replace('&page=1','&page='+str(i))
                result = getwebcontent(url)     
                html = etree.HTML(result)
            else:
                html= response

            for quote in html.xpath('//article[contains(@class, "item")]'):
                href = quote.xpath('./a/@href')
                if href is None:
                    continue
                href = quote.xpath('./a/@href').extract()[0]
                designer='GIORGIO ARMANI'
                yield href, designer

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract_first()
        fits = []
        keys = ['Measurements', 'Dimensions', 'Belt width', 'Heel height', 'This design is']
        for key in keys:
            if key in infos:
                info = key + infos.split(key)[-1]
                fits.append(info)
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = "armani"
    merchant = "ARMANI.COM"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="totalResultsCount"]/text()',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            items = '//article[@class="item   "]/article',
            designer = '@data-ytos-track-product-data',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@class="sold-out-message"]/text()', _parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            ('images', ('//ul[@class="alternativeImages"][1]/li/img/@src', _parser.images)),
            ('description', '//div[@class="item-editorial-description"]//span/text()'),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//ul[@class="alternativeImages"][1]/li/img/@src',
            replace = ("_14_","_12_"),
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="item-editorial-description"]/div/span/text()',
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=ccssrs&gender=D&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page="
        ],
            b = [
                "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=llbgs&gender=D&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page=",
            ],
            c = [
                 "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=llprdcts&gender=D&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page=",
            ],
            s = [
                "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=shs&gender=D&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page=",
            ],
        ),
        m = dict(
            a = [
                "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=ccssrs&gender=U&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page="
                ],
            b = [
                "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=llbgs&gender=U&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page=" 
               ],
            c = [
                "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=llprdcts&gender=U&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page="
            ],
            s = [
                "https://www.armani.com/Search/RenderProducts?ytosQuery=true&department=shs&gender=U&site=armanicom&productsPerPage=999&siteCode=ARMANICOM_US&page="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'ARMANICOM_US',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = 'ARMANICOM_US',
            ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = 'ARMANICOM_JP',
            language = 'JP'

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            country_url = 'ARMANICOM_KR',
            language = 'EN'
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            country_url = 'ARMANICOM_SG',
            currency_sign = 'SG$',

        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'ARMANICOM_HK',

        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'ARMANICOM_GB',

        ),

        CA = dict(
            currency = 'CAD',
            currency_sign = 'CAD$',
            country_url = 'ARMANICOM_CA',

        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = "AU$",
            country_url = 'ARMANICOM_AU',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'ARMANICOM_DE',
            thousand_sign =".",

        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = 'ARMANICOM_NO',
            currency_sign = '\u20ac',
            thousand_sign =".",
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            language = 'RU',
            country_url = 'ARMANICOM_RU',
            thousand_sign ="\u00A0",
        ),
        )

        


