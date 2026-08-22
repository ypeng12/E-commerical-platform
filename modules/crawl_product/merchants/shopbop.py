from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from utils.utils import *
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if 'eastdane.' in item['url']:
            return True
        add_to_bag = checkout.xpath('.//span[@class="add-to-cart-button-text "]')
        if not add_to_bag:
            return True
        sold_out = checkout.xpath('.//span[@class="out-of-stock-button-text "]')
        if sold_out:
            return True
        else:
            return False

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[@class="pdp-price"]/text()').extract()
        listprice = prices.xpath('.//span[@class="retail-price"]/text()').extract()
        if listprice:
            item['originsaleprice'] = saleprice[0]
            item['originlistprice'] = listprice[0]
        else:
            item['originlistprice'] = item['originsaleprice'] = saleprice[0]

        # if item['country'] == 'CN':
        #   item['originsaleprice'] = item['originsaleprice'].replace(u'CN\xa5','').replace(u'\uffe5','')
        #   item['originlistprice'] = item['originlistprice'].replace(u'CN\xa5','').replace(u'\uffe5','')

    def _description(self, desc, item, **kwargs):
        description = []
        for des in desc.extract():
            if des.strip():
                description.append(des.strip())
        item['description'] = '\n'.join(description)
        if item['designer'].upper() == 'WHAT GOES AROUND COMES AROUND':
            item['condition'] = 'p'

    def _parse_json(self, obj, item, **kwargs):
        item['tmp'] = obj

    def _parse_multi_items(self, response, item, **kwargs):
        category = item['category']

        data = json.loads(response.xpath('//script[@type="sui-state"]//text()').extract_first())
        final_sale = data['product']['styleColors'][0]['prices'][0]['onFinalSale']
        memo = ':f' if final_sale else ''

        productData = item['tmp']
        sizeDict = {}
        for k, v in productData['sizes'].items():
            sizeDict[v['sizeCode']] = k

        skus = []

        for colorid, color in productData['colors'].items():
            item_color = deepcopy(item)
            item_color['color'] = color['colorName'].upper()
            imgs = []
            bimgs = []
            for key, img in color['images'].items():
                imgs.append(img['main'])
                bimgs.append(img['zoom'])
            item_color['images'] = imgs
            item_color['cover'] = imgs[0]
            for img in imgs:
                if 'q1' in img:
                    item_color['cover'] = img

            item_color['sku'] += colorid
            skus.append(item_color['sku'])

            sizes = color['sizes']
            item_color['originsizes'] = []
            if len(sizes) == 0:
                item_color['originsizes'] = ""
                item_color['sizes'] = ""
                item_color['error'] = 'Out Of Stock'
            else:
                if category == 'b':
                    osize = 'One Size' + memo
                    item_color['originsizes'] = [osize]
                else:
                    size_type_path = '//div[@id="size-fit-note"]/b/text()'
                    size_type = response.xpath(size_type_path).extract_first()
                    size_tag = size_type if size_type and 'Sizing' not in size_type else ''
                    if category in ['a', 'c', 's', 'e', 'h']:
                        for key in sizes:
                            if not sizeDict[key].isdigit():
                                size_tag = ''
                            size = sizeDict[key]
                            osize = size_tag + size.strip() + memo
                            item_color['originsizes'].append(osize)
            self.sizes(item_color['originsizes'], item_color, **kwargs)
                        
            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _page_num(self, data, **kwargs):
        pages = int(data.strip().split(' ')[0].replace(',',''))/100

        if int(data.strip().split(' ')[0].replace(',',''))%100 == 0:
            pages = pages - 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + str((i-1) * 100)

        return url

    def _get_review_url(self, response, **kwargs):
        review_urls = response.xpath('//div[@class="pagination"]/div/a/@href').extract()
        if review_urls:

            urls = []
            for review_url in review_urls:
                if review_url not in urls:
                    urls.append(review_url)
                    review_url = urljoin(response.url, review_url)
                    yield review_url
        else:
            yield response.url

    def _reviews(self, response, **kwargs):
        for quote in response.xpath('//div[@class="reviews-container celwidget"]//div[contains(@class,"row review")]'):
            review = {}

            review['user'] = quote.xpath('./div[@class="profile g3"]/div[1]/text()').extract_first().strip()
            review['title'] = quote.xpath('.//span[@class="review-title"]/text()').extract_first().strip()
            review['content'] = quote.xpath('.//div[@class="review-text"]/text()').extract_first().strip()
            review['score'] = float(quote.xpath('.//img[@class="rating-stars"]/@src').extract_first().strip().split('stars_')[-1].split('_1-0.png')[0])
            review['review_time'] = ''

            yield review

    def _designer_desc(self, desc, item, **kwargs):
        descriptions = desc.extract()
        desc_li = []
        for description in descriptions:
            description = description.strip()
            if not description:
                continue
            desc_li.append(description)
        item['description'] = ''.join(desc_li)

    def _parse_images(self, response, **kwargs):
        scripts = response.xpath('//script/text()').extract()
        sku1=response.xpath("//span[@itemprop='sku']/@content").extract()[0]
        for script in scripts:
            if 'var productDetail' in script:
                break
        datas = script.split('var productDetail =')[-1].split(';')[0]
        datas = json.loads(datas)
        colors = datas['colors']
        images = {}
        for colorid, color in colors.items():
            pid =sku1+ colorid
            images[pid] = []
            imagesToSort = []
            for key, img in color['images'].items():
                imagesToSort.append(img['main'])
            images[pid] = sorted(imagesToSort)
        return images

    def _parse_look(self, item, look_path, response, **kwargs):
        look_api = 'https://api.shopbop.com/public/products/%s/crosssells' %kwargs['sku'][:-5]
        data = get_json_data(look_api)

        products = data['crossSells'][0]['products']
        outfits = []

        for product in products:
            outfits.append(product['productDetailUrl'])

        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.url
        item['cover'] = 'https://m.media-amazon.com/images/G/01/Shopbop/p' + products[0]['colors'][0]['images'][0]['src']
        item['products']= list(map(lambda x:('https://www.shopbop.com'+str(x).split('?')[0]), list(set(outfits))))

        yield item

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = json.loads(response.xpath(swatch_path['current_path']).extract()[0])
        colors = datas['product']['styleColors']
        swatches = []
        for color in colors:
            swatch = color['styleColorCode']
            swatches.append(swatch)

        if len(swatches) > 1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        measers = response.xpath('//div[@class="new-product-measurements"][1]//text()').extract()
        if not len(measers):            
            descs = response.xpath('//div[@id="long-description"]/text()').extract()
            for desc in descs:
                if desc.strip() not in measers and ('cm' in desc or 'Measurements' in desc):
                    measers.append(desc.strip())
            size_info = '\n'.join(measers)
        else:
            fits = []
            for info in measers:
                if info and info.strip() not in fits:
                    fits.append(info.strip())
            size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//*[@id="product-count"]/text()').extract_first().split(' ')[0].replace(',',''))
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = "shopbop"
    merchant = 'Shopbop'
    mid = 61861

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@id="product-count"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//ul[@id="product-container"]/li',
            designer = './/div[@class="brand"]/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//html', _parser.checkout)),
            ('sku','//span[@itemprop="sku"]/@content'),
            ('name', '//div[@id="product-title"]/text()'),
            ('designer', '//div[@itemprop="brand"]//span[@class="brand-name"]/text()'),
            ('description', ('//div[@itemprop="description"]/ul/li/text()',_parser.description)),
            ('prices', ('//div[@id="pdp-pricing"]', _parser.prices)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=61861,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            current_path='//script[@type="sui-state"]/text()'
            ),
        # reviews = dict(
        #   items = '//div[@class="reviews-container"]//div[contains(@class,"row review")]',
        #   user = './div[@class="profile g3"]/div[1]/text()',
        #   title = './/span[@class="review-title"]/text()',
        #   content = './/div[@class="review-text"]/text()',
        #   review_time = '',
        #   score = '',
        #   ),
        reviews = dict(
            get_review_url = _parser.get_review_url,
            method = _parser.reviews,
            ),
        image = dict(
            method = _parser.parse_images,
            current_path='//script[@type="sui-state"]/text()'
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//html',
            ),
        designer = dict(
            link = '//div[@class="group"]/ul/li/a/@href',
            designer = '//h1[@class="pageHeadingSpan"]/text()',
            description = ('//div[@id="brandmh-bio-copy"]//text() | //dic[@id="bio-container"]//text()',_parser.designer_desc),
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    designer_url = dict(
        EN = dict(
            f = 'https://www.shopbop.com/s/designerindex/alpha?switchToCurrency=USD&switchToLocation=US&switchToLanguage=EN',
            ),
        ZH = dict(
            f = 'https://cn.shopbop.com/actions/designerindex/viewAlphabeticalDesigners.action'
            ),
        )

    json_path = dict(
        method = _parser.parse_json,
        obj_path = '//script',
        keyword = 'var productDetail',
        flag = ('var productDetail =',';'),
        field = dict(
            )
        )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
                "https://www.shopbop.com/accessories-jewelry/br/v=1/13540.htm?baseIndex=",
                "https://www.shopbop.com/accessories-fine-jewelry/br/v=1/48184.htm?baseIndex=",
                "https://www.shopbop.com/accessories-trend-single-earring/br/v=1/13583.htm?baseIndex=",
                "https://www.shopbop.com/accessories-watches/br/v=1/13561.htm?baseIndex=",
                "https://www.shopbop.com/accessories-belts/br/v=1/13577.htm?baseIndex=",
                "https://www.shopbop.com/accessories-gloves/br/v=1/13576.htm?baseIndex=",
                "https://www.shopbop.com/accessories-hair/br/v=1/13575.htm?baseIndex=",
                "https://www.shopbop.com/accessories-hats/br/v=1/13574.htm?baseIndex=",
                "https://www.shopbop.com/accessories-home-gifts/br/v=1/13587.htm?baseIndex=",
                "https://www.shopbop.com/accessories-keychains-bag-charms/br/v=1/13567.htm?baseIndex=",
                "https://www.shopbop.com/accessories-scarves-wraps/br/v=1/13564.htm?baseIndex=",
                "https://www.shopbop.com/accessories-sunglasses-eyewear/br/v=1/13558.htm?baseIndex=",
                "https://www.shopbop.com/accessories-tech/br/v=1/13568.htm?baseIndex=",
                "https://www.shopbop.com/accessories-umbrellas/br/v=1/13565.htm?baseIndex=",
                "https://www.shopbop.com/sale-accessories/br/v=1/15304.htm?baseIndex=",
                ],
            b = [
                "https://www.shopbop.com/bags/br/v=1/13505.htm?baseIndex=",
                "https://www.shopbop.com/shop-category-sale-bags/br/v=1/15355.htm?baseIndex=",
                "https://www.shopbop.com/accessories-travel/br/v=1/13586.htm?baseIndex="
                ],
            c = [
                "https://www.shopbop.com/clothing/br/v=1/13266.htm?baseIndex=",
                "https://www.shopbop.com/shop-category-sale-clothing/br/v=1/15381.htm?baseIndex=",
                "https://www.shopbop.com/accessories-socks-tights/br/v=1/13578.htm?baseIndex=",
            ],
            s = [
                "https://www.shopbop.com/shoes/br/v=1/13438.htm?baseIndex=",
                "https://www.shopbop.com/sale-shoes/br/v=1/15539.htm?baseIndex=",
            ],
        ),
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'www.',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            currency_sign = '$',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrQNDXbRKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAByD4qp9AAAA'
            },
        ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            currency_sign = u'\uffe5',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR19ovUKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQX9g4CAEjXmUN9AAAA'
            },
            
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = u'HK$',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT18HbRKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAE9Z1TJ9AAAA'
            },
            
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = u'\xa5',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT1CojUKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDACCl9Dh9AAAA'
            },
        ),
        KR = dict(
            currency = 'KRW',
            currency_sign = u'\u20a9',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT1DgrXKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDANZCkaZ9AAAA'
            },

        ),
        SG = dict(
            currency = 'SGD',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrQNdnfRKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAEyffNN9AAAA'
            },

        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = u'\xa3',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1dwrQKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDANYeP5F9AAAA'
            },
        ),
        RU = dict(
            currency = 'RUB',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrQNCnXSKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQX9g4CAEm4l019AAAA'
            },
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CA$',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1dnTRKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQX9g4CALpaem59AAAA',
            },
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = u'A$',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1DHXRKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAGD9YJV9AAAA'
            },
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = u'\u20ac',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1DQ3SKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUVdq6uOrk5CQHJ5alptiWFJWmouj2T/MvykzPzLOtykDWBBd29gMA7zRBiH0AAAA='
            },

        ),
        NO = dict(
            currency = 'NOK',
            cookies = {
            'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT18/fWKQAK+CTmpZcmpqfapubplMVnpthaGJhbGFgYmBqaGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAN++lyV9AAAA'
            },

        ),
        )
