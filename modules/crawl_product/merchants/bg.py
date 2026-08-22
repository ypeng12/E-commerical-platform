from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
from base64 import b64encode
import time
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *


class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        page_num = data.split('of')[-1].strip()
        return int(page_num)

    def _checkout(self, data, item, **kwargs):
        checkout = data.xpath('.//button[@aria-label="Add to Bag"]').extract_first()
        child_check = data.xpath('.//*[contains(text(),"Kids\' Size Guide")]//text()').extract_first()

        if child_check :
            return True
        if checkout:
            return False
        else:
            return True

    def _prices(self, prices, item, **kwargs):
        try:
            saleprice = prices.xpath('.//span[@class="adornment currentPrice"]/span/h5/text()').extract()[0]
            listprice = prices.xpath('.//span[@class="adornment originalPrice"]/span/h5/text()').extract()[0]
        except:
            saleprice = prices.xpath('.//span[contains(@class,"retailPrice")]/text()').extract()[0]
            listprice = prices.xpath('.//span[contains(@class,"retailPrice")]/text()').extract()[0]
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_multi_items(self, response, item, **kwargs):
        data = json.loads(response.xpath('//script[@id="state"]/text()').extract_first())

        item['url'] = item['url'].split('?')[0]
        item['designer'] = data['productCatalog']['product']['linkedData']['brand']
        try:
            item['description'] = data['productCatalog']['product']['linkedData']['description']
        except:
            item['description'] = ''
        item['sku'] = data['productCatalog']['product']['id'].upper()
        try:
            options = data['productCatalog']['product']['options']['productOptions']
        except:
            options = ''
        imgs = ''
        for opt in options:
            if opt['label'] == 'color':
                imgs = opt['values']
                break

        colors = response.xpath('//ul[@class="product-options__list"]/li//img/@title').extract()
        if colors == []:
            colors = ["default"]
        for img in imgs:
            if img['name'] not in colors:
                colors.append(img['name'])

        sizes = data['productCatalog']['product']['skus']

        for color in colors:
            item_color = deepcopy(item)
            item_color['color'] = color
            if color == 'default':
                continue
                item_color['sku'] = item_color['sku']
                item_color['color'] = ''
            else:
                item_color['sku'] = item_color['sku'] + '_' + color

            img_li = []
            color_img_li = []
            media = []

            for img in imgs:
                if img['name'] == color:
                    break
            try:
                media = img['media']
            except:
                media = data['productCatalog']['product']['media']

            if len(media):
                if 'large' in list(media['main'].keys()):
                    img_li.append(media['main']['dynamic']['url'])
                else:
                    img_li.append(media['main']['dynamic']['url'])
                if 'alternate' in media:
                    if 'a' in media['alternate']:
                        if 'large' in list(media['main'].keys()) and 'url' in list(media['alternate']['a']['large'].keys()):
                            img_li.append(media['alternate']['a']['large']['url'])
                        else:
                            img_li.append(media['alternate']['a']['dynamic']['url'])
                    if 'b' in media['alternate']:
                        if 'large' in list(media['main'].keys()) and 'url' in list(media['alternate']['b']['large'].keys()):
                            img_li.append(media['alternate']['b']['large']['url'])
                        else:
                            img_li.append(media['alternate']['b']['dynamic']['url'])
                    if 'c' in media['alternate']:
                        if 'large' in list(media['main'].keys()) and 'url' in list(media['alternate']['c']['large'].keys()):
                            img_li.append(media['alternate']['c']['large']['url'])
                        else:
                            img_li.append(media['alternate']['c']['dynamic']['url'])
                
                for img in img_li:
                    if 'http' not in img:
                        img = 'https:'+img
                        color_img_li.append(img)
                item_color['images'] = color_img_li
                item_color['cover'] = color_img_li[0]
            size_li = []
            for size in sizes:
                try:
                    if size['color']['name'] == color:
                        osize = size['size']['name'].split('/')[-1].strip() if 'name' in size['size'] else 'IT'
                        if size['inStock']:
                            size_li.append(osize)
                        elif size['preOrder']:
                            size_li.append(osize+':p')
                        elif size['backOrder']:
                            size_li.append(osize+':b')
                        elif size['dropShip'] and size['stockStatusMessage'] != 'Item Not Available':
                            size_li.append(osize)
                except:
                    size_li = ['onesize']
            item_color['originsizes'] = size_li
            self.sizes(size_li, item_color)

            yield item_color

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@id="state"]/text()').extract_first())
        colors = response.xpath('//ul[@class="product-options__list"]/li//img/@title').extract()

        if not colors or len(colors) == 1:
            try:
                image = data['productCatalog']['product']['linkedData']['image']
            except:
                image = data['productCatalog']['product']['media']['main']['dynamic']['url']
            images = [image]
            return images

        color = response.meta['sku'].split('_')[-1].upper()

        options = data['productCatalog']['product']['options']['productOptions']
        imgs = []
        for opt in options:
            if opt['label'] == 'color':
                imgs = opt['values']
                break
        images = []
        media = []

        for img in imgs:
            if img['name'] == color:
                media = img['media']
                break

        if media:
            try:
                image = 'https:' + media['alternate']['a']['medium']['url']
            except:
                image = 'https:' + media['main']['dynamic']['url']
            images.append(image)

        return images

    def _parse_look(self, item, look_path, response, **kwargs):
        # self.logger.info('==== %s', response.url)
        try:
            script = response.xpath('//script/text()').extract()
            for s in script:
                if 'window.utag_data=' in s:
                    s = s.split(' window.utag_data=')[-1].split(';')[0]
                    break
            products = json.loads(s)
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            # logger.debug(traceback.format_exc())
            return

        if len(products["product_cmos_item"])==1:
            yield self.parseWithOutCover(response, item)
        else:
            yield self.parseWithCover(response, products, item)
            
    def parseWithCover(self, response, products, item):
        item['main_prd'] = response.meta.get('sku')
        # item['look_key'] = outfit.get('outfitId')
        cover = response.xpath("//img[@data-static-main-image]/@src").extract()
        main_photo =None
        for c in cover:
            if '/SU/' in c:
                main_photo = c
                break
        if (not main_photo) and cover:
            main_photo = cover[0]

        item['cover'] = main_photo.replace('_mu','_mz')
        item['products'] = json.dumps(products["product_cmos_item"])

        yield item

    def parseWithOutCover(self, response, item):
        products = None
        try:
            products = response.xpath('//div[@id="complete-the-look"]//div/@data-cmosid').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if not products:
            logger.info('outfit none@ %s', response.url)
            return

        item['cover'] = response.xpath("//img[@data-static-main-image]/@src").extract_first()
        item['products'] = []
        for product in products:
            item['products'].append(product.split('_')[-1])

        item['main_prd'] = response.meta.get('sku')
        tup1 =str(item['main_prd']).split('_')[0]
        # item['look_key'] = outfit.get('outfitId')
        tup=[]
        tup.append(tuple([tup1,[]]))
        for product in item['products']:
            tup2 = [x for x in item['products'] if x != product]
            tup.append(tuple([product, tup2]))
        item['products'] = list(tup)
        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'Height' in info or '/' in info or 'Fit' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="product-list__header__container count"]/div/text()[last()]').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('items',''))
        return number

_parser = Parser()

class Config(MerchantConfig):
    name = 'bg'
    merchant = 'BERGDORF GOODMAN'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="pagination-pages"]/@aria-label', _parser.page_num),
            items = '//div[@class="list-container"]/div/div',
            designer = './/span[@class="designer line-height-sixteen"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//html', _parser.checkout)),
            ('name','//span[@class="product-heading__name__product"]/text()'),
            ('prices',('//html', _parser.prices)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=61853,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="productCutline"]/div[1]//text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.bergdorfgoodman.com/c/accessories-cat441106?page=",
                "https://www.bergdorfgoodman.com/c/accessories-jewelry-cat441013?page="
            ],
            b = [
                "https://www.bergdorfgoodman.com/c/handbags-cat428607?page=",
            ],
            c = [
                "https://www.bergdorfgoodman.com/c/womens-clothing-cat441206?page=",
            ],
            s = [
                "https://www.bergdorfgoodman.com/c/shoes-cat428606?page=",
            ],
            e = [
                "https://www.bergdorfgoodman.com/c/beauty-skin-care-cat243404?page=",
                "https://www.bergdorfgoodman.com/c/beauty-makeup-cat243403?page="
            ]
        ),
        m = dict(
            a = [
                "https://www.bergdorfgoodman.com/c/men-accessories-belts-cat214308?page=",
                "https://www.bergdorfgoodman.com/c/men-accessories-cuff-links-cat213532?page=",
                "https://www.bergdorfgoodman.com/c/men-accessories-scarves-hats-gloves-cat261801?page=",
                "https://www.bergdorfgoodman.com/c/men-accessories-sunglasses-eyeglasses-cat216801?page=",
                "https://www.bergdorfgoodman.com/c/men-accessories-ties-pocket-squares-cat213541?page=",
                "https://www.bergdorfgoodman.com/c/men-accessories-watches-jewelry-cat472113?page=",
            ],
            b = [
                "https://www.bergdorfgoodman.com/c/men-accessories-bags-wallets-cat214310?page=",
                "https://www.bergdorfgoodman.com/c/men-accessories-luggage-travel-cat495901"
            ],
            c = [
                "https://www.bergdorfgoodman.com/c/men-clothing-cat521724?page=",
                "https://www.bergdorfgoodman.com/c/men-accessories-socks-cat548214?page=",
            ],
            s = [
                "https://www.bergdorfgoodman.com/c/men-shoes-cat501911?page=",
            ],
            e = [
                "https://www.bergdorfgoodman.com/c/men-accessories-cologne-grooming-cat364602"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '.com/',
    )

    parse_multi_items = _parser.parse_multi_items

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = '$',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            # country_url = '.com/en-cn/',
            # vat_rate = 1.058,
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            # country_url = '.com/en-jp/',
            # vat_rate = 1.064
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            # country_url = '.com/en-kr/',
            # vat_rate = 1.128
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            # country_url = '.com/en-sg/',
            # vat_rate = 1.093
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            country_url = '.com/en-hk/',
            # vat_rate = 1.076
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            # country_url = '.com/en-gb/',
            # vat_rate = 1.10
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            # country_url = '.com/en-ru/',
            # vat_rate = 1.0
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            # country_url = '.com/en-ca/',
            # vat_rate = 1.076
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            # country_url = '.com/en-au/',
            # vat_rate = 1.083
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            # country_url = '.com/en-de/',
            # vat_rate = 1.067
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            # country_url = '.com/en-no/',
            # vat_rate = 1.093
        ),

        )

        


