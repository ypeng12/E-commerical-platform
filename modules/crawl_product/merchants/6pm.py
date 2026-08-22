from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
import json
from copy import deepcopy
from utils.cfg import *
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True
        
    def _page_num(self, data, **kwargs):
        num = data.split()[-1]
        return int(num)

    def _description(self, description, item, **kwargs):
        descs = description.extract()
        desc_str = []
        for desc in descs:
            if desc.strip():
                desc_str.append(desc.strip())
        item['description'] = '\n'.join(desc_str)

    def _prices(self, scripts, item, **kwargs):
        script_li = scripts.extract()
        json_str = ''
        for script in script_li:
            if 'styles' in script:
                json_str = script
                break
                
        json_dict = json.loads(json_str.split('INITIAL_STATE__ = ')[-1].strip()[:-1].strip())
        item['tmp'] = json_dict
        item['originlistprice'] = json_dict['product']['detail']['styles'][0].get('originalPrice', '')
        item['originsaleprice'] = json_dict['product']['detail']['styles'][0].get('price')

    def _parse_multi_items(self, response, item, **kwargs):
        json_dict = item['tmp']
        products = json_dict['product']['detail']['styles']
        colors_sizes = {}
        color_ids = {}
        color_urls = {}
        colorIds = []
        for product in products:
            colors_sizes[product['color']] = []
            color_ids[product['color']] = []
            color_ids[product['color']].append(product['colorId'])
            colorIds.append(product['colorId'])
            color_ids[product['color']].append(product['images'])
            for sto in product['stocks']:
                if sto['size'] not in colors_sizes:
                    colors_sizes[product['color']].append(sto['size'])
            color_urls[product['color']] = urljoin(response.url, product['productUrl'])

        if 'sku' in kwargs and kwargs['sku']:
            color_id = kwargs['sku'].split('_')[-1]
            if color_id not in colorIds:
                item['sku'] = kwargs['sku']
                item['originsizes'] = ''
                item['sizes'] = ''
                item['error'] = 'Out Of Stock'
                colors_sizes = {}
                yield item

        for color,sizes in list(colors_sizes.items()):
            item_color = deepcopy(item)
            for product in products:
                if product['colorId'] == color_ids[color][0]:
                    item_color['url'] = urljoin(response.url,product['productUrl'])
            item_color['color'] = color
            item_color['url'] = color_urls[color]
            item_color['sku'] = item_color['sku'] + '_' + color_ids[color][0]

            item_color['originsizes'] = sizes
            self.sizes(sizes, item_color, **kwargs)

            img_ids = color_ids[color][1]
            img_li = []
            for img_id in img_ids:
                img = img_id['imageId']
                img = 'https://m.media-amazon.com/images/I/%s._SX480_.jpg'%img
                img_li.append(img)
            item_color['images'] = img_li
            item_color['cover'] = img_li[0]
            if color.upper() not in item_color['name']:
                item_color['name'] += ', %s' % color.upper()
            yield item_color

    def _parse_images(self, response, **kwargs):
        images = []
        script_li = response.xpath('//script/text()').extract()
        json_str = ''
        for script in script_li:
            if 'styles' in script:
                json_str = script
                break
        json_dict = json.loads(json_str.split(' = ')[-1].strip()[:-1])
        color_id = response.meta['sku'].split('_')[-1]
        for style in json_dict['product']['detail']['styles']:
            if color_id == style['colorId']:
                for image in style['images']:
                    img = 'https://m.media-amazon.com/images/I/%s._SX480_.jpg' %image['imageId']
                    images.append(img)

        return images

    def _designer_desc(self, data, item, **kwargs):
        descriptions = data.extract()
        desc_li = []
        for desc in descriptions:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description


    def _parse_swatches(self, response, swatch_path, **kwargs):
        current_pid = response.xpath(swatch_path['current_path']).extract()[0]

        scripts = response.xpath('//script/text()').extract()
        for script in scripts:
            if 'customerInfo' in script:
                break

        obj = json.loads('{"styles"' + script.split('styles"')[-1].split(',"videoUrl')[0] + '}')

        datas = obj['styles']
        swatches = []
        for data in datas:
            pid = current_pid + '_' + data['colorId']
            swatches.append(pid)

        if len(swatches) > 1:
            return swatches
        else:
            return

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            if info.xpath('./text()').extract_first() and 'Measurements' in info.xpath('./text()').extract_first():
                break

        for i in info.xpath('./ul/li'):
            fit = ''.join(i.xpath('.//text()').extract())
            fits.append(fit.strip())
        size_info = '\n'.join(fits)

        return size_info
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="AR"]/text()').extract_first().replace('"','').strip())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = '6pm'
    merchant = '6PM.COM'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="_1-N-rQXDbC"]/text()',_parser.page_num),
            items = '//div[@class="searchPage"]//article',
            designer = './/span[@itemprop="name"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-track-value="Add-To-Cart"]', _parser.checkout)),
            ('sku', '//input[@name="productId"][1]/@value'),
            ('name', '//span[@itemprop="name"]/a/text()'),   # TODO: path & function
            ('designer', '//input[@name="brandName"]/@value'),
            ('description', ('//div[@itemprop="description"]//text()',_parser.description)), # TODO:
            ('prices', ('//script/text()', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            current_path='//input[@name="productId"]/@value',
            path='//div[@class="_1Vf5C"]/button',
            ),
        image = dict(
            method = _parser.parse_images,
            image_path = '//meta[@property="og:image"]/@content',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div',
            ),
        designer = dict(
            link = '//div[@class="AB"]/ul/li/a/@href',
            designer = '//div[@class="Bb testWrapper"]/h1/text()',
            description = ('//div[@class="Fj"]//text()',_parser.designer_desc),
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    designer_url = dict(
        EN = dict(
            u = 'https://www.6pm.com/c/brands',
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.6pm.com/men-accessories/COfWAcABAuICAgEY.zso?p=0",
                "https://www.6pm.com/men-eyewear/CKzXAcABAuICAgEY.zso?p=0",
            ],
            b = [
                "https://www.6pm.com/men-bags/COjWAcABAuICAgEY.zso?p=0",
            ],
            c = [
                "https://www.6pm.com/men-clothing/CKvXAcABAuICAgEY.zso?p=0",
            ],
            s = [
                "https://www.6pm.com/men-shoes/CK_XAcABAuICAgEY.zso?p=0",
            ],
        ),
        f = dict(
            a = [
                "https://www.6pm.com/women-accessories/COfWAcABAeICAgEY.zso?p=0",
                "https://www.6pm.com/eyewear-women/wAEB4gIBGA.zso?t=eyewear&p=0",
                "https://www.6pm.com/women-watches/CLHXAcABAeICAgEY.zso?p=0",
                "https://www.6pm.com/women-jewelry/CK7XAcABAeICAgEY.zso?p=0",
            ],
            b = [
                "https://www.6pm.com/women-handbags/COjWARCS1wHAAQHiAgMBAhg.zso?p=0",
            ],
            c = [
                "https://www.6pm.com/women-clothing/CKvXAcABAeICAgEY.zso?p=0",
            ],
            s = [
                "https://www.6pm.com/women-shoes/CK_XAcABAeICAgEY.zso?p=0",
            ],

        params = dict(
            page = 1,
            ),
        ),
    )
    parse_multi_items = _parser.parse_multi_items

    countries = dict(
        US = dict(
            area = 'US',
            language = 'EN', 
            currency = 'USD',
            ),

        )

        


