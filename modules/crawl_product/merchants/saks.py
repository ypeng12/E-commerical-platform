from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from utils.utils import *
import requests

class Parser(MerchantParser):

    def _check_shipped(self, checkshipped, item, **kwargs):
        if item['country'] != 'US' and checkshipped:
            return True
        else:
            return False

    def _checkout(self, checkout, item, **kwargs):
        pid = checkout.xpath('.//input[@name="productID"]/@value').extract_first()
        if not pid:
            return True

        ajax_link = 'https://www.saksfifthavenue.com/on/demandware.store/Sites-SaksFifthAvenue-Site/en_US/Product-AvailabilityAjax?quantity=1&readyToOrder=false&pid=%s' %pid
        response = requests.get(ajax_link, headers=bot_header)
        data = json.loads(response.text)

        if data['availability']['buttonName'] == 'SOLD OUT':
            return True
        else:
            item['error'] = 'ignore'
            item['tmp'] = data
            return False

    def _parse_json(self, obj, item, **kwargs):
        item['tmp'] = obj

    def parse_prices(self, item, price, obj, **kwargs):

        if price['list_price']['local_currency_code'] == item['currency']:
            item['originlistprice'] = price['list_price']['local_currency_value']
            item['originsaleprice'] = price['sale_price']['local_currency_value']
            self.prices(item['tmp'], item, **kwargs)
        elif item['currency'] == 'USD' and price['list_price']['local_currency_code'] != 'USD':
            item['originlistprice'] = price['list_price']['usd_currency_value']
            item['originsaleprice'] = price['sale_price']['usd_currency_value']
            self.prices(item['tmp'], item, **kwargs)
        else:
            rate = get_currency_rate('USD', item['currency'])
            item['originlistprice'] = str(float(price['list_price']['usd_currency_value']) * rate)
            item['originsaleprice'] = str(float(price['sale_price']['usd_currency_value']) * rate)
            item['listprice'] = float(item['originlistprice'])
            item['saleprice'] = float(item['originsaleprice'])

    def _parse_multi_items(self, response, item, **kwargs):
        obj = item['tmp']
        item['sku'] = obj['ProductDetails']['main_products'][0]['product_id']
        skus = dict()
        tmp = obj['ProductDetails']['main_products'][0]['skus']['skus']
        for sku in tmp:
            if sku['color_id'] not in skus:
                skus[sku['color_id']] = {}
            skus[sku['color_id']][sku['size_id']] = sku
        colors = obj['ProductDetails']['main_products'][0]['colors']['colors']
        sizes = obj['ProductDetails']['main_products'][0]['sizes']['sizes']
        if len(colors) == 0 and item['category'] == 'e':
            colors = [{'is_waitlistable': False, 'counter': 1, 'label': '', 'value': '', 'colorize_image_url': '', 'is_soldout': False, 'is_value_an_image': False, 'id': -1}]
        media = obj['ProductDetails']['main_products'][0]['media']

        img_path = 'https:' + media['images_server_url'] + media['images_path']
        images = media['images']
        cover = img_path + images[0]

        # price = obj['ProductDetails']['main_products'][0]['skus']['skus'][-1]['price']
        # self.parse_prices(item, price, obj, **kwargs)

        for color in colors:
            item_color = deepcopy(item)

            item_color['color'] = color['label'].strip().upper()
            item_color['sku'] = '%s%s' % (item['sku'], item_color['color'])
            if color['is_soldout'] == True:
                item_color['originsizes'] = ''
                item_color['sizes'] = ''
                item_color['error'] = 'Out Of Stock'
                yield item_color
                continue
            color_id = color['id']
            colors_price = obj['ProductDetails']['main_products'][0]['skus']['skus']
            for color_price in colors_price:

                if color_price['color_id'] == color_id and 'sold out' not in color_price['status_label'].split('>')[0].strip().lower():
                    self.parse_prices(item_color, color_price['price'], obj, **kwargs)
                    break
            
            # detail = detail.replace("&#189;", '').replace("&#190;", '')
            item_color['description'] = item['description'] + '\n' + item_color['color']

            if len(colors) > 1:
                item_color['cover'] = img_path + color['colorize_image_url']
            else:
                item_color['cover'] = cover

            item_color['images'] = [item_color['cover']]

            # for img in images:
            #   imgurl = img_path + img
            #   if imgurl not in item_color['images']:
            #       item_color['images'].append(imgurl)
            if 'error' in item:
                del item['error']
            item_color['originsizes'] = []
            item_color['originsizes2'] = []
            if len(skus) > 0:

                if item_color['category'] in ['s','c']:
                    sizeinfo = ''
                    for size in sizes:
                        try:
                            sku = skus[color_id][size['id']]
                        except Exception as ex:
                            continue

                        memo = ''
                        if sku['status_alias'] == 'preorder':
                            memo = ':p'
                        elif sku['status_alias'] != 'available':
                            continue
                        sku1 = sku
                        item_color['originsizes'].append(size['value'].strip() + memo)
                        item_color['originsizes2'].append(size['value'].split('(')[0].split('/')[0].strip())

                    self.sizes(item_color['originsizes'], item_color, **kwargs)
                    yield item_color
                    continue

                elif item_color['category'] in ['b']:
                    try:
                        sku = skus[color_id][-1]
                    except:
                        sku = skus[color_id][0]

                    if sku['status_alias'] in ['waitlist']:
                        item_color['error'] = 'Out Of Stock'
                        item_color['originsizes'] = ''
                        item_color['sizes'] = ''
                        yield item_color
                        continue
                    if sku['status_alias'] in ['available', 'preorder']:
                        memo = ':p' if sku['status_alias'] == 'preorder' else ''
                        item_color['originsizes'] = ['IT' + memo]
                    else:
                        item_color['sizes'] = ''
                        item_color['originsizes'] = ''
                    self.sizes(item_color['originsizes'], item_color, **kwargs)
                    yield item_color
                    continue
                elif item_color['category'] in ['e']:
                    size_ids = {}
                    for size in sizes:
                        size_ids[size['id']] = size['value']
                    if size_ids:
                        for sku in list(skus[color_id].values()):
                            item_size = deepcopy(item_color)

                            try:
                                price = sku['price']
                                self.parse_prices(item_size, price, obj, **kwargs)
                            except:
                                item_size['error'] = 'Out Of Stock'
                                item_size['originsizes'] = ''
                                item_size['sizes'] = ''
                                yield item_size
                                continue

                            sizeid = size_ids[sku['size_id']]
                            item_size['sku'] = item['sku'] + sizeid.upper()

                            if sku['status_alias'] in ['waitlist']:
                                item_size['error'] = 'Out Of Stock'
                                item_size['originsizes'] = ''
                                item_size['sizes'] = ''
                                yield item_size
                                continue
                            if sku['status_alias'] in ['available', 'preorder']:
                                memo = ':p' if sku['status_alias'] == 'preorder' else ''
                                item_size['originsizes'] = [size_ids[sku['size_id']] + memo]
                            else:
                                item_size['sizes'] = ''
                                item_size['originsizes'] = ''
                            self.sizes(item_size['originsizes'], item_size, **kwargs)
                            yield item_size
                            continue
                    else:
                        try:
                            sku = skus[color_id][-1]
                        except:
                            sku = skus[color_id][0]

                        if sku['status_alias'] in ['waitlist']:
                            item_color['error'] = 'Out Of Stock'
                            item_color['originsizes'] = ''
                            item_color['sizes'] = ''
                            yield item_color
                            continue
                        if sku['status_alias'] in ['available', 'preorder']:
                            memo = ':p' if sku['status_alias'] == 'preorder' else ''
                            try:
                                osize = [sizes[0]['value'] + memo]
                            except:
                                osize = ['IT' + memo]
                            item_color['originsizes'] = osize
                        else:
                            item_color['sizes'] = ''
                            item_color['originsizes'] = ''
                        self.sizes(item_color['originsizes'], item_color, **kwargs)
                        yield item_color
                        continue
                elif item_color['category'] in ['a']:
                    sku1 = sku
                    for size in sizes:
                        try:
                            sku = skus[color_id][size['id']]
                        except Exception as ex:
                            try:
                                skus[color_id][-1]
                            except:
                                color_id = 0
                                sku = skus[color_id][0]
                        if sku['status_alias'] != 'available':
                            continue
                        sku1 = sku                        
                        item_color['originsizes'].append(size['value'].strip())
                    if item_color['originsizes']:
                        item_color['originsizes'] = ['IT']
                    elif sku1['status_alias'] == 'available':
                        item_color['originsizes'] = ['IT']
                    elif sku1['status_alias'] == 'preorder':
                        item_color['originsizes'] = ['IT:p']
                    elif not color['is_soldout']:
                        item_color['originsizes'] = ['IT']
                    else:
                        item_color['sizes'] = ''
                        item_color['originsizes'] = ''
                    self.sizes(item_color['originsizes'], item_color, **kwargs)
                    yield item_color


    # def _sku(self, data, item, **kwargs):
    #   item['sku'] = data.extract()[0].split('prd_id=')[-1].split('&')[0]

    # def _prices(self, prices, item, **kwargs):
    #   if len(prices) == 1:
    #       item['originlistprice'] = prices.xpath('./span/text()').extract()[-1].strip()
    #       item['originsaleprice'] = prices.xpath('./span/text()').extract()[-1].strip()
    #   else:
    #       item['originlistprice'] = prices[0].xpath('./span/text()').extract()[-1].strip()
    #       item['originsaleprice'] = prices[1].xpath('./span/text()').extract()[-1].strip()

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _page_num(self, data, **kwargs):
        pages = int(data.replace(',', '').replace(' ', '')) / 60
        return pages

    def _list_url(self, i, response_url, **kwargs):
        if '?' in response_url:
            url = response_url + "&Nao=" + str(i * 60)
        else:
            url = response_url + "?Nao=" + str(i * 60)
        return url

    def _parse_images(self, response, **kwargs):
        images = []
        tmp = response.xpath('//script[contains(text(),"ProductDetails")]/text()').extract_first()
        obj = json.loads(tmp)
        colors = obj['ProductDetails']['main_products'][0]['colors']['colors']
        media = obj['ProductDetails']['main_products'][0]['media']

        img_path = 'https:' + media['images_server_url'] + media['images_path']
        if len(colors) > 1:
            for color in colors:
                if color['label'].lower() in response.meta['sku'].lower():
                    image = img_path + color['colorize_image_url']
                    images.append(image)
        else:
            for img in media['images']:
                image = img_path + img
                images.append(image)
        return images

    def _parse_look(self, item, look_path, response, **kwargs):
        # self.logger.info('==== %s', response.url)

        try:
            outfits = response.xpath('//section[@class="shop-the-look container"]//article//a/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.url
        item['cover'] = self.get_image(response)+'?wid=760&hei=900&fmt=jpg'
        item['products'] = [str(outfit).split('prd_id=')[-1] for outfit in outfits]
        item['products'] = list(set(item['products']))
        # self.logger.debug(item)

        yield item

    def get_image(self, response):
        codes = response.xpath('//link[@rel="canonical"]/@href').extract()
        code = codes[0].split('prd_id=')[-1].split('&')[0]

        tmp = response.xpath('//script/text()').extract()
        for script in tmp:
            if 'ProductDetails' in script:
                tmp = script
                break
        tmp = tmp.split(' = ')[-1]

        try:
            obj = json.loads(tmp)
        except:
            return ''
        media = obj['ProductDetails']['main_products'][0]['media']

        img_path = 'https:' + media['images_server_url'] + media['images_path']

        images = media['images']
        cover = img_path + images[0]
        return cover

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or '/' in info or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info  

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[contains(@class,"search-results-coun")]//text()').extract_first().strip().lower().split("of")[-1].split("item")[0].strip().replace(',',''))
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'saks'
    merchant = 'Saks Fifth Avenue'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@id="pc-top"]/div[1]/span/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//*[@id="product-container"]/div/div[3]',
            designer = './/span[@class="product-designer-name"]/text()',
            link = './a[1]/@href',
            ),
        product = OrderedDict([
            ('checkshipped',('//p[@class="product__label-message-display"]/a/text()', _parser.check_shipped)),
            ('checkout',('//html', _parser.checkout)),
            # ('sku',('//span[@itemprop="url"]/text()', _parser.sku)),
            ('name', '//h1[@class="product-overview__short-description"]/text()'),
            ('designer', '//div[@class="product-details"]/article//h2[@class="product-overview__brand"]/a/text()'),
            ('color','//input[@id="pr_color"]/@value'),
            ('description', ('//section[contains(@class, "product-description")]//text()',_parser.description)),
            # ('prices', ('//div[@class="product-pricing"]//dd', _parser.prices)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=57236,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//section[@class="product-description"]//text()',         
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    json_path = dict(
        method = _parser.parse_json,
        obj_path = '//script',
        keyword = 'ProductDetails',
        flag = ('strat_flag','end_flag'),#when don't need split use it
        field = dict(),
        )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/All-Jewelry/shop/_/N-52flr0?Nao=0",
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/Fine-Jewelry/shop/_/N-52k3nz?Nao=0",
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/Demi-Fine-Jewelry/shop/_/N-52khq7?Nao=0",
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/Fashion-Jewelry/shop/_/N-52k9ke/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/Watches/For-Her/shop/_/N-52flr9/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/Sunglasses/shop/_/N-52flre/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/shop/_/N-52flrb/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306418050+1553"
            ],
            b = [
                "https://www.saksfifthavenue.com/Handbags/shop/_/N-52jzot?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306622828+1553"
            ],
            c = [
                "https://www.saksfifthavenue.com/Women-s-Apparel/shop/_/N-52flog/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306418048+1553"
            ],
            s = [
                "https://www.saksfifthavenue.com/Shoes/shop/_/N-52k0s7/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306622397+1553"
            ],
            e = [
                "https://www.saksfifthavenue.com/Beauty/View-All-Beauty/shop/_/N-52flrm/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306418051+1553"
            ]
        ),
        m = dict(
            a = [
                "https://www.saksfifthavenue.com/Men/Accessories/Belts/shop/_/N-52flsw?Nao=0",
                "https://www.saksfifthavenue.com/Men/Accessories/Cuff-Links-and-Tie-Bars/shop/_/N-52kg40?Nao=0",
                "https://www.saksfifthavenue.com/Men/Accessories/Jewelry/shop/_/N-52kg41?Nao=0",
                "https://www.saksfifthavenue.com/Men/Accessories/Hats-Scarves-and-Gloves/shop/_/N-52fuiu?Nao=0",
                "https://www.saksfifthavenue.com/Men/Accessories/Sunglasses-and-Opticals/shop/_/N-52flsy?Nao=0",
                "https://www.saksfifthavenue.com/Men/Accessories/Ties-and-Formal-Accessories/shop/_/N-52jyvs?Nao=0",
                "https://www.saksfifthavenue.com/Men/Accessories/Watches/shop/_/N-52kg3z?Nao=0",
                "https://www.saksfifthavenue.com/Jewelry-and-Accessories/Watches/For-Him/shop/_/N-52flra?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306418206+1553"
            ],
            b = [
                "https://www.saksfifthavenue.com/Men/Accessories/Bags-and-Leather-Goods/shop/_/N-52kdfq?Nao=0",
                "https://www.saksfifthavenue.com/Men/Accessories/Wallets-and-Money-Clips/shop/_/N-52ki99?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306643320+1553"
            ],
            c = [
                "https://www.saksfifthavenue.com/Men/Apparel/shop/_/N-52flsg?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306418192+1553"
            ],
            s = [
                "https://www.saksfifthavenue.com/Men/Shoes/shop/_/N-52flst/Ne-6lvnb5?Nao=0",
                "https://www.saksfifthavenue.com/search/EndecaSearch.jsp?N=306418205+1553"
            ],
        ),
        u = dict(
            a = [
                "https://www.saksfifthavenue.com/Home/shop/_/N-52flom/Ne-6lvnb5?Nao=0"
            ]
        )
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cookies = dict(
                E4X_COUNTRY='US; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='USD; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        CN = dict(
            area = 'CN',
            currency = 'CNY',
            thousand_sign = ',',
            cookies = dict(
                E4X_COUNTRY='CN; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='CNY; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        JP = dict(
            currency = 'JPY',
            cookies = dict(
                E4X_COUNTRY='JP; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='JPY; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        KR = dict(
            currency = 'KRW',
            cookies = dict(
                E4X_COUNTRY='KR; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='KRW; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        SG = dict(
            currency = 'SGD',
            cookies = dict(
                E4X_COUNTRY='SG; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='SGD; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        HK = dict(
            currency = 'HKD',
            cookies = dict(
                E4X_COUNTRY='HK; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='HKD; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        GB = dict(
            currency = 'GBP',
            cookies = dict(
                E4X_COUNTRY='GB; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='GBP; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        RU = dict(
            currency = 'RUB',
            cookies = dict(
                E4X_COUNTRY='RU; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='RUB; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        CA = dict(
            currency = 'CAD',
            cookies = dict(
                E4X_COUNTRY='CA; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='CAD; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        AU = dict(
            currency = 'AUD',
            cookies = dict(
                E4X_COUNTRY='AU; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='AUD; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        DE = dict(
            currency = 'EUR',
            cookies = dict(
                E4X_COUNTRY='DE; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='EUR; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),
        NO = dict(
            currency = 'NOK',
            cookies = dict(
                E4X_COUNTRY='NO; Path=/; Domain=.saksfifthavenue.com',
                E4X_CURRENCY='NOK; Path=/; Domain=.saksfifthavenue.com',
                TLTHID='8EA1AE14A3C310A30C7E9430F623FBA7; Path=/; Domain=.saksfifthavenue.com',
                TS54c0f7=' 0484bc316057f393d98935a7b63b8182476036e46c11982b56710d6a5562781050de5786286023f2f06d1ea860ac0ec5f7cdf143866d39d0b12f6551077623711809f75107601fb840b6a4ae5283d66affffffff2396c135d4d3511daf1a552cf2a7fa2c7d8b0044d4d3511d48de5bd5f2a7fa2c9660146b5fdc6280; Path=/;'
            )
        ),

        )

        


