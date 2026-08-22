from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = json.loads(checkout.extract_first())
        if checkout['event_config']['product_add_to_cart']:
            return False
        else:
            return True

    def color(self, res, item, **kwargs):
        color_json = res.extract_first().strip()
        item['color'] = re.search(r'Color: "(.*?)"',color_json,re.M).group(1)
        desc = re.search(r'Description: "(.*?)"',color_json,re.M).group(1)
        item['description'] = desc.replace('\\n','\n').strip()

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('//span[@class="price"]/text()').extract_first()
        listprice = prices.xpath('//span[@class="list_price"]/text()').extract_first()
        item["originsaleprice"] = saleprice
        item["originlistprice"] = listprice if listprice else saleprice

    def _images(self, images, item, **kwargs):
        images_json = json.loads(images.extract_first())
        image_li = []
        for image in images_json['media']:
            if image not in image_li:
                image_li.append(image['src'])
        item["images"] = image_li
        cover = images_json['flat_image']['src']
        item["cover"] = cover if cover else image_li[0]

    def _sizes(self,res,item,**kwargs):
        sizes_info = res.xpath('//span[@class="nosto_sku"]')
        sizes = []
        for size_li in sizes_info:
            check_size = size_li.xpath('./span[@class="availability"]/text()').extract_first()
            if "outofstock" not in check_size.lower():
                sizes.append(size_li.xpath('./span[@class="custom_fields"]/span/text()').extract_first())
        item['originsizes'] =  list(set(sizes)) 

    def _parse_images(self, response, **kwargs):
        images = json.loads(response.extract_first())
        image_li = []
        for image in images['media']:
            if image not in image_li:
                image_li.append(image['src'])
        return image_li
    
    def _page_num(self, data, **kwargs):

        return int(5)

    def _list_url(self, i, response_url, **kwargs):
        return response_url + '{}'.format(i)

    def _parse_item_url(self,response,**kwargs):
        item_data_json = response.xpath('//script[contains(text(),"const configElement = document.getElement")]/text()').extract_first()
        item_datas = re.findall(r'handle:"(.*?)"',item_data_json,re.M)
        for url_item in set(item_datas):
            url = response.url.split('?')[0] + '/products/' + url_item
            yield url,'designer'

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = json.loads(response.xpath(size_info['size_info_path']).extract_first())
        size_info = infos['metafields']['details']['size_and_fit']
        try:
            fit_size = "\n".join(re.findall('<li>(.*?)</li>',size_info))
        except:
            fit_size = ''
        return fit_size

_parser = Parser()

class Config(MerchantConfig):
    name = "bandier"
    merchant = "Bandier"
    merchant_headers = {
    'User-Agent':'ModeSensBotBandier20210901',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            ),
        product=OrderedDict([
            ('checkout',('//script[@id="elevar-gtm-suite-config"]/text()',_parser.checkout)),
            ('sku','//div[@class="nosto_product"]/span[@class="product_id"]/text()'),
            ('name','//div[@class="nosto_product"]/span[@class="name"]/text()'),
            ('designer','//span[@class="brand"]/text()'),
            ('color',('//script[@text="text/javascript"]/text()',_parser.color)),
            ('price', ('//html', _parser.prices)),
            ('images', ('//script[@type="application/json"][contains(text(),"details")]/text()', _parser.images)),
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
            size_info_path = '//script[@type="application/json"][contains(text(),"details")]/text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
            "https://www.bandier.com/collections/accessories?page=",
            ],
            c = [
            "https://www.bandier.com/collections/new-bottoms?page=",
            "https://www.bandier.com/collections/tops?page=",
            "https://www.bandier.com/collections/loungewear?page=",
            "https://www.bandier.com/collections/bras?page=",
            "https://www.bandier.com/collections/kits?page=",
            ],
            s = [
            "https://www.bandier.com/collections/shoes?page=",
            ]
        ),
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )