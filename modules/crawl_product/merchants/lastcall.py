from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
from base64 import b64encode
import time
import json
from lxml import etree
from urllib.parse import urljoin
from utils.utils import *

class Parser(MerchantParser):

    def _page_num(self, data, **kwargs):
        pages = int(data.split('of')[-1].strip())
        return pages

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _description(self, description, item, **kwargs):
        desc_str = []
        desc_li = description.extract()
        # desc_end = description.xpath('.//div[@class="productBottom"]//text()').extract_first()
        for desc in desc_li:
            if desc.strip():
                desc_str.append(desc.strip())
        item['description'] = '.\n'.join(desc_str)

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//p[@class="lbl_ItemPriceSingleItem product-price"]/text()').extract()
        if saleprice:
            saleprice = saleprice[0].strip()
            listprice = saleprice
        else:
            try:
                listprice = prices.xpath('.//div[@class="price-adornments-elim-suites"]/span[@class="item-price"]/text()').extract()[0]
                saleprice = prices.xpath('.//p[@class="line-item-promo-elim-suites"]//span[@class="promo-price"]/text()').extract()[0]
            except:
                listprice = prices.xpath('.//div[@class="price-adornments-elim-suites"]/span[@class="item-price"]/text()').extract_first()
                saleprice = prices.xpath('.//span[@class="pos1override item-price"]/text()').extract_first()
        item['originlistprice'] = listprice.strip() if listprice else saleprice.strip()
        item['originsaleprice'] = saleprice.strip()

    def _parse_multi_items(self, response, item, **kwargs):
        item['url'] = item['url'].split('?')[0]
        productId = response.url.split('/p.prod')[0].split('/')[-1].split('_cat')[0]
        
        json_url = 'https://www.lastcall.com/product.service'
        form_data = {
                    'data': '$b64$%s' % b64encode('{"ProductSizeAndColor":{"productIds":"%s"}}' % productId),
                    "sid":"getSizeAndColorData",
                    "bid":"ProductSizeAndColor",
                    "timestamp":int(time.time())
        }
        result = getwebcontent(json_url,form_data)
        json_data = json.loads(result)
        product_json = json_data['ProductSizeAndColor']['productSizeAndColorJSON']
        json_dic = json.loads(product_json[1:-1])
        json_data = json_dic['skus']
        colors_sizes = {}
        for product in json_data:
            color = product.get('color', '').split('?')[0]
            if color not in colors_sizes:
                colors_sizes[color] = []
            colors_sizes[color].append(product.get('size', ''))
            if 'sku' not in item:
                item['sku'] = product['cmosItemCode']
        skus = []
        for color,sizes in list(colors_sizes.items()):
            item['images'] = ''
            item_color = deepcopy(item)
            item_color['color'] = color
            try:
                item_color['originsizes'] = sizes
            except:
                item_color['originsizes'] = ''

            item_color['sku'] = '%s_%s' % (item_color['sku'], color.upper())
            skus.append(item_color['sku'])
            if color.upper() not in item_color['name']:
                item_color['name'] += ', %s' % color.upper()
            skuimgs = response.xpath('//li[contains(@class, "color-picker") and @data-color-name="' + color + '"]/@data-sku-img').extract()
            if skuimgs:
                skuimgs = skuimgs[0]
                obj_images = json.loads(skuimgs)
                if len(obj_images) > 1:
                    item_color['images'] = []
                if 'm*' in obj_images:
                    mimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images[
                        'm*']
                    if item_color['images']:
                        item_color['images'][0] = mimg
                    else:
                        item_color['images'] = [mimg]
                if 'a*' in obj_images:
                    aimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images[
                        'a*']
                    if len(item_color['images']) >= 2:
                        item_color['images'][1] = aimg
                    else:
                        item_color['images'].append(aimg)
                if 'b*' in obj_images:
                    bimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images[
                        'b*']
                    if len(item_color['images']) >= 3:
                        item_color['images'][2] = bimg
                    else:
                        item_color['images'].append(bimg)
                if 'c*' in obj_images:
                    cimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images[
                        'c*']
                    if len(item_color['images']) >= 4:
                        item_color['images'][3] = cimg
                    else:
                        item_color['images'].append(cimg)
            else:
                imgs = response.xpath('//div[@class="img-wrap"]/img/@src').extract()
                for i in range(len(imgs)):
                    if 'http' not in imgs[i]:
                        imgs[i] = urljoin('https://images.lastcall.com/', imgs[i])
                item_color['images'] = imgs

            item_color['cover'] = item_color['images'][0]
            if item_color['category'] in ['b', 'a','e'] and not ';'.join(item_color['originsizes']):
                item_color['originsizes'] = ['IT']
            self.sizes(result, item_color, **kwargs)

            # if item_color['category'] == 's' or item_color['category'] == 'c':
            #     item_color['sizes'] = []
            #     for size in sizes:
            #         if size != 'IT':
            #             size = size.replace('\\', '').replace('B', '').replace('1/2', '.5').replace(' ', '').split(
            #             'IT')[0].strip().split('/')[0].split('R ')[0].split('L ')[0].split('S ')[0].split('EU')[0]

            #         if 'FR' in size.split('(')[0]:
            #             size = 'FR' + size.split('FR')[0]
            #         if size:
            #             if size.split('(')[0][-1] == 'P':
            #                 size = size.split('P')[0]
            #         if 'R' in size and 'LARGE' not in size and 'FR' not in size:
            #             size = size.replace('R', '')
            #         if 'D' in size and 'MEDIUM' not in size:
            #             size = size.replace('D', '')

            #         if item_color['category'] == 's':
            #             size = toItSize(size, item_color['gender'])
            #         elif item_color['category'] == 'c':
            #             size = clothToItSize(
            #                 size.split('(')[0], item_color['gender'])
            #         if 'IT' in size:
            #             item_color['sizes'].append(size)

            #     item_color['sizes'] = ';'.join(item_color['sizes'])

            #     if len(item_color['sizes']) == 0 and item_color['category'] != 'a':
            #         item_color['sizes'] = ''
            #         item_color['originsizes'] = ''
            #         item_color['error'] = 'Out Of Stock'

            # elif item_color['category'] in ['b', 'a','e']:
            #     if not item_color['originsizes']:
            #         item_color['sizes'] = 'IT'
            #         item_color['originsizes'] = 'IT'
            #         # item_color['error'] = 'Out Of Stock'
            #     else:
            #         item_color['sizes'] = 'IT'

            # if item_color['sizes'] and item_color['sizes'][-1] != ';':
            #     item_color['sizes'] += ';'
            # if item_color['originsizes'] and item_color['originsizes'][-1] != ';':
            #     item_color['originsizes'] += ';'

            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _parse_item_url(self, response, **kwargs):
        url = response.url
        categoryid = 'cat' + url.split('/cat')[1].split('_')[0]
        page = int(url.split('page=')[-1])
        url = 'https://www.lastcall.com/category.service'
        data = '{"GenericSearchReq":{"pageOffset":%s,"pageSize":"30","refinements":"","selectedRecentSize":"","activeFavoriteSizesCount":"0","activeInteraction":"true","mobile":false,"sort":"PCS_SORT","definitionPath":"/nm/commerce/pagedef_rwd/template/EndecaDriven","userConstrainedResults":"true","updateFilter":"false","rwd":"true","advancedFilterReqItems":{"StoreLocationFilterReq":[{"allStoresInput":"false","onlineOnly":""}]},"categoryId":"%s","sortByFavorites":false,"isFeaturedSort":false,"prevSort":""}}' % (page-1, categoryid)
        data = {
            'data': '$b64$%s$$' % b64encode(data),
            'service': 'getCategoryGrid',
            'sid': 'getCategoryGrid',
            'bid': 'GenericSearchReq',
            'timestamp': int(time.time())
        }

        result = getwebcontent(url, data)
        result = json.loads(result)
        html = etree.HTML(result['GenericSearchResp'][
                          'productResults'])
        products = html.xpath('//li[@class="category-item"]')
        for quote in products:
            href = quote.xpath(
                './/a[@id="productTemplateId"]/@href')
            designer = quote.xpath(
                './/div[@class="productdesigner OneLinkNoTx"]//text()')
            if len(href) == 0:
                continue
            # elif len(designer) != 0 and not check_designer(designer[0].strip().upper()):
            #     self.crawler.stats.inc_value("uncarried")
            #     continue
            href = 'https://www.lastcall.com%s' % href[0]
            yield href,designer

    def _parse_images(self, response, **kwargs):
        color = response.meta['sku'].split('_')[-1].upper()
        images = []
        skuimgs = response.xpath('//li[contains(@class, "color-picker") and @data-color-name="' + color + '"]/@data-sku-img').extract()
        if skuimgs:
            skuimgs = skuimgs[0]
            obj_images = json.loads(skuimgs)
            if 'm*' in obj_images:
                mimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images['m*']
                images = [mimg]
            if 'a*' in obj_images:
                aimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images['a*']
                images.append(aimg)
            if 'b*' in obj_images:
                bimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images['b*']
                images.append(bimg)
            if 'c*' in obj_images:
                cimg = 'https://lastcall.scene7.com/is/image/lastcall/%s?&wid=400&height=500' % obj_images['c*']
                images.append(cimg)
        else:
            imgs = response.xpath('//div[@class="img-wrap"]/img/@src').extract()
            images = imgs
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
            logger.debug(traceback.format_exc())
            return

        if len(products["product_cmos_item"])==1:
            return self.parseWithOutCover(response, item)
        else:
            return self.parseWithCover(response, products, item)

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
        item['cover'] = response.xpath('//img[@data-static-main-image]/@src').extract_first()
        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'Height' in info or '/' in info or 'Fit' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info  


_parser = Parser()

class Config(MerchantConfig):
    name = 'lastcall'
    merchant = 'LastCall.com'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//li[@class="pagingDots"]/following-sibling::li/a/text()',
            parse_item_url = _parser.parse_item_url,
            # items = '//ul[@class="category-items"]/li',
            # designer = './/div[@class="productdesigner OneLinkNoTx"]/text()',
            # link = './/a[@id="productTemplateId"]/@href',
            ),
        product = OrderedDict([
            ('checkout',('//input[@value="Add to Shopping Bag"]', _parser.checkout)),
            # ('sku','//div[@itemprop="offers"]/@catalog-item'),
            ('name','//span[@class="prodDisplayName"]/text()'),
            ('designer','//h1[@class="product-name elim-suites"]//text()'),
            ('description',('//div[@class="product-details-info elim-suites"]//li/text()', _parser.description)),
            ('prices',('//html', _parser.prices)),
            #noship TODO:https://www.neimanmarcus.com/en-cn/Stuart-Weitzman-Pure-Crinkled-Napa-Leather-Bootie-Boots/prod204520175_cat45140734__/p.prod
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=61850,
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
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.lastcall.com/Hers/Jewelry/cat5730008_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Hers/Watches/cat9910036_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Hers/Scarves-Hats-Gloves/cat12800000_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Hers/Accessories/cat7780000_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Hers/Sunglasses/cat7640004_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Hers/Gifts-Fragrance/cat5960000_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Clearance/Accessories/cat5910025_cat1230000_cat000000/c.cat?page=",
                "https://www.lastcall.com/Clearance/Jewelry/cat5910024_cat1230000_cat000000/c.cat?page=",
            ],
            b = [
                'https://www.lastcall.com/Hers/Handbags/cat5730007_cat000001_cat000000/c.cat?page=',
                'https://www.lastcall.com/Hers/Handbags/cat5910023_cat6400019_cat1230000/c.cat?page=',
            ],
            c = [
                "https://www.lastcall.com/Hers/Womens-Apparel/cat6150001_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Hers/Plus-Size/cat7030000_cat000001_cat000000/c.cat?page=",
                "https://www.lastcall.com/Clearance/Womens-Apparel/cat6400019_cat1230000_cat000000/c.cat?page=",
            ],
            s = [
                'https://www.lastcall.com/Hers/Shoes/cat5730006_cat000001_cat000000/c.cat?page=',
                'https://www.lastcall.com/Hers/Shoes/cat5910022_cat6400019_cat1230000/c.cat?page=',
            ],
            e = [
                "https://www.lastcall.com/Hers/Fragrance-Beauty/cat3700007_cat000001_cat000000/c.cat?page=",
            ]
        ),
        m = dict(
            a = [
                "https://www.lastcall.com/Men/Accessories/cat6080009_cat5950072_cat1230000/c.cat?page=",
                "https://www.lastcall.com/Accessories/Ties/cat5920003_cat5920002_cat000002/c.cat?page=",
                "https://www.lastcall.com/Accessories/Watches-Jewelry/cat8820002_cat5920002_cat000002/c.cat?page=",
                "https://www.lastcall.com/Accessories/Scarves-Hats-Gloves/cat5920034_cat5920002_cat000002/c.cat?page=",
                "https://www.lastcall.com/Accessories/Scarves-Hats-Gloves/cat5920034_cat5920002_cat000002/c.cat?page=",
                "https://www.lastcall.com/Accessories/Belts/cat5920029_cat5920002_cat000002/c.cat?page=?page=",
                "https://www.lastcall.com/Accessories/Sunglasses/cat5920030_cat5920002_cat000002/c.cat?page=",
                "https://www.lastcall.com/His/Gifts-Cologne/cat5920022_cat000002_cat000000/c.cat?page="
            ],
            b = [
                'https://www.lastcall.com/Accessories/Wallets-Bags/cat5920017_cat5920002_cat000002/c.cat?page=',
                'https://www.lastcall.com/Hers/Handbags/cat5910023_cat6400019_cat1230000/c.cat?page=',
            ],
            c = [
                "https://www.lastcall.com/His/Mens-Apparel/cat5730010_cat000002_cat000000/c.cat?page=",
                "https://www.lastcall.com/Men/Sweaters-Sweatshirts/cat5950082_cat5950072_cat1230000/c.cat?page=",
                "https://www.lastcall.com/Men/Shirts/cat16100000_cat5950072_cat1230000/c.cat?page=",
                "https://www.lastcall.com/Men/Suits-Sportcoats/cat11360025_cat5950072_cat1230000/c.cat?page=",
                "https://www.lastcall.com/Men/Jackets-Coats/cat5950083_cat5950072_cat1230000/c.cat?page=",
                "https://www.lastcall.com/Men/Pants-Shorts/cat5910031_cat5950072_cat1230000/c.cat?page=",
            ],
            s = [
                'https://www.lastcall.com/His/Shoes/cat5920005_cat000002_cat000000/c.cat?page=',
                'https://www.lastcall.com/Men/Shoes/cat5950084_cat5950072_cat1230000/c.cat?page=',
            ],
            e = [
                "https://www.lastcall.com/His/Cologne-Grooming/cat7580005_cat000002_cat000000/c.cat?page=",
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'www.',
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
            country_url = 'intl.',
            # vat_rate = 1.058,
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.064
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.128
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.093
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.076
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.10
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.0
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.076
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.083
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.067
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            country_url = 'intl.',
            # vat_rate = 1.093
        ),

        )

        


