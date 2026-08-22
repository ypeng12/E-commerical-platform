from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json

class Parser(MerchantParser):
    def _checkout(self,res,item,**kwargs):
        checkout = res.extract()
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = 200
        return int(5)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + str(i)
        return url

    def _sku(self,res,item,**kwargs):
        sku = res.xpath('//script[@type="application/json"][contains(text(),"product")]/text()').extract_first()
        item['tmp'] = json.loads(sku)['product']
        item['color'] = item['tmp']['variants'][0]['option1'].upper()
        if item['tmp']['variants'][0]['option3']:
            item['sku'] = item['tmp']['variants'][0]['option3'] + "_" + item['color'].upper()
        else:
            item['sku'] = item['tmp']['variants'][0]['sku'].split(item['color'][0:4])[0]+'_'+item['color'].upper()
        item['name'] = item['tmp']['title']
        item['designer'] = 'DIANE VON FURSTENBERG'
        item['description'] = re.findall(r'<p>([\s\S]+?)</p>',item['tmp']['description'])[0]

    def _sizes(self,res,item,**kwargs):
        sizes_li = []
        sizes_json = item['tmp']['variants']
        for sizes in sizes_json:
            if sizes['available'] and sizes['option2']:
                if sizes['option3'] in item['sku']:
                    sizes_li.append(sizes['option2'])
            else:
                sizes_li = ['IT']
        item["originsizes"] = sizes_li

        item['images'] = ["https:" + images for images in item['tmp']['images']]
        item['cover'] = item['images'][0]
        listprice = str(item['tmp']['compare_at_price_max'])
        saleprice = str(item['tmp']['price_min'])
        item['originlistprice'] = str(float(listprice[0:-2] + '.' + listprice[-2:]))
        item['originsaleprice'] = str(float(saleprice[0:-2] + '.' + saleprice[-2:]))
        
    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="Product__Wrapper"]//div[@class="AspectRatio AspectRatio--withFallback"]/img/@data-original-src').extract()
        images_li = []
        for image in results["images"]:
            if "https" not in image:
                img = "https:" + image
                images_li.append(img)
        return images_li

_parser = Parser()


class Config(MerchantConfig):
    name = "dvf"
    merchant = "Diane von Furstenberg"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = '//meta[@property="og:site_name"]/@content',
            link = './a/@href',
            ),
        product=OrderedDict([
            ('checkout',('//*[@data-action="add-to-cart"]//text()',_parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            ('sizes', ('//html', _parser.sizes)),
            ]),
        image=dict(
            method=_parser.parse_images,
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="productCutline"]/div[1]//text()',            
            ),
        checknum = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.dvf.com/collections/face-masks?page='
            ],
            b = [
            ],
            c = [
                'https://www.dvf.com/collections/all-dresses?page=',
                'https://www.dvf.com/collections/all-wraps?page=',
            ],
            s = [
            ],
        ),
        u = dict(
            h = [
                'https://www.dvf.com/collections/books?page='
            ]
        ),
    )

    countries = dict(
        US=dict(
            currency = 'US',
        ),
    )