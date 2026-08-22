from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        add_to_cart = checkout.extract_first()
        if not add_to_cart:
            return True
        elif add_to_cart and add_to_cart.lower() == 'sold out':
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].strip()

    def _images(self, images, item, **kwargs):
        images = images.extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img = img.replace("//","https://")
            img = img.split('?')[0] + '?sw=556&sm=fit'
            if img not in imgs:
                imgs.append(img)
        item['cover'] = imgs[0]
        item['images'] = imgs
        item['color'] = item['color'].upper() if item['color'] else item['color']
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        orsizes = sizes.xpath('.//ul[@class="swatches size"]/li[not(contains(@class,"unselectable"))]/a/span/text()').extract()
        size_tag = sizes.xpath('.//*[@class="size-type"]/text()').extract_first()
        size_li = []
        for osize in orsizes:
            size = osize.split('-')[0].strip().replace('\\','').replace('"','')
            if size_tag and size.isdigit():
                size = size_tag.strip() + size
            size_li.append(size)

        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[contains(@class,"product-sales-price bfx-price")]/text()').extract()
        regularPrice = prices.xpath('.//span[@class="product-standard-price bfx-price"]/text()').extract()
        for r in regularPrice:
            if "pri" not in r.lower() and r.strip()!='':
                regularPrice = r.strip()
        for s in salePrice:
            if "pri" not in s.lower() and s.strip()!='':
                salePrice = s.strip()
        if regularPrice:
            item['originsaleprice'] = salePrice.strip()
            item['originlistprice'] = regularPrice.strip()
        else:
            item['originsaleprice'] = salePrice.strip()
            item['originlistprice'] = ''

    def _page_num(self, pages, **kwargs):
        item_num = pages.replace('items','').strip()
        page_num = int(item_num)/60 + 2
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        i=i-1
        url = response_url + '?sz=60&start=' + str(i * 60)
        return url

    def _get_headers(self, response, item, **kwargs):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
        return headers
    
    def _parse_images(self, response, **kwargs):
        images = response.xpath('//ul[@class="product-img-thumbnails"]/li//img/@src').extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img = img.replace("//","https://")
            img = img.split('?')[0] + '?sw=556&sm=fit'
            if img not in imgs:
                imgs.append(img)

        return imgs

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//*[@class="recommendations cross-sell"]//li//a[@class="name-link"]/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        pid = response.meta.get('sku')
        item['main_prd'] = pid
        fcover =None
        try:
            cover = response.xpath('//*[@id="pdpMain"]//img/@src').extract()
            for c in cover:
                if '_2.jpg' in c.lower():
                    fcover=c
                    break
            if not fcover:
                fcover = cover[-1]
            item['cover'] = fcover.split('?')[0]+'?sw=1000&sh=1000&sm=fit'
        except:
            pass
        item['products']= [str(x).split('#')[-1].split('.htm')[0].split('/')[-1].replace('-','').replace('%2F','/').replace('+',' ').upper() for x in outfits]
        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        desc_info = infos.xpath('./div[@class="product-details-content"][1]/text()').extract_first()
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
            if '"' in descs[i]:
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

        info_li = []
        infos = infos.xpath('./div[@class="product-details-content"]/ul/li/text()').extract()
        for info in infos:
            if info.strip() and info.strip() not in info_li and '"' in info:
                info_li.append(info.strip())

        size_info = '\n'.join(desc_li + info_li)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[contains(@class,"search-result-items-count")]/span/text()').extract_first().replace('items','').strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'intermix'
    merchant = 'INTERMIX'

    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[contains(@class,"search-result-items-count")]/span/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[@id="search-result-items"]/li',
            designer = './/span[@class="brand high-level-description"]/text()',
            link = './/a[@class="name-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add-to-cart"]/text()', _parser.checkout)),
            ('sku', ('//span[@itemprop="productID"]/text()',_parser.sku)),
            ('name', '//h2[@class="product-name high-level-description"]/text()'),
            ('designer', '//h1[@class="product-brand-name"]/a/text()'),
            ('color', '//li[@class="attribute fit-predictor-attr color"]/div/p/text()'),            
            ('images', ('//ul[@class="product-img-thumbnails"]/li//img/@src', _parser.images)),
            ('description', '//div[@class="product-info"]//div[@class="accordion expand"]/div[@class="product-details-content"]//text()'), # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="product-pricing product-price"]', _parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=74768,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="accordion expand"][1]',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
                "https://www.intermixonline.com/designer-jewelry/",
                "https://www.intermixonline.com/designer-jewelry-sale/",
                "https://www.intermixonline.com/designer-accessories/belts/",
                "https://www.intermixonline.com/designer-accessories/hats/",
                "https://www.intermixonline.com/designer-accessories/scarves-wraps/",
                "https://www.intermixonline.com/designer-accessories/sunglasses/"
            ],
            b = [
                "https://www.intermixonline.com/designer-accessories/bags/",
            ],
            c = [
                "https://www.intermixonline.com/designer-clothing/",
                "https://www.intermixonline.com/designer-clothing-sale/"
            ],
            s = [
                "https://www.intermixonline.com/designer-shoes/",
                "https://www.intermixonline.com/designer-shoes-sale/",
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
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            vat_rate = 1.3  # TODO

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            vat_rate = 1.1  # TODO

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            vat_rate = 1.2  # TODO

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            vat_rate = 1  # TODO

        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            vat_rate = 1  # TODO

        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            vat_rate = 1  # TODO

        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            vat_rate = 1.15  # TODO

        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            vat_rate = 1  # TODO

        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            vat_rate = 1  # TODO

        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            vat_rate = 1.2  # TODO

        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            vat_rate = 1.2  # TODO
        ),

        )

        


