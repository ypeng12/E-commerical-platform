from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):

    def _page_num(self, data, **kwargs):
        items_num = data.replace('"','').replace(',','').lower().replace('results','').split()[0]
        page_num = int(items_num) / 12
        return page_num + 1

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?sz=12&start=%s'%((i-1)*12)
        return url

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first()

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'THEORY'
        
    def _sizes(self, sizes, item, **kwargs):
        size_li = []
        if item['category'] in ['a','b']:
            if not sizes:
                size_li.append('IT')
            else:
                size_li = sizes
        else:
            for size in sizes:
                if size.strip() not in size_li:
                    size_li.append(size.strip())
        item['originsizes'] = size_li

    def _prices(self, price, item, **kwargs):
        salePrice = price.xpath('//div[@class="mobile-product-header"]//div[@class="product-price"]/span[@class="price-sales"]/text()')
        listPrice = price.xpath('//div[@class="mobile-product-header"]//div[@class="product-price"]/span[@class="price-standard"]/text()')
        if not len(salePrice):
            salePrice = price.xpath('//div[@class="product-price"]/span[@class="price-sales"]/text()')
            listPrice = price.xpath('//div[@class="product-price"]/span[@class="price-standard"]/text()')
        item['originlistprice'] = listPrice[0] if len(listPrice) else salePrice[0]
        item['originsaleprice'] = salePrice[0]      

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

    def _parse_multi_items(self, response, item, **kwargs):
        colors_data = response.xpath('//ul[@data-attr-type="color"]/li')
        colors_li = []
        skus = []
        for color in colors_data:
            colors_dict = {}
            color_str = color.xpath('./a[@class="swatchanchor is-color-anchor"]/@title').extract_first()
            color_id = color.xpath('./a[@class="swatchanchor is-color-anchor"]/@href').extract_first()
            colors_dict['color'] = color_str.split(':')[-1].strip()
            cid = color_id.split("color=")[-1].split('&')[0]
            if not cid:
                cid = response.url.split('color=')[-1]
            colors_dict['id'] = cid
            colors_li.append(colors_dict)
        for color_dict in colors_li:
            item_color = deepcopy(item)
            item_color['color'] = color_dict['color']
            item_color['sku'] = item['sku'] + item_color['color']
            skus.append(item_color['sku'])
            if item['country'] == 'US':      
                base_url = 'https://www.theory.com/on/demandware.store/Sites-theory2_US-Site/default/Product-Variation?pid={sku}&dwvar_{sku}_color={color}'
            elif item['country'] == 'GB':
                base_url = 'https://uk.theory.com/on/demandware.store/Sites-theory_uk-Site/en_GB/Product-Variation?pid={sku}&dwvar_{sku}_color={color}'
            res = requests.get(base_url.format(sku=item['sku'], color=color_dict['id']))
            html = etree.HTML(res.text)
            sizes = html.xpath('//ul[@class="swatches clearfix size"]/li[not(contains(@class, "nope"))]/@data-attid')
            self.sizes(sizes, item_color, **kwargs)
            img_li = html.xpath('//div[@class="pdp-slider"]/div//img[@itemprop="image"]/@src')
            imgs = []
            for img in img_li:
                if 'http' not in img:
                    img = 'https:' + img
                if img not in imgs:
                    imgs.append(img.split('?')[0] + '?$TH-pdp-tablet$')
            item_color['cover'] = imgs[0] if len(imgs) else ''
            item_color['images'] = imgs
            if len(sizes):
                if item['country'] == 'US':
                    base_url = 'https://www.theory.com/on/demandware.store/Sites-theory2_US-Site/default/Product-Variation?pid={sku}&dwvar_{sku}_color={color}&dwvar_{sku}_size={size}'
                elif item['country'] == 'GB':
                    base_url = 'https://uk.theory.com/on/demandware.store/Sites-theory_uk-Site/en_GB/Product-Variation?pid={sku}&dwvar_{sku}_color={color}&dwvar_{sku}_size={size}'
                res = requests.get(base_url.format(sku=item['sku'], color=color_dict['id'], size=sizes[0]))
                html = etree.HTML(res.text)
                prices = html.xpath('//div[@class="mobile-product-header"]//div[@class="product-price"]')
                self.prices(html, item_color, **kwargs)
            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        fit_li = response.xpath('//div[@class="pdp-fit"]/ul/li/text()').extract()
        details = response.xpath('//div[@class="pdp-details pdp-fabric"]/ul/li/text()').extract()
        infos = fit_li + details
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info or 'dimensions' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="results-count float-left"]/span/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'theory'
    merchant = 'Theory'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="results-count float-left"]/span/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@id="search-result-items"]/div',
            designer = './/div[@class="sc-dyGzUR kCMbOt sc-hBbWxd cqWPzI"]/text()',
            link = './/div[@class="product-image"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add-to-cart"]', _parser.checkout)),
            ('sku', ('//div[@data-gtm-master-pid]/@data-gtm-master-pid', _parser.sku)),
            ('name', '//meta[@property="og:title"]/@content'),    # TODO: path & function
            ('designer', ('//html',_parser.designer)),
            ('description', ('//meta[@property="og:description"]/@content',_parser.description)),
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//html',
            ),
        designer = dict(

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    parse_multi_items = _parser.parse_multi_items


    list_urls = dict(
        f = dict(
            a = [
                'https://www.theory.com/womens-jewelry/',
                'https://www.theory.com/womens-sunglasses/',
                'https://www.theory.com/womens-accessories-belts/',

            ],
            b = [
                'https://www.theory.com/womens-bags-crossbody/',



            ],
            c = [
                'https://www.theory.com/womens-outerwear/',
                'https://www.theory.com/womens-sweaters/',
                'https://www.theory.com/womens-pants/',
                'https://www.theory.com/womens-dresses/',
                'https://www.theory.com/womens-sweaters/',
                'https://www.theory.com/womens-tops/',
                'https://www.theory.com/womens-tshirts/',
                'https://www.theory.com/womens-skirts/',
                'https://www.theory.com/womens-denim/',
                'https://www.theory.com/womens-swim/',
                'https://www.theory.com/womens-dresses-sale/',
                'https://www.theory.com/womens-pants-sale/',
                'https://www.theory.com/womens-tops-sale/',
                'https://www.theory.com/womens-outerwear-sale/',
                'https://www.theory.com/womens-sweaters-sale/',
                'https://www.theory.com/womens-jackets-sale/',
                'https://www.theory.com/womens-skirts-sale/',

            ],
            s = [
                'https://www.theory.com/womens-shoes/',
            ],
        ),
        m = dict(
            a = [
                'https://www.theory.com/mens-accessories/',
                'https://www.theory.com/mens-accessories-sale/',
            ],
            b = [
            ],
            c = [
                'https://www.theory.com/mens-outerwear/',
                'https://www.theory.com/mens-pants/',
                'https://www.theory.com/mens-sweaters/',
                'https://www.theory.com/mens-suits/',
                'https://www.theory.com/mens-shirts/',
                'https://www.theory.com/mens-blazers/',
                'https://www.theory.com/mens-tshirts/',
                'https://www.theory.com/mens-denim/',
                'https://www.theory.com/mens-shorts/',
                'https://www.theory.com/mens-pants-sale/',
                'https://www.theory.com/mens-shirts-sale/',
                'https://www.theory.com/mens-outerwear-sale/',
                'https://www.theory.com/mens-sweaters-sale/',
            ],
            s = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'www.',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = 'www.',
            currency_sign = '$',
            ),
        
        # GB = dict(
        #     area = 'GB',
        #     currency = 'GBP',
        #     country_url = 'uk.',
        #     currency_sign = u'\xa3',
        #     translate = [
        #         ('sweaters', 'knitwear'),
        #         ('swim', 'trousers'),
        #         ('denim', 'jumpsuits'),
        #         ('bags-crossbody', 'accessories-viewall'),
        #         ('jewelry', 'accessories'),
        #     ]
        # ),

        )

        


