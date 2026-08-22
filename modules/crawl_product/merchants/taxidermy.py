from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):

    def _parse_multi_items(self, response, item, **kwargs):
        item['designer'] = "TAXIDERMY"
        item['url'] = response.url.split('?')[0] + '?ref=modesens'
        item['name'] = response.xpath(
            '//h1[@class="product_title entry-title"]/text()').extract()[0].strip()
        nameupper = item['name'].upper()
        detail = response.xpath('//div[@id="tab-description"]/p[1]//text()').extract()
        datas = response.xpath('//form[@class="variations_form cart"]/@data-product_variations').extract()
        skus = []
        try:
            datas = json.loads(datas[0])
            for data in datas:
                itm = deepcopy(item)
                itm['color'] = data['attributes']['attribute_color'].upper()
                sku = data['sku']
                itm['sku'] = sku + '_' + itm['color']
                skus.append(itm['sku'])
                instock = data['is_in_stock']
                itm['images'] = data['image']['url']
                itm['cover'] = itm['images'][0]
                itm['originsaleprice'] = data['display_price']
                itm['originlistprice'] = data['display_regular_price']
                itm['saleprice'] = float(itm['originsaleprice']) 
                itm['listprice'] = float(itm['originlistprice']) 
                itm['description'] = detail[0].strip()
                if itm['category']=='s':
                # Adding all sizies becaues these are made on order
                    itm['sizes'] = 'IT35;IT35.5;IT36;IT36.5;IT37;IT37.5;IT38;IT38.5;IT39;IT39.5;IT40;IT40.5;IT41;IT41.5;IT42;IT42.5;IT43'
                    itm['originsizes'] = 'IT35;IT35.5;IT36;IT36.5;IT37;IT37.5;IT38;IT38.5;IT39;IT39.5;IT40;IT40.5;IT41;IT41.5;IT42;IT42.5;IT43'
                else:
                    itm['sizes'] = 'IT'
                    itm['originsizes'] = 'IT'
                if itm['sizes'] and itm['sizes'][-1] != ';':
                    itm['sizes'] += ';'
                if itm['originsizes'] and itm['originsizes'][-1] != ';':
                    itm['originsizes'] += ';'
                yield itm
        except:
            try:
                price = response.xpath('//p[@class="price"]/span/text()').extract()
                item['originsaleprice'] = price[0].replace(',','')
                item['originlistprice'] = price[0].replace(',','')
            except:
                saleprice = response.xpath('//p[@class="price"]/ins/span/text()').extract()
                listprice = response.xpath('//p[@class="price"]/del/span/text()').extract()
                item['originsaleprice'] = saleprice[0].replace(',','')
                item['originlistprice'] = listprice[0].replace(',','')
            item['saleprice'] = float(item['originsaleprice']) 
            item['listprice'] = float(item['originlistprice'])
            item['images'] = []
            images = response.xpath('//div[contains(@class,"product-gallery__image")]/a/img/@src').extract()
            for i in images:
                if '-1-' in i:
                    i = i.split('-1-')[0] + '-1.jpg'
                item['images'].append(i)
            item['cover'] = item['images'][0]
            try:
                item['sku'] = response.xpath('//span[@class="sku"]/text()').extract()[0]
            except:
                item['sku'] = ''
                item['sizes'] = ''
                item['originsizes'] = ''
                item['error'] = 'Out of Stock'
                yield item
                return
            item['color'] = ''
            item['description'] = detail[0].strip()
            if item['category']=='s':
                # Adding all sizies becaues these are made on order
                item['sizes'] = 'IT35;IT35.5;IT36;IT36.5;IT37;IT37.5;IT38;IT38.5;IT39;IT39.5;IT40;IT40.5;IT41;IT41.5;IT42;IT42.5;IT43'
                item['originsizes'] = 'IT35;IT35.5;IT36;IT36.5;IT37;IT37.5;IT38;IT38.5;IT39;IT39.5;IT40;IT40.5;IT41;IT41.5;IT42;IT42.5;IT43'
            else:
                item['sizes'] = 'IT'
                item['originsizes'] = 'IT'
            if item['sizes'] and item['sizes'][-1] != ';':
                item['sizes'] += ';'
            if item['originsizes'] and item['originsizes'][-1] != ';':
                item['originsizes'] += ';'
            yield item

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item





    def _parse_images(self, response, **kwargs):

        datas = response.xpath('//form[@class="variations_form cart"]/@data-product_variations').extract()
        
        try:
            datas = json.loads(datas[0])
            images = {}
            for data in datas:


                sku = data['sku']
                try:
                    color = '_'+data['attributes']['attribute_color'].upper()
                except:
                    color = ''
                color_sku = sku  + color
                images[color_sku] = []
                image = data['image']['url']
                images[color_sku].append(image)
            return images
        except:
            images = {}
            image = response.xpath('//div[contains(@class,"product-gallery__image")]/a/img/@src').extract()

            try:
                sku = response.xpath('//span[@class="sku"]/text()').extract()[0]
            except:
                return None
            images[sku] = []
            for i in image:
                if '-1-' in i:
                    i = i.split('-1-')[0] + '-1.jpg'
                if sku in i and i not in images[sku]:
                    images[sku].append(i)

            return images

    def _parse_item_url(self, response, **kwargs):
        try:
            pages = int(response.xpath('//ul[@class="page-numbers"]/li/a/text()').extract()[-1])
        except:
            pages = 1
        for i in range(1, pages+1):
            url = response.url.replace('page/11','').replace('page/1','').replace('page/','') + 'page/' + str(i) + '/'
            result = getwebcontent(url) 
            html = etree.HTML(result)
            for quote in html.xpath('//ul[contains(@class,"products")]/li'):
                href = quote.xpath('./a/@href')[0]
                if href is None:
                    continue
                designer='TAXIDERMY'
                yield href, designer

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="woocommerce-result-count"]/text()').extract_first().lower().replace('results','').replace('showing','').replace('all','').strip())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = "taxidermy"
    merchant = "TAXIDERMY"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="woocommerce-result-count"]/text()',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            items = '//ul[contains(@class,"products")]/li',
            designer = './/div/@data-brand',
            link = './a/@href',
            ),
        product = OrderedDict([
            # ('checkout', ('//html', _parser.checkout)),
            # ('sku', ('//meta[@itemprop="sku"]/@content',_parser.sku)),
            # ('name', '//h1[@class="product_title entry-title"]/text()'),  
            # ('designer', '//h1[@class="product-brand"]//text()'),
            # ('color','//div[@class="l-product-details js-product_detail"]//span[@class="js_color-description"]/text()'),
            # ('images', ('//div[@id="gallery_thumbs"]//ul/li/img/@src', _parser.images)),
            # ('description', ('//div[@class="accordion_content_inner"]/p[1]//text()',_parser.description)),
            # ('sizes', ('//html', _parser.sizes)), 
            # ('prices', ('//html', _parser.prices)),
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
        f = dict(

            s = [
                "https://shoptaxidermy.com/product-category/shoes/page/1"
            ],
            b = [
                "https://shoptaxidermy.com/product-category/handbags/page/1",
                "https://shoptaxidermy.com/product-category/wallets/page/1",
                "https://shoptaxidermy.com/product-category/stocking-stuffers/",
                "https://shoptaxidermy.com/product-category/minibags/",
                "https://shoptaxidermy.com/product-category/travel/",
                "https://shoptaxidermy.com/product-category/crossbody-bags/",
                "https://shoptaxidermy.com/product-category/luxe-leather/",
                "https://shoptaxidermy.com/product-category/totes/",
                "https://shoptaxidermy.com/product-category/clutches/",
                
            ],
            a = [
                "https://shoptaxidermy.com/product-category/accessories/page/1",
                "https://shoptaxidermy.com/product-category/belts/page/1",
            ],
            c = [
                "https://shoptaxidermy.com/product-category/apparel/page/1"
            ],
        ),
        m = dict(
            s = [
                
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

    )

    parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
        ),

        )

        


