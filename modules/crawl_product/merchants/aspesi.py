from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from copy import deepcopy
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "Whoops, our bad..." not in checkout.extract_first():
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = int(data.split('of ')[-1].strip().split(' ')[0])/24 + 1
        # pages = 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = response_url.replace('&start=0','&start='+str(24*i))
        return url
          
    def _images(self, images, item, **kwargs):
        img_li = images.xpath('.//ul[@data-colorswatchid="'+item['sku']+'"]//li/img/@src').extract()
        images = []
        for img in img_li:
            img = img.split('?')[0] + '?sw=869&sh=1072&sm=fit'
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        item['designer'] = "ASPESI"
        description = description.extract()
        
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('./span[@class="normal-price"]//span[@data-price-type="finalPrice"]/span/text()').extract_first()
        listprice = prices.xpath('./span[@class="old-price sly-old-price no-display"]//span[@data-price-type="oldPrice"]/span/text()').extract_first()

        item['originsaleprice'] = salePrice
        item['originlistprice'] = listprice if listprice else salePrice

    def _parse_multi_items(self,response,item,**kwargs):
        data_json = json.loads(response.xpath('//script[contains(text(),"[data-role=swatch-options]")]/text()').extract_first())
        data_num = data_json['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']
        for data in data_num['attributes']['277']['options']:
            item_color = deepcopy(item)
            item_color['color'] = data['label']
            item_color['sku'] = data['admin_label']

            sizes_info_ids = data['products']
            osize = []
            images_li = []
            for sizes_info in sizes_info_ids:
                if sizes_info in data_num['images'].keys():
                    for image in data_num['images'][sizes_info]:
                        if image['img'] not in images_li:
                            images_li.append(image['img'])
                sizes_index = data_num['attributes']['650']['options']
                for sizes in sizes_index:
                    if sizes_info in sizes['products']:
                        osize.append(sizes['label'])
            item_color['originsizes'] = osize
            item_color['images'] = images_li
            self.sizes(osize, item_color, **kwargs)
            yield item_color

    def _parse_images(self, response, **kwargs):
        data_json = json.loads(response.xpath('//script[contains(text(),"[data-role=swatch-options]")]/text()').extract_first())
        data_num = data_json['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']
        for data in data_num['attributes']['277']['options']:
            image_ids = data['products']
            images_li = []
            for image_id in image_ids:
                if data['admin_label'].replace('__','_') not in response.url.upper().replace('-','_'):
                    continue
                for image in data_num['images'][image_id]:
                    if image['img'] not in images_li:
                        images_li.append(image['img'])
            return images_li[:4]

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[contains(@class,"l-search")]/span/text()').extract_first().split('of ')[-1].strip().split(' ')[0])
        return number

_parser = Parser()

class Config(MerchantConfig):
    name = 'aspesi'
    merchant = "Aspesi"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[contains(@class,"l-search")]/span/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//a[contains(@class,"js-producttile_link")]',
            designer = './/h3[@class="list-product-brand"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//h1[@class="page-title"]/span/text()', _parser.checkout)),
            ('name', '//h1[@class="page-title"]/span/text()'),
            ('description', ('//div[@class="popup-content"]/div[@id="map-popup-text-what-this"]/text()',_parser.description)), # TODO:
            ('prices', ('//div[@class="product-info-price"]/div', _parser.prices))
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
            a = [
                "https://www.aspesi.com/en/accessories/unisex/?loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a=",
            ],
            b = [
            ],
            c = [
                "https://www.aspesi.com/en/men/clothing/?loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a=",
                "https://www.aspesi.com/en/men/pre-fall/?loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a=",
                "https://www.aspesi.com/en/men/fall-winter/?loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a="
            ],
            s = [
                "https://www.aspesi.com/en/men/highlights/sneakers/?loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a="
            ],
        ),
        f = dict(
            a = [
	            "https://www.aspesi.com/en/accessories/unisex/?comparecgid=women-navigation&loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a="
            ],
            b = [
                
            ],
            c = [
                'https://www.aspesi.com/en/women/clothing/?comparecgid=women-navigation&loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a=',
                "https://www.aspesi.com/en/women/highlights/mix-and-match/?comparecgid=women-navigation&loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a=",
                "https://www.aspesi.com/en/women/pre-fall/?comparecgid=women-navigation&loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a=",
                "https://www.aspesi.com/en/women/fall-winter/?comparecgid=women-navigation&loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a=",

            ],
            s = [
                "https://www.aspesi.com/en/women/highlights/sneakers/?comparecgid=women-navigation&loaderbar=true&sz=24&start=0&subview=false&position=next&format=page-element&a="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )
# preferredCountry
# preferredLanguage

    countries = dict(
        US = dict(
            area = 'EU',
            language = 'EN', 
            currency = 'USD',
            cookies = {'preferredCountry':'US'},
            ),

        CN = dict(
            area = 'EU',
            currency = 'CNY',
            discurrency = 'EUR',
            cookies = {
            'preferredCountry':'CN'
            },
        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            cookies = {
            'preferredCountry':'JP'
            },
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            cookies = {
            'preferredCountry':'KR'
            },
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = 'EUR',
            cookies = {
            'preferredCountry':'SG'
            },
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            discurrency = 'EUR',
            cookies = {
            'preferredCountry':'HK'
            },
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            country_url ="&Country=GB&",
            cookies = {
            'preferredCountry':'GB'
            },
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'EUR',
            cookies = {
            'preferredCountry':'RU'
            },
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            discurrency = 'USD',
            cookies = {
            'preferredCountry':'CA'
            },
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            discurrency = 'EUR',
            cookies = {
            'preferredCountry':'AU'
            },
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            cookies = {
            'preferredCountry':'DE'
            },
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            cookies = {
            'preferredCountry':'NO'
            },
        ),


        )
        


