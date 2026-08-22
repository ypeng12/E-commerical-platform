from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from copy import deepcopy
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *
from lxml import html
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):

        total = json.loads(data)['total']
        page_num = total/12 + 1
        
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('offset=')[0] + 'offset=' + str((i-1)*12)

        return url

    def _parse_item_url(self, response, **kwargs):
        prds_dict = json.loads((response.text))
        prds = prds_dict['products']
        for prd in prds:
            url = 'https://www.toryburch.com/' + prd['name'].lower().replace(' ','-') + '/' + prd['id'] + '.html' + '?color=' + prd['swatches'][0]['colorNumber']
            brand = prd['brand'].upper()

            yield url,brand

    def _parse_multi_items(self, response, item, **kwargs):
        pid = response.url.split('.html')[0].split('/')[-1]

        ajax_url = 'https://www.toryburch.com/api/prod-r2/v11/products/%s?site=ToryBurch_US'%pid
        headers = {
            'x-api-key': 'yP6bAmceig0QmrXzGfx3IG867h5jKkAs',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        prd_json = requests.get(ajax_url, headers=headers)
        prd_dict = json.loads(prd_json.text)
        if 'product' not in prd_dict.keys():
            logger.info('parse issue')
            return
        if 'error' in prd_dict or not prd_dict['product']['swatches']:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku'] if 'sku' in response.meta else ''
            item['error'] = 'Out Of Stock'
            swatches = []
            yield item
        else:
            item['designer'] = prd_dict['product']['brand'].upper()
            item['name'] = prd_dict['product']['name'].upper()
            swatches = prd_dict['product']['swatches']

        skus = []

        for color in swatches:
            item_color = deepcopy(item)  
            item_color['color'] = color['colorName'].upper()
            color_id = color['colorNumber']
            item_color['sku'] = prd_dict['product']['id'] + '_' + color_id
            skus.append(item_color['sku'])
            for prd_info in prd_dict['product']['variations']:
                if prd_info['values']['color'] == color_id:
                    img_li = prd_info['images']
                    images = ['https://s7.toryburch.com/is/image/ToryBurch/'+ x +'.pdp-470x535.jpg' for x in img_li if color_id in x]
                    item_color['cover'] = images[0]
                    item_color['images'] = images

                    item_color['originsaleprice'] = str(color['price']['min'])
                    item_color['originlistprice'] = str(color['price']['max'])
                    break
            descs = prd_dict['product']['longDescription']
            descs = descs.replace('\r','').replace('\t','').replace('\n','')
            descs = html.fromstring(descs)
            descs_li = []
            desc_li = descs.xpath('//li/text()')
            for desc in desc_li:
                if desc and desc not in descs_li:
                    descs_li.append(desc)
            item_color['description'] = '\n'.join(descs_li)

            self.sizes(prd_dict, item_color, **kwargs)
            self.prices(prd_dict, item_color, **kwargs)

            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _sizes(self, prd_dict, item_color, **kwargs):
        product_ids = '%2C'.join([p_id['id'] for p_id in prd_dict['product']['variations']])
        ajax_url = 'https://www.toryburch.com/api/prod-r2/v11/products/inventoryStatuses?site=ToryBurch_US&pip=true&productIds=%s'%product_ids
        headers = {
            'x-api-key': 'yP6bAmceig0QmrXzGfx3IG867h5jKkAs',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        size_json = requests.get(ajax_url, headers=headers)
        size_dict = json.loads(size_json.text)

        item_color['originsizes'] = []
        for prd_info in prd_dict['product']['variations']:
            if prd_info['values']['color'] != item_color['sku'].split('_')[1]:
                continue
            for size_status in size_dict['inventoryStatuses']:
                if size_status['productId'] == prd_info['id']:
                    if size_status['inventoryStatus']['value'] != 'SOLD_OUT':
                        item_color['originsizes'].append(prd_info['values']['size'])

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="product-image__thumbnail-list"]/div/img/@src').extract()
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append(img)

        return img_li

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[@data-product-list="styled-with"]//div[@data-id="ProductTile"]/@data-product-id').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        cover = response.xpath('//div[contains(@class,"js-show-image-viewer")]//img/@src').extract()
        if len(cover)>2:
            item['cover'] = cover[-2]

        item['main_prd'] = response.url

        item['products']= [(str(x).split('?')[0]) for x in outfits]
        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url.replace('page=1','page=%s'%str(i))
        return url

    def _blog_page_num(self, data, **kwargs):
        page_num = 1
        return page_num

    def _parse_blog(self, response, **kwargs):
        title = ''.join(response.xpath('//h2//text()').extract())
        html_origin = response.xpath('//div[contains(@class,"postTemplate")]').extract_first().encode('utf-8')
        key = response.url.split('=')[-1]
        cover = response.xpath('//div[contains(@class,"postTemplate")]/div[@class="postImage"]/img/@src').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        for node in response.xpath('//div[contains(@class,"postTemplate")]/*'):
            if node.xpath('./@class').extract_first() == 'postImage':
                images = {"type": "image","alt": ""}
                image = node.xpath('.//img/@src').extract_first()
                images['src'] = image
                html_parsed['items'].append(images)

                if node.xpath('./*[@class="postBody"]').extract_first():
                    text = node.xpath('./*[@class="postBody"]/p').extract_first()
                    if text:
                        texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                        texts['value'] = text
                        html_parsed['items'].append(texts)

            if node.xpath('./@class').extract_first() == 'postBody':
                # text = ''.join(node.xpath('./text() | ./a').extract())
                # texts = {"type": "html"}
                # texts['value'] = text
                # html_parsed['items'].append(texts)

                text = ''.join(node.xpath('./text() | ./a | ./span/span/text() | ./span/span/a').extract())
                if text:
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text
                    html_parsed['items'].append(texts)

                text = ''.join(node.xpath('./strong/span/span/text()').extract())
                if text:
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text
                    html_parsed['items'].append(texts)

                text = ''.join(node.xpath('./span/text()').extract())
                if text:
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text
                    html_parsed['items'].append(texts)

                text = ''.join(node.xpath('./div/span[@data-contrast="auto"]/span/text()').extract())
                if text:
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text
                    html_parsed['items'].append(texts)

                txts = node.xpath('./p | ./div[not(@class="postImage")]/a | ./div[not(@class="postImage")]/p | ./h3 | ./div[not(@class="postImage")]/div/p | ./div[not(@class="postImage")]/div/strong | ./div[not(@class="postImage")]/div/text() | ./div[not(@class="postImage")]/strong').extract()
                for txt in txts:
                    if txt.strip():
                        texts = {"type": "html"} if '<a' not in txt else {"type": "html_ext"}
                        texts['value'] = txt.strip()
                        html_parsed['items'].append(texts)

                imgs = node.xpath('./div[@class="postImage"]/div[@class="postImage"]/img/@src | ./div[@class="postBody"]/div[@class="postImage"]/img/@src | ./div[@class="postImage"]/div[@class="postImage"]/div[@class="postImage"]/img/@src').extract()
                for img in imgs:
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images)

                imgs = node.xpath('./div[@class="postImage"]')
                for img in imgs:
                    images = {"type": "image","alt": ""}
                    images['src'] = img.xpath('./img/@src').extract_first()
                    html_parsed['items'].append(images)

                    texts = {"type": "html"}
                    texts['value'] = ''.join(img.xpath('./div[@class="wp-caption-text"]/text() | ./div[@class="wp-caption-text"]/a').extract())
                    html_parsed['items'].append(texts)


                txts = node.xpath('./div[@class="postImage"]/div[@class="postImage"]/div[@class="postBody"]/p').extract()
                for txt in txts:
                    if txt.strip():
                        texts = {"type": "html"} if '<a' not in txt else {"type": "html_ext"}
                        texts['value'] = txt
                        html_parsed['items'].append(texts)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json
            

_parser = Parser()



class Config(MerchantConfig):
    name = 'toryburch'
    merchant = 'TORY BURCH'
    url_split = False
    headers = {
    'x-api-key':' yP6bAmceig0QmrXzGfx3IG867h5jKkAs',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p/text()',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            list_url = _parser.list_url,
            # items = '//div[@class="searchresults"]/div//a[@class="product-tile__thumb"]',
            # designer = '//a/text',
            # link = './@href',
            ),
        product = OrderedDict([
            
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=4056,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="longDescription"]/ul/li/text()',
            ),
        blog = dict(
            official_uid = 4056,
            blog_page_num = ('//html', _parser.blog_page_num),
            blog_list_url = _parser.blog_list_url,
            link = '//ul[@class="blogThumbnails"]/li/a[1]/@href',
            # json_blog_links = _parser.json_blog_links,
            method = _parser.parse_blog,
            ),
        )
    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        m = dict(
        ),
        f = dict(
            a = [
                'https://www.toryburch.com/api/prod-r2/v4/categories/accessories-belts/products?site=ToryBurch_US&limit=12&offset=0',
                "https://www.toryburch.com/api/prod-r2/v4/categories/accessories-small-accessories/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/accessories-hats-scarves-gloves/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/accessories-jewelry/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/accessories-wallets-small-accessories/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/accessories-eyewear/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/accessories-tech-accessories/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/accessories-sale/products?site=ToryBurch_US&limit=12&offset=0"
            ],
            b = [
                "https://www.toryburch.com/api/prod-r2/v4/categories/handbags-view-all/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/shops-minibags/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/handbags-sale/products?site=ToryBurch_US&limit=12&offset=0"
            ],
            c = [
                "https://www.toryburch.com/api/prod-r2/v4/categories/clothing-view-all/products?site=ToryBurch_US&limit=12&offset=0",
                "https://www.toryburch.com/api/prod-r2/v4/categories/clothing-sale/products?site=ToryBurch_US&limit=12&offset=0"
            ],
            s = [
                # 'https://www.toryburch.com/shoes/view-all/',
                # 'https://www.toryburch.com/sale-shoes/',
                'https://www.toryburch.com/api/prod-r2/v4/categories/shoes-view-all/products?site=ToryBurch_US&limit=12&offset=0',
                'https://www.toryburch.com/api/prod-r2/v4/categories/shoes-sale/products?site=ToryBurch_US&limit=12&offset=0',
            ],
            e = [
                'https://www.toryburch.com/api/prod-r2/v4/categories/beauty-view-all/products?site=ToryBurch_US&limit=12&offset=0'
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    blog_url = dict(
        EN = [
            'https://www.toryburch.com/blog/torys-blog-style-landing.html?page=1&format=ajax'
        ]
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '.com/',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        # JP = dict(
        #     currency = 'JPY',
        #     country_url = '.jp/',
        #     currency_sign = u'\u00a5',
        #     translate = [
        #         ('shoes/view-all/','%E3%82%B7%E3%83%A5%E3%83%BC%E3%82%BA/%E5%85%A8%E3%81%A6%E3%82%92%E8%A6%8B%E3%82%8B/'),
        #         ('handbags/view-all/', '%E3%83%90%E3%83%83%E3%82%B0/%E5%85%A8%E3%81%A6%E3%82%92%E8%A6%8B%E3%82%8B/'),
        #         ('accessories/view-all','accessories-viewall'),
        #         ]
        # ),
        # GB = dict(
        #     currency = 'GBP',
        #     country_url = '.co.uk/',
        #     currency_sign = u'\xa3'
        # ),

        # DE = dict(
        #     language = 'DE', 
        #     currency = 'EUR',
        #     country_url = '.de/',
        #     area = 'DE',
        #     translate = [
        #         ('clothing', 'kleidung'),
        #         ('view-all', 'alle-anzeigen'),
        #         ('shoes','schuhe'),
        #         ('handbags', 'taschen'),
        #         ('accessories','accessoires'),
        #     ]
        # ),
        )

        


