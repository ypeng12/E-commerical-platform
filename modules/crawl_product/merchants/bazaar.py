from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['images'] = []
        cover = None
        for img in images:
            item['images'].append(img)
            if '-1_' in img:
                cover = img

        if cover:
            item['cover'] = cover
        else:
            item['cover'] = item['images'][0] if item['images'] else ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.replace('\n\n','\n').replace('\n\n','\n').replace('\t','').strip()

    def _sizes(self, sizes, item, **kwargs):
        item['designer'] = item['designer'].strip()
        pid = item['url'].split('-')[-1].split('.')[0]
        preorder = sizes.xpath('.//p[contains(text(),"Pre-Order")]').extract_first()
        json1 = sizes.xpath('.//script/text()').extract()
        item['sku'] = ''
        for j in json1:
            if 'skusJson_' in j:
                break

        try:
            obj = json.loads(j.split('skusJson_%s = ' %pid)[1].split(';')[0])
        except:
            obj = None
        if not obj:
            item['originsizes'] = ''
            item['error'] = 'Out Of Stock'
        try: 
            item['name'] = obj['productDatas'][0]['productName']
        except:
            item['error'] = 'Out of Stock'
            return
        saleprice = 0
        listprice = 0
        sku = ''
        styleid = ''
        color = ''
        originsizes = []
        originsizes2 = []
        sizes = ''
        sizes_old = {}
        for info in obj['skuInfos']:
            itemId = info['itemId']
            saleprice = info['price'] if not saleprice and 'price' in info else saleprice
            listprice = info['listPrice'] if not listprice and 'listPrice' in info else listprice
            if not styleid:
                skuCode = info['skuCode'] if 'skuCode' in info else ''
                sp = ' ' if ' ' in skuCode else '-'
                styleid = skuCode.split(sp)[0]
                sku = (pid + '-' + styleid)
            for option in info['options']:
                if option['code'] == 'COLOR':
                    color = option['optionValue']['value'] if not color and 'optionValue' in option else color
                elif option['code'] == 'SIZE':
                    value = option['optionValue']['value'] if 'optionValue' in option else None
                    if item not in sizes_old:
                        sizes_old[itemId] = value
                    else:
                        pass

        result = {}
        try:
            url = 'https://shop.harpersbazaar.com/front/app/product/inventory/%s.json' %pid
            result = getwebcontent(url)
        except Exception as ex:
            pass
        if result:
            result_ = json.loads(result)
            sizes_new = {}
            for info_new in result_['productInfo']['skuInfos']:
                sizes_new[info_new['itemId']] = info_new['inStock']
            for k, v in list(sizes_old.items()):
                if preorder:
                    v = v + ':p'
                if sizes_new[k]:
                    originsizes.append(v)
                    if ' / ' in v:
                        originsizes2.append(v.split(' / ')[-1].strip())
                    

        if saleprice > 0:
            item['originsaleprice'] = saleprice
        else:
            item['error'] = 'Sale price not found'
        if listprice > 0:
            item['originlistprice'] = listprice
        else:
            item['originlistprice'] = saleprice

        if int(item['originlistprice']) < int(item['originsaleprice']):
            item['originlistprice'] = item['originsaleprice']

        item['originlistprice'] = str(item['originlistprice'])
        item['originsaleprice'] = str(item['originsaleprice'])
        item['originsizes'] = originsizes
        item['originsizes2'] = originsizes2
        item['sku'] = sku.upper()
        item['color'] = color

    def _prices(self, prices, item, **kwargs):
        pass

    def _parse_item_url(self, response, **kwargs):
        try:
            obj = json.loads(response.body)
        except:
            obj = None
        numFound = obj['response']['numFound'] if obj else 0
        url = response.url.replace('rows=0','rows=%s' %numFound)
        result = getwebcontent(url)
        obj = json.loads(result)
        docs = obj['response']['docs'] if obj else []
        for doc in docs:
            page_name_s = doc['page_name_s']
            if not page_name_s.startswith('clothing') and not page_name_s.startswith('shoes') \
                    and not page_name_s.startswith('bags') and not page_name_s.startswith('jewelry') \
                    and not page_name_s.startswith('jewelry'):
                href = 'https://shop.harpersbazaar.com/%s' %doc['page_name_s']
                yield href,''

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath('//ul[@class="font-list-copy"]/li//text()').extract()
        if not infos:
            infos = response.xpath('//div[@class="full-width-col"]/ul/li/text()').extract()
        else:
            infos += response.xpath('//div[@class="full-width-col"]/ul/li/text()').extract()
        if not infos:
            infos = response.xpath('//ul[@class="pdp-accordion__body__size-list"]/li/text()').extract()
        else:
            infos += response.xpath('//ul[@class="pdp-accordion__body__size-list"]/li/text()').extract()
        if not infos:
            infos = response.xpath('//div[@class="size-fit-details"]/ul/li/text()').extract()
        else:
            infos += response.xpath('//div[@class="size-fit-details"]/ul/li/text()').extract()

        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('Dimensions' in info or 'Model' in info or 'measures' in info or 'width' in info or 'length' in info or 'inches' in info or '/' in info):
                fits.append(info.strip())
        desc_info = response.xpath('//div[@class="product-details"]//text()').extract_first()
        descs = desc_info.split('.')
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
            if 'Dimensions' in descs[i] or 'Model' in descs[i] or 'measures' in descs[i] or 'width' in descs[i] or 'length' in descs[i] or 'inches' in descs[i] or '/' in descs[i]:
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

        size_info = '\n'.join(fits + desc_li)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.body)
        number = (obj["response"]["numFound"])
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = "bazaar"
    merchant = "ShopBAZAAR"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            parse_item_url = _parser.parse_item_url,
            items = '//article[@class="item   "]/article',
            designer = '@data-ytos-track-product-data',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="in-stock-container" and contains(@style, "display:none")]', _parser.checkout)), 
            ('designer','//*[@class="product_option_container_BRAND"]/text()'),
            ('images', ('//div[@class="slider-paging hidden-xs"]/ul/li/a/img/@src', _parser.images)),
            ('description', ('//*[@class="product-details"]//text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="slider-paging hidden-xs"]/ul/li/a/img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//html',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://shop.harpersbazaar.com/search/?wt=json&start=0&rows=0&sort=score%20desc&q=attr_cat_id:8&i=',
                'https://shop.harpersbazaar.com/search/?wt=json&start=0&rows=0&sort=score%20desc&q=attr_cat_id:9&i='
            ],
            b = [
                "https://shop.harpersbazaar.com/search/?wt=json&start=0&rows=0&sort=sequence52_i%20desc&q=attr_cat_id:52&i=",
            ],
            c = [
                 "https://shop.harpersbazaar.com/search/?wt=json&start=0&rows=0&sort=sequence6_i%20desc&q=attr_cat_id:6&i=",
            ],
            s = [
                "https://shop.harpersbazaar.com/search/?wt=json&start=0&rows=0&sort=sequence7_i%20desc&q=attr_cat_id:7&i=",
            ],
            e = [
                "https://shop.harpersbazaar.com/search/?wt=json&start=0&rows=0&sort=score%20desc&q=attr_cat_id:1580&i="
                ],
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

    )


    countries = dict(
        US = dict(
            language = 'EN',
            currency = 'USD',
            ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        CN = dict(
            currency = 'CNY',
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
        GB = dict(
            currency = 'GBP',
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
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
        )
        )

        


