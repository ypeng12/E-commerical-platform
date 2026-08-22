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
        page_num = data.split(' ')[0]
        return int(page_num)/24 +1

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=1','?page=%s'%i)
        return url

    def _color(self, data, item, **kwargs):
        color = item['url'].split('?color=')[-1].strip()
        item['color'] = color.replace('%20',' ').replace('%2f','/').upper()

    def _sku(self, sku_data, item, **kwargs):
         sku = sku_data.extract_first().strip().rsplit('-',1)[0]
         item['sku'] = sku + '_' + item['color']

    def _designer(self, designer_data, item, **kwargs):
        item['designer'] = designer_data.extract_first().upper().strip()
          
    def _images(self, images, item, **kwargs):
        item['images'] = []
        color = item['color'].lower().replace(' / ','___').replace(' ','_')
        imgs = images.extract()
        for img in imgs:
            if color not in img:
                continue
            image = 'https://www.nancymeyer.com' + img.split("('")[-1].split("',")[0]
            if image not in item['images']:
                item['images'].append(image)
        
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.replace('Description\n','')

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        sizes = sizes_data.extract()
        if len(sizes) > 0:
            for size in sizes[1:]:
                item['originsizes'].append(size.strip().upper())

    def _prices(self, prices, item, **kwargs):
        regularprice = prices.xpath('.//span[@class="ListPricewSale"]/text()').extract()
        salePrice = prices.xpath('.//span[@class="SalePrice"]/text()').extract()
        if len(regularprice) == 0:
            salePrice = prices.xpath('.//span[@class="ListPricewoSale"]/text()').extract()
            item['originlistprice'] = salePrice[0].strip().upper().replace('SALE:','').strip()
            item['originsaleprice'] = item['originlistprice']
        else:
            item['originlistprice'] = regularprice[0].strip().upper().replace('SALE:','').strip()
            item['originsaleprice'] = salePrice[0].strip().upper().replace('SALE:','').strip()

    def _parse_images(self, response, **kwargs):
        images = []
        color = kwargs['sku'].split('_')[-1]
        split_color = '"name":"Color","values":{"type":"json","json":["%s"]'%color
        scripts = response.xpath('//script').extract()
        img_script = ''
        for script in scripts:
            if 'name":"Color","values":{"type":"json","json' in script:
                img_script = script
                break
        img_list = eval(img_script.split(split_color)[0].split('images":')[-1].split(',"__typename')[0].replace('false', '"false"'))
        imgs = []
        for img in img_list[:-1]:
            img = 'https://nancymeyer.vtexassets.com/arquivos/ids/%s-800-auto?width=800&height=auto&aspect=true'%img['id'].split('Image:')[-1]
            imgs.append(img)

        if split_color not in img_script:
            imgs = []
        return imgs
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[contains(@class,"totalProducts--")]/span/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'nancy'
    merchant = "Nancy Meyer"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[contains(@class,"totalProducts--")]/span/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//a[@rapt="SearchProduct"]',
            designer = './div/a/@data-brand',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@id="ctl00_ctl00_mainSiteContent_MainContent_ProductView_FormView1_AddToCart"]', _parser.checkout)),
            ('color',('//option[@selected="selected"]/@value', _parser.color)),
            ('sku', ('//div[@class="ProductStyle"]/text()',_parser.sku)),
            ('name', '//span[@class="prod-name"]/text()'),    # TODO: path & function
            ('designer', ('//span[@class="prod-brand"]/text()', _parser.designer)),
            ('images', ('//div[@id="AltCarousel"]//ul//li//a/@onclick', _parser.images)),
            ('description', ('//span[@id="PPdetail"]/span//div/text()',_parser.description)), # TODO:
            ('sizes', ('//select[@id="ctl00_ctl00_mainSiteContent_MainContent_ProductView_FormView1_MultiSelectSkuSelector1_skupicker_ctl00_AttributeSelector"]//@value', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(

        ),
        f = dict(

            c = [
                'https://www.nancymeyer.com/Bras/search?page=1',
                "https://www.nancymeyer.com/Panties/search?page=1",
                "https://www.nancymeyer.com/Lingerie/search?page=1",
                "https://www.nancymeyer.com/Sleep-and-Loungewear/search?page=1",
                "https://www.nancymeyer.com/Hosiery/search?page=1",
                "https://www.nancymeyer.com/Activewear/search?page=1",
                "https://www.nancymeyer.com/Swimwear/search?page=1",
                "https://www.nancymeyer.com/Gifts/search?page=1",
                "https://www.nancymeyer.com/apparel/search?page=1",
                "https://www.nancymeyer.com/Sale/search?suppress=true?page=1"
            ],



        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),
        )

        


