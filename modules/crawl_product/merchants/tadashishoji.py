from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
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
        num_data = data.lower().strip()
        count = int(num_data)
        page_num = count 
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = i
        url = urljoin(response_url.split('?')[0], '?p=%s'%num)
        return url



    def _parse_json(self, obj, item, **kwargs):
        item['tmp'] = obj
          
    def _parse_multi_items(self, response, item, **kwargs):
        item["designer"] = "TADASHI SHOJI"
        scripts = response.xpath('//script[@type="text/javascript"]').extract()
        color_ids = ''
        for script in scripts:
            if 'ConfigDefaultText' in script:
                color_ids = script
                break
        obj = json.loads(color_ids.split('ConfigDefaultText(')[-1].split('});')[0].strip()+"}")
        colors = obj['attributes']["92"]["options"]
        for color in colors:
            item_color = deepcopy(item)
            item_color['color'] = color['label'].upper()
            color_id = color['id']
            code = obj['productId']
            item_color['sku'] = code + '_'+item_color['color']
            sizes = color["products"]
            size_codes = obj['attributes']["179"]["options"]

            osizes = []
            for size in size_codes:
                s_code = size['id']
                if color_id+","+s_code in obj["quantities"]:
                    osizes.append(size["label"])


            item_color['originsizes'] = osizes if osizes else ['IT']
            self.sizes(obj, item_color, **kwargs)

            

        #    
            item_color['originlistprice'] = obj["oldPrice"]
            item_color['originsaleprice'] = obj["basePrice"]

            self.prices(obj, item_color, **kwargs)
            if len(colors)>1:
                code = color['image'].split('/')[-1].split("SWATCH")[0].split('_')[-1].replace("_",'').lower()

                item_color["images"] = []
                for img in item["images"]:
                    imgcolor = item["images"][0].split("_front")[0].split("_")[-1].replace("_",'').lower()
                    if item_color['color'].lower().split('/')[0] not in img:
                        item_color["images"].append(img.replace(imgcolor,code).replace("__","_").replace('_2',''))
            else:
                item_color["images"] =  item["images"]



            item_color['cover'] = item_color['images'][0]
            yield item_color







    def _images(self, images, item, **kwargs):

        imgs = images.extract()
        images = []
        for img in imgs:
            if img not in images and 'placeholder' not in img.lower():
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
            desc_li.append(desc.strip())

        item['description'] = '\n'.join(desc_li)

        item['description'] = item['description'].split("Our Customer Care")[0].split("For Assistance")[0].split("Hemming")[0]

        



    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="mobileProductGallery"]//img/@src').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
        

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="total-pages"]//a[@class="last"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))*12
        return number



_parser = Parser()



class Config(MerchantConfig):
    name = 'tadashishoji'
    merchant = 'Tadashi Shoji'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="total-pages"]//a[@class="last"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ma-box-content"]',
            designer = './div[@class="designer-name"]/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="add-to-cart"]', _parser.checkout)),
            ('images', ('//div[@id="mobileProductGallery"]//img/@src', _parser.images)),
            ('description', ('//dd[contains(@class,"accordion-content")]/div//text()',_parser.description)),
            # ('name', '//h1[@data-auto="product-name"]/text()'),
            # ('designer', '//a[@data-auto="product-brand"]/text()'),
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



    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        m = dict(

        ),
        f = dict(

            b= [
                'https://www.tadashishoji.com/shop/accessories'
            ],
            c = [
                'https://www.tadashishoji.com/bridal/bride?p=1',
                "https://www.tadashishoji.com/shop/dresses?p=1",
                "https://www.tadashishoji.com/shop/separates?p=1",
                "https://www.tadashishoji.com/shop/shapewear?p=1",
                "https://www.tadashishoji.com/shop/intimates?p=1",
                "https://www.tadashishoji.com/shop/wedding?p=1"

            ],


            e = [
                "https://www.tadashishoji.com/shop/fragrance?p=1"
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
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            cur_rate = 1,   # TODO
            
            ),

#ships only in US
#      
        )

        


