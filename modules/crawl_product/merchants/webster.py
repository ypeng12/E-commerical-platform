from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        instock = checkout.xpath('//button[@title="Add to Cart"]')
        outstock = checkout.xpath('//button[@title="Out of stock"]')
        if instock and not outstock:
            return False
        else:
            return True

    def _page_num(self, count, **kwargs):
        page_num = int(float(count) / 24) + 1
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('p=100','p=%s'%i)
        return url

    def _sku(self, data, item, **kwargs):
        code = data.extract_first()
        item['sku'] = code.strip().upper() if code else ''

    def _images(self, script, item, **kwargs):
        img_dict = json.loads(script.extract_first().split('slider(')[-1].split(', sliderContext')[0])
        images = []
        for img in img_dict['data']:
            images.append(img['img'])
        item['cover'] = images[0]
        item['images'] = images
        
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

    def _sizes(self, data, item, **kwargs):
        final_sale = data.xpath('.//ul[@class="product-tags"]/li/text()').extract()
        memo = ':f' if final_sale and 'Final Sale' in final_sale else ''
        size_li = []
        script = data.xpath('.//script[contains(text(),"jsonSwatchConfig")]/text()').extract_first()
        if script:
            size_dict = json.loads(script)
            sizes = list(size_dict['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']['attributes'].values())[0]['options']
            for size in sizes:
                if not size['products']:
                    continue
                size_li.append(size['label'] + memo)
        else:
            size_li = ['One Size']

        item['originsizes'] = size_li
        if item['category'] in ['a','b','e'] and not size_li:
            size_li.append('IT' + memo)
            item['originsizes'] = size_li

    def _prices(self, res, item, **kwargs):
        saleprice = res.xpath('.//span[@data-price-type="finalPrice"]/text()').extract()[0]
        if not saleprice.replace('$', '').isalnum():
            saleprice = res.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0]
        listprice = res.xpath('.//span[@data-price-type="oldPrice"]/span/text()').extract_first()

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="owl-carousel-gallery"]//img/@src').extract()
        if not imgs:
            imgs = response.xpath('//div[@class="product item-image base-image"]/img/@src').extract()
        img_li = [x.replace('width=120','width=900').replace('height=160','height=1200') for x in imgs]
        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower() or 'inches' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//article[@class="blog-posts-post blog-post"]/header/div/h1/text()').extract_first().strip()
        key = response.url.split('?')[0].split('/')[-1]
        html_origin = response.xpath('//article[@class="blog-posts-post blog-post"]').extract_first().encode('utf-8')
        cover = response.xpath('//article[@class="blog-posts-post blog-post"]//img/@src').extract_first()

        img_li = []
        html_parsed = {
            "type": "article",
            "items": []
        }
        products = {"type": "products","pids":[]}

        # header = response.xpath('//article[@class="blog-posts-post blog-post"]/header/div/h1/text()').extract_first()
        # if header:
        #     headers = {"type": "header"}
        #     headers['value'] = header
        #     html_parsed['items'].append(headers)

        for node in response.xpath('//article[@class="blog-posts-post blog-post"]/div[@class="blog-post-content"]/div[@*="row"]/div//*'):
            node_type = node.xpath('./@data-role | ./@data-content-type').extract_first()
            if node_type in ['image']:
                images = {"type": "image","alt": ""}
                imgs = node.xpath('.//img/@src').extract()
                for img in imgs:
                    if img not in img_li and '/product/' not in img:
                        images['src'] = img
                        html_parsed['items'].append(images)
                        img_li.append(img)

            elif node_type in ['column-group']:
                for node in node.xpath('./div/*'):
                    node_sub_type = node.xpath('./@data-role').extract_first()
                    if node_sub_type == 'text':
                        text = node.xpath('./p').extract_first()
                        if text:
                            if '<a' in text:
                                links = etree.HTML(text).xpath('//a/@href')
                                for link in set(links):
                                    if 'http' not in link:
                                        text = text.replace(link, 'https://thewebster.us/' + link)
                            texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                            texts['value'] = text
                            html_parsed['items'].append(texts)
                    elif node_sub_type == 'image':
                        images = {"type": "image","alt": ""}
                        imgs = node.xpath('.//img/@src').extract()
                        for img in imgs:
                            if img not in img_li:
                                images['src'] = img
                                html_parsed['items'].append(images)
                                img_li.append(img)
                    elif node_sub_type == 'heading':
                        header = node.xpath('./text()').extract_first()
                        if header:
                            headers = {"type": "header"}
                            headers['value'] = header
                            html_parsed['items'].append(headers)

                for img in node.xpath('./div'):
                    images = {"type": "image","alt": ""}
                    img = img.xpath('.//img/@src').extract_first()
                    if img not in img_li:
                        images['src'] = img
                        html_parsed['items'].append(images)
                        img_li.append(img)

            elif node_type in ['text']:
                text = ''.join(node.xpath('.//p').extract())
                if text:
                    if '<a' in text:
                        links = etree.HTML(text).xpath('//a/@href')
                        for link in set(links):
                            if 'http' not in link:
                                text = text.replace(link, 'https://thewebster.us' + link)
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text
                    html_parsed['items'].append(texts)
                header = node.xpath('./h2/span/strong/text()').extract_first()
                if header:
                    headers = {"type": "header"}
                    headers['value'] = header
                    html_parsed['items'].append(headers)

            elif node_type in ['html']:
                links = node.xpath('.//a[contains(@class,"product-item-photo")]/@href').extract()
                for link in links:
                    prod = parseProdLink(link)                    
                    for product in prod[0]:
                        pid = product.id
                        if pid not in products['pids']:
                            products['pids'].append(pid)
                if products['pids'] and products not in html_parsed['items']:
                    html_parsed['items'].append(products)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json 

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@id="toolbar-amount"]/span[last()]/text()').extract_first().strip().replace('"','').replace(',','').lower())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'webster'
    merchant = 'THE WEBSTER'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="toolbar-number"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@class="item product product-item"]/div',
            designer = './/div[@class="product manufacturer product-item-manufacturer"]/text()',
            link = './a[@class="product photo product-item-photo"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//form/@data-product-sku', _parser.sku)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('designer', '//*[@class="product attribute manufacturer"]/a/text()'),
            ('images', ('//script[contains(text(),"mage/gallery/gallery")]/text()', _parser.images)),
            ('description', ('//div[@class="product attribute description"]//p/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="product-info-price"]', _parser.prices))
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
            size_info_path = '//p[contains(text(),"Dimensions")][1]/text()',
            ),
        blog = dict(
            official_uid = 27888,       
            blog_page_num = '//div[@class="blog-pagination"]/a[last()-1]/span/text()',
            link = '//div[@class="blog-posts"]/article/div/a/@href',            
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    blog_url = dict(
        EN = [
            'https://thewebster.us/play/the-webster-way?p=',
            'https://thewebster.us/play/must-read?p='
        ]
    )

    list_urls = dict(
        m = dict(
            a = [
                "https://thewebster.us/shop/men/jewelry.html?p=100",
                "https://thewebster.us/shop/men/accessories.html?p=100"
            ],
            b = [
                "https://thewebster.us/shop/men/bags.html?p=100"
            ],
            c = [
                "https://thewebster.us/shop/men/clothing.html?p=100"
            ],
            s = [
                "https://thewebster.us/shop/men/shoes.html?p=100",
            ],
        ),
        f = dict(
            a = [
                "https://thewebster.us/shop/women/jewelry.html?p=100",
                "https://thewebster.us/shop/women/accessories.html?p=100",
            ],
            b = [
                "https://thewebster.us/shop/women/bags.html?p=100",
            ],
            c = [
                "https://thewebster.us/shop/women/clothing.html?p=100",
            ],
            s = [
                "https://thewebster.us/shop/women/shoes.html?p=100"
            ],

        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
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
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        )
        )

        


