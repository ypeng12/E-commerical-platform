from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        script = checkout.xpath('.//script[@type="application/ld+json"]/text()').extract_first()
        if script:
            data = json.loads(script)
        else:
            return True

        if 'MJI_' in data['image'] and '_1-1' in data['image']:
            colorid = data['image'].split('MJI_')[-1].split('_1-1')[0].split('_')[-1]
            if 'color=' in item['url'] and colorid != item['url'].split('color=')[-1]:
                return True

        add_to_bag = checkout.xpath('.//button[contains(@class,"size-selection-button")][not(contains(@class,"disabled"))]/@value').extract()
        if not add_to_bag:
            return True
        else:
            return False
            
    def _sku(self, script, item, **kwargs):
        data = json.loads(script.extract_first())
        if 'MJI_' in data['image'] and '_1-1' in data['image']:
            item['sku'] = data['image'].split('MJI_')[-1].split('_1-1')[0]
            pid = item['sku'].split('_')[0]
            colorid = item['sku'].split('_')[-1]
        else:
            item['sku'] = ''
        item['designer'] = data['brand']['name'].upper()

        item['url'] = item['url']+'?dwvar_'+pid+'_color='+colorid if '?dwvar_' not in item['url'] else item['url']

    def _name(self, script, item, **kwargs):
        data = json.loads(script.extract_first())
        item['name'] = data['name']

    def _images(self, images, item, **kwargs):
        images = images.extract()
        images = [x.split('?')[0] for x in images]
        item['cover'] = ''
        for image in images:
            if 'MAIN' in image:
                item['cover'] = image
        if not item['cover']:
            item['cover'] = images[0]
        
        img_li = []
        for image in images:
            if image not in img_li:
                img_li.append(image)
        item['images'] = img_li
     
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        item['originsizes'] = []
        for size in sizes:
            osize = 'One Size' if size.strip() == '1SZ' else size.strip()
            item['originsizes'].append(osize)

        if kwargs['category'] in ['a', 'b', 'e'] and not item['originsizes']:
            item['originsizes'] = ['One Size']

    def _prices(self, prices, item, **kwargs):
        
        listprice = prices.xpath('.//span[@class="toolbar__price toolbar__price--strike"]/@content').extract()
        saleprice = prices.xpath('.//span[@class="toolbar__price"]/@content').extract()
        try:
            if len(listprice):
                item['originsaleprice'] = saleprice[0].strip()
                item['originlistprice'] = listprice[0].strip()
            else:
                item['originsaleprice'] = saleprice[0].strip()
                item['originlistprice'] = saleprice[0].strip()
        except:
                item['originsaleprice'] = ''
                item['originlistprice'] = ''
                item['error'] = 'Do Not Ship'

    def _parse_item_url(self, response, **kwargs):
        items = response.xpath('//div[contains(@class,"product-grid__list-element")]')
        for item in items:
            url = item.xpath('./div/a/@href').extract_first()
            yield url,'MARC JACOBS'

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//picture[@class="image"]/img[@class="switchable"]/@src').extract()         
        images = [x.split('?')[0] for x in images]
        images = list(set(images))
        images = sorted(images, key=lambda x:x.split('?')[0].split('_')[-1])
        cover = ''
        for image in images:
            if 'MAIN' in image:
                cover = image   
        img_li = []     
        if cover:
            img_li = [cover] + images[:-1]
        else:
            img_li = images

        if img_li:
            return img_li
        

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[contains(@class,"product-grid__list-element")]/div/a/@href').extract())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = "marcjacobs"
    merchant = "MARC JACOBS"

    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//html',_parser.page_num),
            # items = '//div[@class="product-grid__list-element"]',
            # designer = '@data-ytos-track-product-data',
            # link = './div/a/@href',
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('name', ('//script[@type="application/ld+json"]/text()',_parser.name)),
            ('color', '//input[@name="colorSelector"][@checked]/@data-label'),
            ('images', ('//div[@class="swiper-wrapper"]//picture[@class="image"]//img/@src', _parser.images)),
            ('description', '//meta[@name="description"]/@content'),
            ('sizes', ('//button[contains(@class,"size-selection-button")][not(contains(@class,"disabled"))]/@value', _parser.sizes)), 
            ('prices', ('//div[@class="pdpw__price"]', _parser.prices)),
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
            size_info_path = '//h3[contains(text(),"Dimensions")]/following-sibling::p//text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-watches&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-strap-shop&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-tech&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-jewelry&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-hair&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-sunglasses&start=0&sz=10000&startingOffset=1000",
                "",
            ],
            b = [
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=bags-view-all&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=wallets-view-all&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-cosmetic-bags&start=0&sz=10000&startingOffset=1000",
            ],
            c = [
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=clothing-view-all&start=0&sz=10000&startingOffset=1000",
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=accessories-socks-tights&start=0&sz=10000&startingOffset=1000",
            ],
            s = [
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=shoes-view-all&start=0&sz=10000&startingOffset=1000",
                ],
            e = [
                "https://www.marcjacobs.com/on/demandware.store/Sites-mjsfra-Site/default/Search-UpdateGrid?cgid=beauty-view-all&start=0&sz=10000&startingOffset=1000",
            ]
        ),
        m = dict(
            a = [],
            b = [],
            c = [],
            s = [],

        params = dict(
            # TODO:
            ),
        ),

        country_url_base = '',
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {'BLCountry':'US'},
            ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            cookies = {'BLCountry':'CA'},
            ),
        )

        


