from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import requests
import json
from urllib.parse import urljoin
from utils.ladystyle import blog_parser,parseProdLink
from utils.extract_helper import *

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = int(data.strip().replace(',',''))/60 + 1
        return pages

    def _checkout(self, checkout, item, **kwargs):
        add_to_bag = checkout.xpath('.//button[@data-action="add-to-bag"] | //button[text()="Add to bag"]')
        sold_out = checkout.xpath('.//div[@class="outofstock"]')
        if not add_to_bag or sold_out:
            return True
        else:
            return False

    def _images(self, data, item, **kwargs):
        color = item['url'].split('previewAttribute=')[-1] if 'previewAttribute' in item['url'] else ''
        item['color'] = color.replace('%20', ' ').replace('%2F', '/').replace('%2B', '+') if color else ''
        path_rule = './/span[@data-js-action="%s"]/div/img/@src' %item['color']
        img = data.xpath(path_rule).extract_first()

        if not img:
            path_rule = './/span[@data-js-action="%s"]/div/img/@src | .//div[@class="c-select__icon"]/img[contains(@src,"%s")]/@src | .//meta[@property="og:image"]/@content'%(item['color'],item['color'].replace(' ','').replace('/','').replace('+','')) if color else './/meta[@property="og:image"]/@content'

            img = data.xpath(path_rule).extract_first()

        if img and '/selfridges/' in img and img.split('?')[0][-3:] == '_SW':
            sku = img.split('?')[0].split('/selfridges/')[-1][:-3]
        elif img and '/selfridges/' in img and img.endswith('_M'):
            sku = img.split('/selfridges/')[-1][:-2]
            img = img + '?$PDP_M_ZOOM$'
        else:
            sku = ''
        item['sku'] = kwargs['sku'] if 'sku' in kwargs else sku

        cover = 'https:' + img.replace('_SW?$PDP_SWATCH$','_M?$PDP_M_ZOOM$') if 'http' not in img else img
        try:
            serialized_data = urllib.request.urlopen(cover).read()
            images = [cover]
        except:
            cover = cover.replace('_M?', '_ALT10?')
            try:
                serialized_data = urllib.request.urlopen(cover).read()
                images = [cover]
            except:
                images = []
        
        for i in range(4):
            try:
                img_url = cover.replace('_ALT10?', '_ALT0%s?' % (i+1)).replace('_M?$PDP_M_ZOOM$', '_ALT0%s?$PDP_M_ZOOM$' % (i+1))
                serialized_data = urllib.request.urlopen(img_url).read()
                images.append(img_url)
            except:
                break
        item['images'] = images
        item['cover'] = images[0] if images else ''

    def _description(self,desc, item, **kwargs):
        descs = desc.extract()
        desc_li = []
        for des in descs:
            des = des.strip()
            if 'Size & Fit' in des:
                break
            if des and des not in desc_li:
                desc_li.append(des)
        item['description'] = '\n'.join(desc_li)

    def _sizes(self, data, item, **kwargs):
        if not item['color']:
            item['color'] = data.xpath('//div[@class="c-select c-filter__select --colour"]//span[@class="c-select__dropdown-item"]/@data-js-action').extract_first()
        item['color'] = item['color'].replace('%20', ' ') if item['color'] else ''
        headers = {
            'api-key': 'xjut2p34999bad9dx7y868ng',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        originsizes = []
        skuids = []
        if item['color']:
            color_id = item['color'].replace(' ', '%20').replace('/', '%2F').replace('+', '%2B')
            url = 'https://www.selfridges.com/api/cms/ecom/v1/US/en/stock/byId/%s?option=SupplierColourName&optionValue=%s' %(item['sku'].split('_')[0], color_id)
        else:
            url = 'https://www.selfridges.com/api/cms/ecom/v1/US/en/stock/byId/%s' %item['sku'].split('_')[0]
        res = getwebcontent(url, headers=headers)
        prd_stocks = json.loads(res)
        stocks = prd_stocks['stocks'] if prd_stocks else {}
        if item['category'] in ['c','s']:
            for size in stocks:
                if size['Stock Quantity Available to Purchase'] == '0':
                    continue
                osize = size['value'].replace('EUR','EU')
                if osize.replace('.','').isdigit() and float(osize) < 20:
                    osize = 'UK ' + osize
                originsizes.append(osize)
                skuids.append(size['SKUID'])
        elif item['category'] in ['a', 'b', 'e']:
            if item['color']:
                for prd in stocks:
                    if prd['value'].lower().replace('/','') == item['color'].lower().replace(' ',''):
                        if prd['Stock Quantity Available to Purchase'] != '0':
                            originsizes = ['IT']
                            skuids.append(size['SKUID'])
            else:
                if stocks[0]['Stock Quantity Available to Purchase'] != '0':
                    originsizes = ['IT']
                    skuids.append(size['SKUID'])
            originsizes = originsizes if originsizes else ['IT']
        item['originsizes'] = originsizes
        item['tmp'] = skuids

    def _prices(self, prices, item, **kwargs):
        try:
            headers = {
                'api-key': 'xjut2p34999bad9dx7y868ng',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
            }
            url = 'https://www.selfridges.com/api/cms/ecom/v1/%s/en/price/byId/%s'%(item['country'],item['sku'].split('_')[0])
            data = json.loads(getwebcontent(url, headers=headers))

            for price in data['prices']:
                if price['SKUID'] in item['tmp']:
                    default_saleprice = price['Current Retail Price']
                    default_listprice = price['Current Retail Price'] if 'Was Retail Price' in price else default_saleprice
                    break

            for price in data['prices']:
                if price['SKUID'] in item['tmp']:
                    saleprice = price['Current Retail Price']
                    listprice = price['Was Retail Price'] if 'Was Retail Price' in price else saleprice
                    if float(default_saleprice) > float(saleprice):
                        default_saleprice = saleprice
                        default_listprice = price['Was Retail Price'] if 'Was Retail Price' in price else saleprice

            item['originsaleprice'] = default_saleprice
            item['originlistprice'] = default_listprice
        except:
            try:
                saleprice = prices.xpath('.//span[@class="now-price"]/span//text()').extract()[0]
                listprice = prices.xpath('.//span[@class="now-price"]/span//text()').extract()[0]
            except:
                saleprice = prices.xpath('.//span[@data-js-action="updatePrice"]/text()').extract_first()
                listprice = prices.xpath('.//span[@class="reduced_price_one"]/text()').extract_first()

            item['originsaleprice'] = saleprice
            item['originlistprice'] = listprice if listprice else saleprice

    def _parse_images(self, response, **kwargs):
        path_rule = '//div[@class="c-select__icon"]/img[contains(@src,"%s")]/@src' %kwargs['sku']

        img = response.xpath(path_rule).extract_first()

        if not img:
            img = response.xpath('//meta[@property="og:image"]/@content').extract_first()
            img = img + '?$PDP_M_ZOOM$' if '?' not in img else img

        cover = 'https:' + img.replace('_SW?$PDP_SWATCH$','_M?$PDP_M_ZOOM$') if 'http' not in img else img
        try:
            serialized_data = urllib.request.urlopen(cover).read()
            images = [cover]
        except:
            cover = cover.replace('_M?', '_ALT10?')
            try:
                serialized_data = urllib.request.urlopen(cover).read()
                images = [cover]
            except:
                images = []

        for i in range(4):
            try:
                img_url = cover.replace('_ALT10?', '_ALT0%s?' % (i+1)).replace('_M?$PDP_M_ZOOM$', '_ALT0%s?$PDP_M_ZOOM$' % (i+1))
                serialized_data = urllib.request.urlopen(img_url).read()
                images.append(img_url)
            except:
                break

        return images

    def _parse_swatches(self, response, swatch_path, **kwargs):
        current_pid = response.xpath(swatch_path['current_path']).extract()
        datas = response.xpath(swatch_path['path'])
        if len(datas) < 2:
            return
        swatches = []
        for data in datas:
            pid = current_pid[0] + data.xpath('./@alt').extract()[0].upper()
            swatches.append(pid)
        return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if '<li>' in info or '<BR />' in info:
                info = info.replace('</li>','#').replace('<li>','#').replace('<BR />','#').replace('<ul>','#').replace('</ul>','#')
                info = info.split('#')
                for ifo in info:
                    if ifo and ifo.strip() not in fits and ('length' in ifo.lower() or 'cm' in ifo.lower() or 'model' in ifo.lower() or '"' in ifo or 'height' in ifo.lower()):
                        fits.append(ifo.strip())
            else:
                if info and info.strip() not in fits and ('length' in info.lower() or 'cm' in info.lower() or 'model' in info.lower() or '"' in info or 'height' in info.lower()):
                    fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _json_blog_links(self, response, **kwargs):
        urls = []
        tags = response.xpath('//div[@class="paragraphSystem content"]')

        for tag in tags:
            if tag.xpath('.//div[@class="richText-content"]/h3/text()').extract_first() not in ['FASHION & STYLE' ,'BEAUTY', 'INSPIRING CHANGE']:
                continue
            tag_urls = tag.xpath('.//div[@class="articleList-article-wrapper"]/a/@href').extract()
            urls = urls + tag_urls

        return urls

    def _parse_blog(self, response, **kwargs):
        # title = response.xpath('//li[@class="odd last is-current "]/text()').extract_first().strip()
        key = response.url.split('?')[0].split('articles')[-1]
        html_origin = response.xpath('//div[@class="content-paragraph paragraphSystem"]').extract_first().encode('utf-8')
        cover = response.xpath('//div[@class="image component section col-xs-12 image-full-width show-on-mobile"]//img/@src').extract_first()
        check_cover = cover
        if cover:
            cover = urljoin(response.url, cover)
        else:
            cover = ''

        html_parsed = {
            "type": "article",
            "items": []
        }

        header_set = []
        imgs_set = []
        text_set = ["<h3><strong>like what you see? try these...</strong></h3>", '<h3 style="text-align: center;">beauty talking points</h3>']
        start = False

        imgs_set = imgs_set + list([urljoin(response.url, x) for x in response.xpath('//img[@class="carousel-cover"]/@src | //ul[@class="carousel-slides owl-loaded owl-drag"]//img/@src | //li[@class="carousel-slide clearfix odd is-active first "]//img/@src').extract()])
        for ignor in response.xpath('//div[@class="content-paragraph paragraphSystem"]/div/div//div[contains(@class,"component section")]'):
            if ignor.xpath('.//a[contains(text(),"Read & shop")]').extract_first():
                imgs = ignor.xpath('.//img/@src').extract()
                for img in imgs:
                    image = urljoin(response.url, img)
                    imgs_set.append(image)
                headers = ignor.xpath('.//h1').extract()
                text_set = text_set + list([x.lower().strip() for x in headers])
                htmls = ignor.xpath('.//h5 | .//h3 | .//p').extract()
                text_set = text_set + list([x.lower().strip() for x in htmls])

        for node in response.xpath('//div[@class="content-paragraph paragraphSystem"]/div/div//div[contains(@class,"component section") and not(contains(@class,"show-on-mobile"))]/div/*'):


            imgs = node.xpath('.//img/@src').extract()
            if (all([check_cover,imgs]) and check_cover in imgs) or not check_cover:
                start = True
            if not start:
                continue
            for img in imgs:
                images = {"type": "image","alt": ""}
                image = urljoin(response.url, img)
                if image not in imgs_set:
                    images['src'] = image
                    html_parsed['items'].append(images)
                    imgs_set.append(image)
            header = ' '.join(list([x.lstrip() for x in node.xpath('.//h1//text()').extract()])).replace('  ', ' ')
            if header:
                if not header_set:
                    header_set.append(header.lower().strip())
                    title = header
                else:
                    headers = {"type": "header"}
                    headers['value'] = header
                    if header.lower().strip() not in header_set:
                        header_set.append(header.lower().strip())
                        html_parsed['items'].append(headers)
                # if headers not in html_parsed['items']:
            ignore_htmls = response.xpath('//div[@class="carousel-content"]//h5 | //div[@class="carousel-content"]//h3 | //div[@class="carousel-content"]//p').extract()
            htmls = node.xpath('.//h5 | .//h3 | .//p').extract()
            for text in htmls:
                if text in ignore_htmls:
                    continue
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text
                if text.lower().strip() not in text_set:
                    text_set.append(text.lower().strip())
                    html_parsed['items'].append(texts)

            links = node.xpath('.//ul[@class="carousel-slides"]//div[@class="image-and-content"]/a/@href').extract()
            products = {"type": "products","pids":[]}
            for link in [urljoin(response.url, x) for x in links]:
                prod = parseProdLink(link)
                if prod[0]:
                    for product in prod[0]:
                        pid = product.id
                        products['pids'].append(pid)
            if products['pids']:
                html_parsed['items'].append(products)
                
        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])
        return title, cover, key, html_origin, html_parsed, item_json
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@data-total-products-count]/@data-total-products-count').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'self'
    merchant = 'Selfridges'
    url_split = False
    merchant_headers = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@data-total-products-count]/@data-total-products-count', _parser.page_num),
            items = '//div[@data-item-primarykey="product-list"]',
            designer = './/h4/a/text()',
            link = './/h4/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('name', '//span[@class="a-txt-product-description"]/text()'),
            ('images', ('//html', _parser.images)),
            ('designer', '//span[@class="a-txt-brand-name"]/a/text() | //span[@class="brand"]/a/text()'),
            ('description', ('//article[@id="content1"]//text()', _parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            current_path='//input[@name="wcid"]/@value',
            path='//fieldset[@class="att1 colour"]/ul/li/label/span/img',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="productDetails"]//text()',          
            ),
        blog = dict(
            official_uid = 85861,
            blog_list_url = _parser.blog_list_url,
            json_blog_links = _parser.json_blog_links,
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    # parse_multi_items = _parser.parse_multi_items

    blog_url = dict(
        EN = [
            'https://www.selfridges.com/US/en/features/welove/'
        ]
    )

    list_urls = dict(
        f = dict(
            a = [
                "http://www.selfridges.com/US/en/cat/womens/accessories/?pn=",
            ],
            b = [
                "http://www.selfridges.com/US/en/cat/bags/womens/?pn=",
            ],
            c = [
                "http://www.selfridges.com/US/en/cat/womens/clothing/?pn=",

            ],
            s = [
                "http://www.selfridges.com/US/en/cat/womens/shoes/?pn=",
            ],
            e = [
                "http://www.selfridges.com/US/en/cat/beauty/skincare/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/make-up/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/bath-bodycare/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/fragrance/candles-diffusers/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/fragrance/womens-perfume/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/beauty-gift-sets/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/korean-beauty/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/travel-size-beauty/?pn=",
            ],
        ),
        m = dict(
            a = [
                "http://www.selfridges.com/US/en/cat/mens/accessories/?pn=",
            ],
            b = [
                "http://www.selfridges.com/US/en/cat/bags/mens/?pn=",
            ],
            c = [
                "http://www.selfridges.com/US/en/cat/mens/clothing/?pn=",
            ],
            s = [
                "http://www.selfridges.com/US/en/cat/mens/shoes/?pn=",
            ],
            e = [
                "http://www.selfridges.com/US/en/cat/beauty/fragrance/mens-aftershave/?pn=",
                "http://www.selfridges.com/US/en/cat/beauty/mens-grooming/?pn=",
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/US/',
    )

    # ajax =  _parser.parse_ajax

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '/US/en/',
            currency_sign = '$',
            ),
        GB = dict(
            currency = 'GBP',
            country_url = '/GB/en/',
            currency_sign = '\xa3'
        ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            country_url = '/CN/zh/',
            currency_sign = '\u00a5'
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '/JP/en/',
            currency_sign = '\xa5',
        ),
        KR = dict(
            currency = 'KRW',
            country_url = '/KR/en/',
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/SG/en/',
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '/HK/en/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/CA/en/',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '/AU/en/',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '/DE/en/',
        ),

        )

        


