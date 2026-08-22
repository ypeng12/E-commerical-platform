from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
from utils.utils import *

class Parser(MerchantParser):

    def _page_num(self, data, **kwargs):
        pages = int(data.split('of')[-1].strip())
        return pages

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _check_shipped(self, checkshipped, item, **kwargs):
        if checkshipped:
            return True
        else:
            return False

    def _sku(self, response, item, **kwargs):
        data = json.loads(response.extract_first())
        item['sku'] = data['productCatalog']['product']['id'].upper()
        item['name'] = data['chatData']['product_name'][0]
        item['designer'] = data['chatData']['product_brand'].upper()
        if item['designer'] == 'FOUR HANDS':
            item['designer'] = ''
        item['description'] = data['productCatalog']['product']['linkedData']['description']
        item['tmp'] = data

    def _prices(self, prices, item, **kwargs):
        prices = item['tmp']['productCatalog']['product']['price']
        if 'adornments' in prices:
            for price in prices['adornments']:
                if price['label'] == 'Original':
                    item['originlistprice'] = price['price']
                elif price['label'] == 'NOW':
                    item['originsaleprice'] = price['price']
            if 'promotionalPrice' in prices:
                item['originsaleprice'] = prices['promotionalPrice']
        else:
            item['originlistprice'] = prices['retailPrice']
            item['originsaleprice'] = item['originlistprice']

    def _parse_multi_items(self, response, item, **kwargs):
        obj = item['tmp']
        try:
            productOptions = obj['productCatalog']['product']['options']['productOptions']
        except:
            item['images'] = []
            item['color'] = ''
            imgs = response.xpath('//div[@class="product-media"]/div/ul/li//img/@src').extract()
            if not imgs:
                imgs = response.xpath('//img[@alt="%s"]/@src'%item['name']).extract()
            if not imgs:
                imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
            for img in imgs:
                if 'http' not in img:
                    image = 'https:' + img.replace('g.jpg','z.jpg')
                else:
                    image = img.replace('g.jpg','z.jpg')
                item['images'].append(image)
            item['cover'] = item['images'][0]
            back_order = obj['productCatalog']['product']['skus'][0]['backOrder']
            memo = ':b' if back_order else ''
            osize = 'One Size' + memo
            item['originsizes'] = [osize]
            self.sizes('', item, **kwargs)
            yield item
            return

        for option in productOptions:
            if option['label'] == 'color':
                break

        skus = []
        offers = obj['productCatalog']['product']['linkedData']['offers']['offers']
        sku_sizes = {}
        stock_info = {}
        for sku in obj['productCatalog']['product']['skus']:
            sku_sizes[sku['id']] = sku['size']['name'] if 'name' in sku['size'] else 'IT'
            stock_info[sku['id']] = sku['stockStatusMessage']

        for value in option['values']:
            item_color = deepcopy(item)
            color = value['name']
            item_color['color'] = color
            item_color['sku'] = item['sku'] + '_' + color
            skus.append(item_color['sku'])
            images = []
            if 'media' in value:
                try:
                    cover = 'https:' + value['media']['main']['medium']['url']
                    images.append(cover)
                    if 'alternate' in value['media']:
                        for img in list(value['media']['alternate'].values()):
                            img_url = 'https:' + img['medium']['url']
                            images.append(img_url)
                except:
                    medias = list(value['media']['alternate'].values())[0]
                    cover = 'https:' + medias['medium']['url']
                    images.append(cover)
            else:
                color_datas = obj['productCatalog']['product']['media']
                cover = 'https:' + color_datas['main']['medium']['url']
                images.append(cover)
                try:
                    for value in list(color_datas['alternate'].values()):
                        img_url = 'https:' + value['medium']['url']
                        images.append(img_url)
                except:
                    pass
            item_color['images'] = images
            orisizes = []

            memo = ''
            for offer in offers:
                if offer['availability'] in ['InStock','PreOrder','Back Order'] and offer['itemOffered']['color'] == color:
                    memo = ':p' if offer['availability'] == 'PreOrder' else ''
                    memo = ':b' if offer['availability'] == 'Back Order' else ''
                    if not memo:
                        if 'PreOrder' in str(stock_info):
                            memo = ':p'
                        elif 'Back Order' in str(stock_info):
                            memo = ':b'
                    orisizes.append(sku_sizes[offer['sku']])

            if item_color['category'] in ['b', 'a', 'e'] and not ';'.join(orisizes):
                item_color['originsizes'] = ['IT' + memo]
            else:
                item_color['originsizes'] = list([x+memo for x in orisizes])
            self.sizes('', item_color, **kwargs)

            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _parse_images(self, response, **kwargs):
        images = []
        obj = json.loads(response.xpath('//script[@id="state"]/text()').extract()[0])
        try:
            productOptions = obj['productCatalog']['product']['options']['productOptions']
            for option in productOptions:
                if option['label'] == 'color':
                    break
            for value in option['values']:
                if value['name'].upper() != response.meta['sku'].split('_')[-1].upper():
                    continue
                color = value['name']
                images = []
                if 'media' in value:
                    try:
                        cover = 'https:' + value['media']['main']['medium']['url']
                        images.append(cover)
                        if 'alternate' in value['media']:
                            for img in list(value['media']['alternate'].values()):
                                img_url = 'https:' + img['medium']['url']
                                images.append(img_url)
                    except:
                        medias = list(value['media']['alternate'].values())[0]
                        cover = 'https:' + medias['medium']['url']
                        images.append(cover)
                else:
                    color_datas = obj['productCatalog']['product']['media']
                    cover = 'https:' + color_datas['main']['medium']['url']
                    images.append(cover)
                    try:
                        for value in list(color_datas['alternate'].values()):
                            img_url = 'https:' + value['medium']['url']
                            images.append(img_url)
                    except:
                        pass
        except:
            imgs = response.xpath('//div[@class="product-media"]/div/ul/li//img/@src').extract()
            if not imgs:
                imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
            for img in imgs:
                if 'http' not in img:
                    image = 'https:' + img.replace('g.jpg','z.jpg')
                else:
                    image = img.replace('g.jpg','z.jpg')
                images.append(image)
        if not images:
            imgs = response.xpath('//div[@class="product-media"]/div/ul/li//img/@src').extract()
            if not imgs:
                imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
            for img in imgs:
                if 'http' not in img:
                    image = 'https:' + img.replace('g.jpg','z.jpg')
                else:
                    image = img.replace('g.jpg','z.jpg')
                images.append(image)
        return images

    def _parse_mpnmaps(self, response, **kwargs):
        datas = []
        scripts = response.xpath('//script/text()').extract()
        for script in scripts:
            if 'utag_data_dt =' in script:
                break

        try:
            data = json.loads(script.split('product_analytics =')[-1].split('d.addEventListener')[0].strip())
        except:
            return datas

        skus = data['details']['products'][0]['skus']
        for sku in skus:
            if 'color' in sku and sku['color'] != kwargs['color']:
                continue
            mpnmap = {}
            mpnmap['pimSkuId'] = sku['pimSkuId'] if 'pimSkuId' in sku else ''
            mpnmap['cmosSkuId'] = sku['cmosSkuId'] if 'cmosSkuId' in sku else ''
            datas.append(mpnmap)
        return datas

    def _parse_look(self, item, look_path, response, **kwargs):
        # self.logger.info('==== %s', response.url)
        try:
            script = response.xpath('//script/text()').extract()
            for s in script:
                if 'window.utag_data_dt' in s:
                    s = s.split(' window.utag_data_dt =')[-1].split(' window.product_analytics')[0].strip()
                    break
            products = json.loads(s)

        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if len(products["product_cmos_item"])==1:
            item =  self.parseWithOutCover(response, item)
        else:
            item = self.parseWithCover(response, products, item)

        yield item

    def parseWithCover(self, response, products, item):

        item['main_prd'] = response.url
        # item['look_key'] = outfit.get('outfitId')
        cover = response.xpath("//img[@itemprop='image']/@src").extract()
        main_photo =None
        for c in cover:
            if '/SU/' in c:
                main_photo = c
                break
        if (not main_photo) and cover:
            main_photo = cover[0]

        item['cover'] = main_photo.replace('_mu','_mz')
        item['products'] = products["product_id"]

        return item

    def parseWithOutCover(self, response, item):
        products = None
        try:
            products = response.xpath('//div[@id="complete-the-look"]//div/@id').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if not products:
            logger.info('outfit none@ %s', response.url)
            return

        item['main_prd'] = response.url

        cover = response.xpath("//img[@itemprop='image']/@src").extract()
        main_photo =None
        for c in cover:
            if '/SU/' in c:
                main_photo = c
                break
        if (not main_photo) and cover:
            main_photo = cover[0]
        item['cover'] = main_photo.replace('_mu','_mz')

        products = [(str(x).split('_')[-1]) for x in set(products)]
        item['products'] = []
        if len(products) == 1:
            item['products'].append(products[0])
        else:
            item['products'].append((products[0],products[1:]))

        return item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'Height' in info or 'Fit' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()

class Config(MerchantConfig):
    name = 'neiman'
    merchant = 'Neiman Marcus'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//nav[@class="pagination"]/span/@aria-label', _parser.page_num),
            items = '//div[contains(@class,"product-list")]/div[contains(@class,"product-thumbnail")]',
            designer = './/span[@class="designer"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            # ('checkshipped',('//p[@class="error-text"]/text()', _parser.check_shipped)),
            ('checkout', ('//div[contains(@class,"soldout")]', _parser.checkout)),
            ('sku', ('//script[@id="state"]/text()',_parser.sku)),
            ('prices', ('//html',_parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=4329,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-description__content__cutline-standard"]/ul/li/text()',
            ),
        mpnmap = dict(
            method = _parser.parse_mpnmaps,
            )
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.neimanmarcus.com/c/jewelry-accessories-jewelry-bracelets-cat4870733?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-jewelry-brooches-cat12100747?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-jewelry-earrings-cat4870732?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-jewelry-necklaces-cat4870734?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-jewelry-personalized-jewelry-cat42390735?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-jewelry-rings-cat2650734?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-jewelry-watches-cat000264?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-precious-jewelry-bracelets-cat14840757?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-precious-jewelry-earrings-cat14840756?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-precious-jewelry-necklaces-cat21750738?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-precious-jewelry-rings-cat21750740?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-precious-jewelry-watches-cat52970755?page=",
                "https://www.neimanmarcus.com/c/jewelry-accessories-accessories-cat51730760?page=",
            ],
            b = [
                "https://www.neimanmarcus.com/c/handbags-handbags-cat46860739?page=",
            ],
            c = [
                "https://www.neimanmarcus.com/c/womens-clothing-clothing-cat58290731?page=",

            ],
            s = [
                "https://www.neimanmarcus.com/c/shoes-all-designer-shoes-cat47190746?page=",
            ],
            e = [
                "https://www.neimanmarcus.com/c/beauty-skin-care-cat10470738?page=",
                "https://www.neimanmarcus.com/c/beauty-makeup-cat10420742?page=",
                "https://www.neimanmarcus.com/c/beauty-fragrances-cat10470744?page=",
                "https://www.neimanmarcus.com/c/beauty-hair-care-cat51180746?page=",
                "https://www.neimanmarcus.com/c/beauty-bath-body-cat10470806?page="
            ]
        ),
        m = dict(
            a = [
                "https://www.neimanmarcus.com/c/mens-accessories-belts-cat13230731?page=",
                "https://www.neimanmarcus.com/c/mens-accessories-jewelry-cuff-links-cat000533?page=",
                "https://www.neimanmarcus.com/c/mens-accessories-scarves-hats-gloves-cat14030744?page=",
                "https://www.neimanmarcus.com/c/mens-accessories-sunglasses-cat9310734?page=",
                "https://www.neimanmarcus.com/c/mens-accessories-tech-accessories-cat62130788?page=",
                "https://www.neimanmarcus.com/c/mens-accessories-ties-pocket-squares-cat40450753?page=",
                "https://www.neimanmarcus.com/c/mens-accessories-watches-cat540731?page="
            ],
            b = [
                "https://www.neimanmarcus.com/c/mens-accessories-bags-wallets-cat8670736?page=",
            ],
            c = [
                "https://www.neimanmarcus.com/c/mens-clothing-cat14120827?page=",
            ],
            s = [
                "https://www.neimanmarcus.com/c/mens-shoes-cat000550?page=",
            ],
            e = [
                "https://www.neimanmarcus.com/c/beauty-mens-cologne-grooming-cologne-cat10470747?page=",
                "https://www.neimanmarcus.com/c/beauty-mens-cologne-grooming-hair-skin-care-cat11270760?page=",
                "https://www.neimanmarcus.com/c/beauty-mens-cologne-grooming-shaving-essentials-cat56650749?page="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        )
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
            vat_rate = 1.08
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            # country_url = '.com/en-gb/',
            vat_rate = 1.06
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            # country_url = '.com/en-de/',
            vat_rate = 1.07
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            # country_url = '.com/en-ca/',
            vat_rate = 1.05
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            # country_url = '.com/en-au/',
            vat_rate = 1.06
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            # country_url = '.com/en-jp/',
            vat_rate = 1.064
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            # country_url = '.com/en-kr/',
            vat_rate = 1.128
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            # country_url = '.com/en-sg/',
            vat_rate = 1.093
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            # country_url = '.com/en-hk/',
            vat_rate = 1.076
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            # country_url = '.com/en-ru/',
            vat_rate = 1.0
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            # country_url = '.com/en-no/',
            vat_rate = 1.093
        )
        )



