from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _parse_images(self, response, **kwargs):
        scripts = response.xpath('//script/text()').extract()
        script_str = ''
        for script in scripts:
            if 'skusInfo' in script:
                script_str = script
                break
        skus_str = script_str.split('skusInfo =')[-1].split('var color_images')[0].strip()
        skus_dict = json.loads(skus_str)
        mainSku = skus_dict['productDatas'][0]['thirdPartyId']
        colors_sizes = []
        for sku in skus_dict['skuInfos']:
            item_id = sku['itemId']
            color = sku['options'][0]['optionValue']['value'] if sku['options'][0]['name']=="Color" else sku['options'][1]['optionValue']['value']
            size = sku['options'][1]['optionValue']['value'] if sku['options'][1]['name']=="Size" else sku['options'][0]['optionValue']['value']
            if color not in colors_sizes:
                colors_sizes[color] = []
            if item_id in slodOut_id or size == '00':
                continue
            colors_sizes.append(color)
        imgs = {}
        imgs_str = script_str.split('color_images =')[-1].split(';')[0].strip()
        imgs_dic = json.loads(imgs_str)
        
        for color in colors_sizes:
            colorSku = mainSku + '_' + color.upper().replace(' ','_')
            imgs[colorSku] = []
            images = list(imgs_dic[color].values())
            for image in images:
                image = image.get('IMG_1200','')
                if not image:
                    continue
                if 'http' not in image:
                    image = urljoin('https://vb.ips.photos/veronicabeard-java/images/skus/',image)
                    imgs[colorSku].append(image)
        return imgs

    def _parse_multi_items(self, response, item, **kwargs):
        colors_sizes = {}
        slodOut_id = []
        num = item['url'].split('-')[-1].split('.html')[0]
        try:
            num = str(int(num))
        except:
            pid_script = ''
            scripts = response.xpath('//script/text()').extract()
            for script in scripts:
                if 'skusInfo' in script:
                    pid_script = script
                    break
            num = pid_script.split('"productId":"')[-1].split('"')[0]

        base_url = 'https://www.veronicabeard.com/front/app/product/inventory/%s.json'%num
        req = requests.get(base_url)
        sizes_str = req.text
        sizes_dic = json.loads(sizes_str)
        sizes_info = sizes_dic['productInfo']['skuInfos']

        for info in sizes_info:
            if not info['inStock']:
                slodOut_id.append(info['itemId'])

        script_str = item['tmp']
        skus_str = script_str.split('skusInfo =')[-1].split('var color_images')[0].strip()
        skus_dict = json.loads(skus_str)
        for sku in skus_dict['skuInfos']:
            item_id = sku['itemId']
            color = sku['options'][0]['optionValue']['value'] if sku['options'][0]['name']=="Color" else sku['options'][1]['optionValue']['value']
            size = sku['options'][1]['optionValue']['value'] if sku['options'][1]['name']=="Size" else sku['options'][0]['optionValue']['value']
            if color not in colors_sizes:
                colors_sizes[color] = []
            if item_id in slodOut_id or size == '00':
                continue
            colors_sizes[color].append(size)

        imgs = []
        imgs_str = script_str.split('color_images =')[-1].split(';')[0].strip()
        imgs_dic = json.loads(imgs_str)

        skus = []

        for color,size_li in list(colors_sizes.items()):
            item_color = deepcopy(item)
            item_color['sizes'] = []
            item_color['color'] = color
            item_color['sku'] = item_color['sku'] + '_' + color.upper().replace(' ','_')
            skus.append(item_color['sku'])
            item_color['description'] = item_color['description'] + '; \n' + color.upper()
            images = list(imgs_dic[color].values())
            img_li = []
            for image in images:
                image = image.get('IMG_1200','')
                if not image:
                    continue
                if 'http' not in image:
                    image = urljoin('https://vb.ips.photos/veronicabeard-java/images/skus/',image)
                    img_li.append(image)
                    if '_01' in image:
                        item_color['cover'] = image
            item_color['images'] = list(set(img_li))

            if item_color['category'] in ['a','b']:
                if not size_li:
                    size_li = ['IT']
                    
            item_color['originsizes'] = size_li

            for orisize in item_color['originsizes']:
                if item_color['category'] in ['a','b','e']:
                    item_color['sizes'] = ['IT']
                elif item_color['category'] == 'c':
                    size = clothToItSize(orisize.upper(), item_color['gender'])
                    item_color['sizes'].append(size)
                elif item_color['category'] == 's':
                    size = toItSize(orisize.upper(), item_color['gender'])
                    item_color['sizes'].append(size)
            if item_color['originsizes']:
                item['originsizes'] = '####' + ';'.join([x[0].replace('IT','')+'-'+x[1] for x in zip(item_color['sizes'],item_color['originsizes'])])
                item_color['sizes'].sort()
                item_color['sizes'] = ';'.join(item_color['sizes']) + ';'
            else:
                item_color['originsizes'] = ''
                item_color['sizes'] = ''
                item_color['error'] = 'Out Of Stock'
            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _sku(self, scripts, item, **kwargs):
        scripts = scripts.extract()
        script_str = ''
        for script in scripts:
            if 'skusInfo' in script:
                script_str = script
                break
        skus_str = script_str.split('skusInfo =')[-1].split('var color_images')[0].strip()
        skus_dict = json.loads(skus_str)
        item['tmp'] = script_str
        item['sku'] = skus_dict['productDatas'][0]['thirdPartyId']

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

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('./text()').extract()
        listPrice = prices.xpath('./strike/text()').extract_first()
        item['originlistprice'] = listPrice if listPrice else ''
        item['originsaleprice'] = salePrice[1].strip() if listPrice else salePrice[0].strip()

    def _parse_item_url(self, response, **kwargs):
        data_str = response.body
        data_dict = json.loads(data_str)
        products = data_dict['response']['docs']
        for product in products:
            url = urljoin('https://www.veronicabeard.com/',product['page_name_s'])
            designer = ''
            yield url,designer

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract_first()
        descs = infos.split('.')
        desc_li = []
        skip = False
        for i in range(len(descs)):            
            if skip:
                try:
                    num1 = int(descs[i][-1])
                    num2 = int(descs[i+1][0])
                    desc_li[-1] = desc_li[-1] + '.' + descs[i+1]
                except:
                    skip = False
                continue
            if 'model' in descs[i] or 'measures' in descs[i] or '/' in descs[i] or 'Length' in descs[i]:
                try:
                    try:
                        num1 = int(descs[i][-1])
                        num2 = int(descs[i+1][0])
                        desc = descs[i] + '.' + descs[i+1]
                        skip = True
                    except:
                        num1 = int(descs[i][0])
                        num2 = int(descs[i-1][-1])
                        desc = descs[i-1] + '.' + descs[i]
                except:
                    desc = descs[i]
                desc_li.append(desc.strip())

        size_info = '\n'.join(desc_li)
        return size_info


_parser = Parser()


class Config(MerchantConfig):
    name = 'vb'
    merchant = 'Veronica Beard'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            # items = '//div[@id="product-container"]/div[@id]',
            # designer = './div[@class="product-text"]/a/p/span/text()',
            # link = './div[@class="product-text"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//a[@class="btn add-to-bag"]', _parser.checkout)),
            ('sku',('//script/text()', _parser.sku)),
            ('name', '//h1[@class="quickshop-title"]/text()'),
            # ('designer', '//a[@class="product-overview__brand-link"]/@content'),
            # ('color','//input[@id="pr_color"]/@value'),
            ('description', ('//div[@class="accordion-body-inner"]//text()',_parser.description)),
            ('prices', ('//p[@class="quickshop-price"]', _parser.prices)),
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
            size_info_path = '//h3[contains(text(),"DETAILS & FIT")]/../../div[@class="accordion-body"]/div/p/text()',
            ),
        )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_253_i+asc&q=attr_cat_id%3A253&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_321_i+asc&q=attr_cat_id%3A321&facet.limit=100?p=',
            ],
            b = [
            ],
            c = [
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_8_i+asc&q=attr_cat_id%3A8&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_9_i+asc&q=attr_cat_id%3A9&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_54_i+asc&q=attr_cat_id%3A54&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_51_i+asc&q=attr_cat_id%3A51&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_10_i+asc&q=attr_cat_id%3A10&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_11_i+asc&q=attr_cat_id%3A11&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_55_i+asc&q=attr_cat_id%3A55&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_52_i+asc&q=attr_cat_id%3A52&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_57_i+asc&q=attr_cat_id%3A57&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=1000&sort=cat_product_sequence_303_i+asc&q=attr_cat_id%3A303&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=1000&sort=cat_product_sequence_304_i+asc&q=attr_cat_id%3A304&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=1000&sort=cat_product_sequence_302_i+asc&q=attr_cat_id%3A302&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=1000&sort=cat_product_sequence_305_i+asc&q=attr_cat_id%3A305&facet.limit=100?p=',
            ],
            s = [
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_312_i+asc&q=attr_cat_id%3A312&facet.limit=100?p=',
                'https://www.veronicabeard.com/search/?wt=json&start=0&rows=10000&sort=cat_product_sequence_330_i+asc&q=attr_cat_id%3A330&facet.limit=100?p=',
            ],
        ),
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            cur_rate = 1,  # TODO
            # country_url = '/en-us/',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            # currency_sign = u'\xa3',
            # country_url = '/en-cn/',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            # currency_sign = u'\xa3',
            # country_url = '/en-jp/',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            # currency_sign = u'\xa3',
            # country_url = '/en-kr/',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            # currency_sign = u'\xa3',
            # country_url = '/en-sg/',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            # currency_sign = u'\xa3',
            # country_url = '/en-hk/', 
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            # discurrency = 'GBP',
            # currency_sign = u'\xa3',
            # country_url = '/en-gb/',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            # currency_sign = u'\xa3',
            # country_url = '/en-ru/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            # country_url = '/en-ca/',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            # currency_sign = u'\xa3',
            # country_url = '/en-au/',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            # currency_sign = u'\u20ac',
            # country_url = '/en-de/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            # currency_sign = u'\u20ac',
            # country_url = '/en-no/',
        ),

        )

        