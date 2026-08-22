from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        if 'cod10' in item['url']:
            item['sku'] = "COD%s" % item['url'].split('cod10=')[-1].split('&')[0]
        else:
            item['sku'] = item['url'].split('.html')[0].split('_')[-1]
        item['sku'] = item['sku'].upper()
        item['designer'] = "SAINT LAURENT"

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            image = img.split('507w,')[-1].split('677w,')[0].strip()
            item['images'].append(image)

        item['cover'] = item['images'][0] if item['images'] else ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        try:
            ajax = 'http://www.ysl.com/yTos/api/Plugins/ItemPluginApi/GetCombinations/?siteCode=SAINTLAURENT_US&code10='+item['sku'].upper().replace('COD','')
            result = getwebcontent(ajax)
            obj = json.loads(result)
        except:
            item['originsizes'] = ''
            item['error'] = 'Out Of Stock'
        try:
            item['color'] = obj['Colors'][0]['Description'].upper()
        except:
            item['color'] = ''

        size = obj['Sizes']
        nsizes = []
        for s in size:
            nsizes.append(str(s['ClassFamily'].replace('\xbe', '').replace('\xbd', ''))+str(s['Description'].replace('\xbe', '').replace('\xbd', '')))
        
        if kwargs['category'] in ['a','b']:
            sizes = sizes.xpath('.//div[@class="size oneSize"]//span[@class="value"]/text() | .//div[contains(@class, "l-product-details")]//ul[contains(@class, "b-swatches_size")]/li[contains(@class, "b-swatches_size-item b-swatches_size-item-selected")]/span/text() | .//div[contains(@class, "l-product-details")]//ul[contains(@class, "b-swatches_size")]/li/a/@title').extract()
            if len(sizes) > 0:
                for size in sizes:
                    item['originsizes'].append(size.strip())
            else:
                item['originsizes'] = ['IT']
        else:
            if len(nsizes) > 0:
                for size in nsizes:
                    item['originsizes'].append(size.strip())

        
    def _prices(self, prices, item, **kwargs):
        
        saleprice = prices.xpath('.//*[@id="itemPrice"]//span[@class="price"]/span[contains(@class, "value")]/text()').extract()
        listprice = prices.xpath('.//*[@id="itemPrice"]//span[@class="full price"]/span[contains(@class, "value")]/text()').extract()

        if len(saleprice) == 0:
            saleprice = prices.xpath('.//span[@class="discounted price"]/span[contains(@class, "value")]/text()').extract()
        
        if len(listprice) == 0 and len(saleprice) == 0:
            try:
                saleprice = [prices.xpath('.//*[@id="itemPrice"]/text()').extract()[-1]]
            except:
                pass
        try:
            if len(listprice):
                item['originsaleprice'] = saleprice[0].strip()
                item['originlistprice'] = listprice[0].strip()
            else:
                item['originsaleprice'] = saleprice[0].strip()
                item['originlistprice'] = item['originsaleprice']
        except:
                item['originsaleprice'] = ''
                item['originlistprice'] = ''
                item['error'] = 'Do Not Ship'

    def _page_num(self, pages, **kwargs): 
        item_num = pages.split('"totalPages":')[-1].split(',')[0].replace(';', '').replace(':', '')
        try:
            page_num = int(item_num)
        except:
            page_num =1
        # print page_num
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('page=1', 'page='+str(i))
        return url

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//*[contains(@class,"relatedItem")]/@data-ytos-related').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        pid = response.meta.get('sku')
        item['main_prd'] = pid
        ## Look Image not for every Product
        try:
            cover = response.xpath('//img[@class="mainImage"]/@data-origin').extract()
            item['cover'] = cover[0].replace('_9_','_13_')
        except:
            pass
        item['products']= ['COD'+str(x).upper() for x in outfits]
        yield item

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="thumbImage"]//ul[@class="alternativeImages"]/li/img/@data-srcset').extract()
        images = []
        for img in imgs:
            images = img.split('507w,')[-1].split('677w,')[0].strip()
            images.append(image)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        width = response.xpath('//h2[contains(@class, "attribute")]/div[@class="width"]/span[@class="value"]/text()').extract_first()
        height = response.xpath('//h2[contains(@class, "attribute")]/div[@class="height"]/span[@class="value"]/text()').extract_first()
        depth = response.xpath('//h2[contains(@class, "attribute")]/div[@class="depth"]/span[@class="value"]/text()').extract_first()
        fits = []
        for info in infos:
            line_text = ''
            words = info.xpath('.//text()').extract()
            for word in words:
                if word.strip():
                    line_text += word.strip() + ' '
            if width and height and depth and width in line_text and height in line_text and depth in line_text:
                line_text = line_text.replace(width, width +' x').replace(height, height + ' x')
            fits.append(line_text)
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = "ysl"
    merchant = "SAINT LAURENT"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="products"]/@data-ytos-opt',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="products"]/article',
            designer = '@data-ytos-track-product-data',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="tag-after-price soldOut"]', _parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            ('name', '//h1[@class="productName"]/@aria-label'),
            ('images', ('//div[@class="thumbImage"]//ul[@class="alternativeImages"]/li/img/@data-srcset', _parser.images)),
            ('description', '//div[@class="descriptionContent accordion-content"]/text()|//div[@class="descriptionContent"]//text()'),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//h2[contains(@class, "attribute")]',
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "http://www.ysl.com/Search/RenderProductsAsync?department=slgw&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?department=jewelsw&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?department=beltsw&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?department=silkw&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?department=sunglassesw&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US"
        ],
            b = [
                "http://www.ysl.com/Search/RenderProductsAsync?department=bagsw&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
            ],
            c = [
                 "http://www.ysl.com/Search/RenderProductsAsync?department=rtww&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
            ],
            s = [
                "http://www.ysl.com/Search/RenderProductsAsync?department=shoesw&gender=D&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
            ],
        ),
        m = dict(
            a = [
                "http://www.ysl.com/Search/RenderProductsAsync?&department=beltsm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?&department=slgm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?&department=jewelsm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?&department=silkm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US",
                "http://www.ysl.com/Search/RenderProductsAsync?&department=sunglassesm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US"
                ],
            b = [
                "http://www.ysl.com/Search/RenderProductsAsync?&department=bagsm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US" 
               ],
            c = [
                "http://www.ysl.com/Search/RenderProductsAsync?&department=rtwm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US"
            ],
            s = [
                "http://www.ysl.com/Search/RenderProductsAsync?&department=shoesm&gender=U&page=1&productsPerPage=50&siteCode=SAINTLAURENT_US"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'SAINTLAURENT_US',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = 'SAINTLAURENT_US',
            ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            country_url = 'SAINTLAURENT_WY',
            currency_sign = '\xa5',
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = 'SAINTLAURENT_JP',
            language = 'JP'
        ),
        KR = dict(
            currency = 'KRW',
            currency_sign = '\u20a9',
            country_url = 'SAINTLAURENT_KR',
            language = 'KR'
        ),
        SG = dict(
            currency = 'SGD',
            country_url = 'SAINTLAURENT_SG',
            currency_sign = 'SG$',
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'SAINTLAURENT_HK',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'SAINTLAURENT_GB',
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CAD$',
            country_url = 'SAINTLAURENT_CA',
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = "AU$",
            country_url = 'SAINTLAURENT_AU',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'SAINTLAURENT_DE',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = 'SAINTLAURENT_NO',
            currency_sign = '\u20ac',
        ),

        )

        


