from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout.xpath('.//p[@class="msg-out-of-stock"]/text()').extract() and kwargs['category'] == 'b':
            return True
        elif checkout.xpath('.//p[@class="b-status_message-not_available"]/text()').extract():
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].strip()
        item['designer'] = "CHARLOTTE OLYMPIA"

    def _images(self, images, item, **kwargs):
        images = images.xpath('//div[contains(@class,"l-product_images_container")]//ul[@data-colorswatchid="%s"]/li/img/@data-lgimg'%item['sku']).extract()
        item['images'] = []
        for img in images:
            image = json.loads(img)
            item['images'].append(image['hires'])
        item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.strip().replace('\n\n','\n').replace('\n\n','\n')

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        ori_sizes = sizes.extract()        
        for ori_size in ori_sizes:
            if 'not available' in ori_size:
                continue
            ori_size = ori_size.replace(',','.')
            item['originsizes'].append(ori_size)
        if not item['originsizes'] and item['category'] in ['a', 'b', 'e']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//*[@class="b-product_price-sales"]/text()').extract()
        listprice = prices.xpath('.//*[contains(@class,"price-standard")]/text()').extract()
        if len(saleprice) > 0:
            item['originsaleprice'] = saleprice[0].strip()
            item['originlistprice'] = listprice[0].strip()
        else:
            item['originlistprice'] = prices.xpath('.//meta[@itemprop="price"]/@content').extract()[0].strip()
            item['originsaleprice'] = item['originlistprice']

    def _page_num(self, pages, **kwargs): 
        item_num = pages
        try:
            page_num = int(item_num.split('of')[-1].replace('items', '').strip())/18 +2
        except:
            page_num =2
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=1','').replace('?page=','') + '?page=' + str(i)
        return url

    def _parse_images(self, response, **kwargs):
        imgs = images.xpath('//div[contains(@class,"l-product_images_container")]//ul[@data-colorswatchid="%s"]/li/img/@data-lgimg'%kwargs['sku']).extract()
        images = []
        for img in imgs:
            image = json.loads(img)
            images.append(image['hires'])
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()        
        fits = []
        desc_li = []
        if len(infos)>1:
            for info in infos:
                if info.strip() and info.strip() not in fits and ('cm' in info.strip().lower() or 'mm' in info.strip().lower()):
                    fits.append(info.strip())
        elif len(infos)==1:
            descs = infos[0].split('.')
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
                if 'cm' in descs[i] or 'mm' in descs[i] or 'Measurements' in descs[i]:
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

        size_info = '\n'.join(fits+desc_li)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = "olympia"
    merchant = "CHARLOTTE OLYMPIA"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[contains(@class,"l-search_result-paging-controls-loaded")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="b-product-hover_box js-product-hover_box"]',
            designer = './/div/@data-brand',
            link = './/a[contains(@class,"js-producttile_link b-product_image-wrapper")]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//div[@class="b-product_attribute-value"]/text()',_parser.sku)),
            ('name', '//span[@class="b-product_name"]/text()'),
            ('color','//div[@class="l-product-details js-product_detail"]//span[@class="js_color-description"]/text()'),
            ('images', ('//html', _parser.images)),
            ('description', ('//div[@class="b-product_long_description"]//text()|//div[@class="accordian"]/div[2]//text()',_parser.description)),
            ('sizes', ('//ul[contains(@class,"b-swatches_size scrollable")]/li/a/@title', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
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
            size_info_path = '//div[@class="b-product_short_customfilter_2"]//text()',
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/accessories/?page=",
            ],
            b = [
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/leather-bags/?page=",
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/clutch-bags/?page=",
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/shoulder-bags/?page=",
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/tote-bags/?page="
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/backpacks/?page="
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/luggage/?page="
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/small-leather-goods/?page="
                "https://www.charlotteolympia.com/en/bags/bags-and-accessories/kitty/?page="
            
            ],

            s = [
                "https://www.charlotteolympia.com/en/shoes/all/?page=",
            ],
        ),
        m = dict(
            s = [
                "https://www.charlotteolympia.com/en/collections/campaigns/men/?page="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cookies = {'preferredCountry':'US'}
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\u20ac',
            cookies = {'preferredCountry':'CN'},
            discurrency = 'EUR',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {'preferredCountry':'JP'},
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {'preferredCountry':'KR'},
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {'preferredCountry':'SG'},
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            cookies = {'preferredCountry':'HK'},
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = {'preferredCountry':'GB'}
        ),

        CA = dict(
            currency = 'CAD',
            currency_sign = '$',
            discurrency = 'USD',
            cookies = {'preferredCountry':'CA'},
        ),
        AU = dict(
            discurrency = 'EUR',
            currency = 'AUD',
            cookies = {'preferredCountry':'AU'}
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',     
            cookies = {'preferredCountry':'DE'},
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {'preferredCountry':'NO'},
        ),

        )

        


