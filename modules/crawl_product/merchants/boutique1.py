from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *
import requests
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page = int(data) / 12 + 1
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?p=' + str(i) + '&ajax=1'
        return url

    def _color(self, data, item, **kwargs):
        item['color'] = data.extract_first().upper() if data.extract_first() else ''

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        json_dict = json.loads(sku_data)
        sku = json_dict['data']['product']
        item['sku'] = str(sku)
        if item['sku'].isdigit():
            item['sku'] = item['sku'].strip()
        else:
            item['error'] = "Missing sku"

    def _images(self, scripts, item, **kwargs):
        for script in scripts.extract():
            if 'list_img' in script:
                json_dict = json.loads(script)
                break
        images_list = json_dict['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        img_li = []
        for img in images_list:
            img_li.append(img['list_img'])
            if '_1' in img['list_img']:
                item['cover'] = img['list_img']
        item['images'] = img_li
        
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

    def _sizes(self, scripts, item, **kwargs):
        for script in scripts.extract():
             if 'jsonSwatchConfig' in script:
                json_data = script
                break
        try:        
            json_str = json_data.split('jsonSwatchConfig:')[-1].split('mediaCallback')[0].strip()[:-1]
            json_dict = json.loads(json_str)
            values = list(json_dict.values())[0].values()
            originsizes = []
            for value in values:
                size = value['value']
                if 'sold' in size.lower() or 'select' in size.lower():
                    continue
                originsizes.append(size)
        except:
            originsizes = ''
        size_li = []
        if item['category'] in ['a','b']:
            if not originsizes:
                size_li.append('IT')
            else:
                size_li = originsizes
        elif item['category'] == 'c':
            for size in originsizes:
                size_li.append(size.replace('GLOBAL', '').strip())
        elif item['category'] == 's':
            size_li = originsizes
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('//span[@id="product-price-%s"]/span/text()'%item['sku']).extract_first()
        listPrice = prices.xpath('//span[@id="old-price-%s"]/span/text()'%item['sku']).extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice

    def _parse_item_url(self, response, **kwargs):
        json_data = json.loads(response.body)
        html = json_data['html']['content']
        html = etree.HTML(html)
        items = html.xpath('//li[@class="item product product-item"]')
        for item in items:
            href = item.xpath('.//a/@href')[0]
            designer = item.xpath('.//h4[@class="product-item-brand"]/text()')[0].strip()
            yield href,designer

    def _parse_images(self, response, **kwargs):
        for script in response.xpath('//script[@type="text/x-magento-init"]/text()').extract():
            if 'list_img' in script:
                json_dict = json.loads(script)
                break
        images_list = json_dict['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        img_li = []
        for img in images_list:
            img_li.append(img['list_img'])
        return img_li

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[@class="block upsell"]//div/@data-product-id').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.meta.get('sku')
        for script in response.xpath('//script[@type="text/x-magento-init"]/text()').extract():
            if 'list_img' in script:
                json_dict = json.loads(script)
                break
        images_list = json_dict['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        img_li = []
        for img in images_list:
            img_li.append(img['list_img'])
        if img_li:
            item['cover'] = img_li[0]

        item['products']= [(str(x).split('/?')[0].split('/')[-1]) for x in set(outfits)]

        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = []
        infos = response.xpath('//td[@data-th="Fit & Care"]/br/preceding-sibling::p/text()').extract()
        if not infos:
            infos = response.xpath('//td[@data-th="Fit & Care"]/p/text()').extract()
        details = response.xpath('//td[@data-th="Details"]/br/following-sibling::p/text()').extract()
        model_info = ''
        for detail in details:
            if 'model' in detail:
                model_info = detail.strip()
        fits = []
        for info in infos:
            if 'Shell' in info or 'Lining' in info or 'Professiona' in info:
                continue
            fits.append(info)
        if model_info:
            fits.append(model_info)
        size_info = '\n'.join(fits)
        return size_info  

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _json_blog_links(self, response, **kwargs):
        urls = self.parse_blog_urls(response)
        return urls
        
    def parse_blog_urls(self, response):
        prds_dict = json.loads(response.text)
        parse_urls = []
        for story in prds_dict['Feed']['stories']:
            url = 'https://www.boutique1.com/magazine/' + story['categories'][0]['slug'] + '/' + story['slug'] if story['categories'] else ''
            if url:
                parse_urls.append(url)
        next_url = 'https://redpanda.styla.com/v1/feed/latest/boutique1-uk?limit=9&offset=%s'%prds_dict['Feed']['meta']['navigation']['next'] if prds_dict['Feed']['meta']['navigation'].get('next', '') else ''
        if next_url:
            return parse_urls + self.parse_blog_urls(requests.get(next_url))
        else:
            return parse_urls

    def _parse_blog(self, response, **kwargs):
        blog_url = 'https://redpanda.styla.com/v1/story/boutique1-uk/' + response.url.split('?')[0].split('/')[-1]
        res = requests.get(blog_url)
        blog_info = json.loads(res.text)

        title = blog_info['title']
        html_origin = json.dumps(blog_info).encode('utf-8')
        key = response.url.split('?')[0].split('magazine/')[-1]
        cover = blog_info['leadImage']['url']

        html_parsed = {
            "type": "article",
            "items": []
        }
        images = {"type": "image","alt": ""}

        text = blog_info['introText']
        texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
        texts['value'] = text
        html_parsed['items'].append(texts)

        image = blog_info['leadImage']['url']
        images['src'] = image
        html_parsed['items'].append(images)
        last_type = None

        for element in blog_info['elements']:
            if element['type'] == 'paragraph':
                content = element['content']
                if '<b>' in content:
                    header = content.replace('<b>', '').replace('&nbsp;', '').strip()
                    if header:
                        headers = {"type": "header"}
                        headers['value'] = header
                        html_parsed['items'].append(headers)
                else:
                    text = content.strip()
                    if text:
                        texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                        texts['value'] = text
                        html_parsed['items'].append(texts)

            if element['type'] == 'image':
                images = {"type": "image","alt": ""}
                image = element['url']
                images['src'] = image
                html_parsed['items'].append(images)

            if element['type'] == 'products':
                if last_type == 'products':
                    pass
                else:
                    products = {"type": "products","pids":[]}
                for prd in element['products']:
                    link = prd['shopUrl']
                    prod = parseProdLink(link)                    
                    for product in prod[0]:
                        pid = product.id
                        if pid not in products['pids']:
                            products['pids'].append(pid)
                if products not in html_parsed['items']:
                    html_parsed['items'].append(products)

            last_type = element['type']

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="toolbar-number"]/text()').extract_first().strip())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'boutique1'
    merchant = 'Boutique 1'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="toolbar-number"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            # items = '//ol[@class="products list items product-items"]/li',
            # designer = 'normalize-space(.//h4/text())',
            # link = './li/div/div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="product-addtocart-button"]', _parser.checkout)),
            ('sku', ('//a[@class="action towishlist tertiary"]/@data-post',_parser.sku)),
            ('name', '//span[@class="base"]/text()'),
            ('designer', 'normalize-space(//div[@class="product attribute brand"])'),
            ("color" , ('//div[@class="product attribute detail"]/p[2]/text()', _parser.color)),
            ('images', ('//script/text()', _parser.images)),
            ('description', ('//div[@class="product attribute detail"]//text()',_parser.description)),
            ('sizes', ('//script/text()', _parser.sizes)), 
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=74474,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//html',
            ),
        blog = dict(
            official_uid = 74474,
            blog_list_url = _parser.blog_list_url,
            json_blog_links = _parser.json_blog_links,
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    blog_url = dict(
        EN = [
            'https://redpanda.styla.com/v1/feed/latest/boutique1-uk?limit=9'
        ]
    )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.boutique1.com/men/accessories/scarves',
                'https://www.boutique1.com/men/accessories/jewellery',
                'https://www.boutique1.com/men/accessories/sunglasses'
            ],
            b = [
            ],
            c = [
                'https://www.boutique1.com/men/clothing',
                'https://www.boutique1.com/men/accessories/socks'
            ],
            s = [
                'https://www.boutique1.com/men/shoes',
            ],
        ),
        f = dict(
            a = [
                'https://www.boutique1.com/women/accessories/belts',
                'https://www.boutique1.com/women/accessories/sunglasses',
                'https://www.boutique1.com/women/jewellery'
            ],
            b = [
                'https://www.boutique1.com/women/bags',
            ],
            c = [
                'https://www.boutique1.com/women/clothing'
            ],
            s = [
                'https://www.boutique1.com/women/shoes',
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
            language = 'EN', 
            currency = 'USD',
            cookies = {
                'store':'en_usd',
                'shipping_code':'US',
                'X-Magento-Vary':'218f434f56a08054335d1498657667407378ddfc'
            }
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            cookies = {
                'store':'en_usd',
                'shipping_code':'CN',
                'X-Magento-Vary':'78e27ba5b8a8ca0be136694411d0134c91a48b62'
            }
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            cookies = {
            'store':'en_usd',
            'shipping_code':'JP',
            'X-Magento-Vary':'caccc9325882b933c290523a4487fe290121d2d'
            }
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            cookies = {
                'store':'en_usd',
                'shipping_code':'KR',
                'X-Magento-Vary':'a158c09bf92e93a207ef7b5076ef05a008d74b33'
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            cookies = {
            'store':'en_usd',
            'shipping_code':'SG',
            'X-Magento-Vary':'da486f38e9dfe562a5c921a11599d16aace91553'
            }
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            cookies = {
            'store':'en_usd',
            'shipping_code':'HK',
            'X-Magento-Vary':'faeaeb3889735419baf5f8752e2caf653ec7e960'
            }
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = {
            'store':'gb_en',
            'shipping_code':'GB',
            'X-Magento-Vary':'b624c0b17ce2aba74965bedc62d4ac48b3618ef4',
            }
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            cookies = {
            'store':'en_usd',
            'shipping_code':'RU',
            'X-Magento-Vary':'2720e63a2c0e60f5b9ba26d487392fd693999e6c'
            }
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            cookies = {
            'store':'en_usd',
            'shipping_code':'CA',
            'X-Magento-Vary':'bb31946676bcc42024b3f83f2bbc01129a204dc4'
            }
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            cookies = {
            'store':'en_usd',
            'shipping_code':'AU',
            'X-Magento-Vary':'1a9345eb9a7ba0ccb94d023d15f16994ac9a661c'
            }
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {
            'store':'en_eur',
            'shipping_code':'DE',
            'X-Magento-Vary':'d7fe8cd0e3aff62ee56b9243a2c90d396bab7514'
            }
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {
            'store':'en_eur',
            'shipping_code':'NO',
            'X-Magento-Vary':'e9f4b65fc284acdc3ee1203927189ee6aaba4937'
            }
        ),

        )

        


