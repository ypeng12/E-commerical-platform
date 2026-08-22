from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.extract_helper import *
from utils.cfg import *
from utils.utils import *
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = int(data.split('totalPages":')[-1].split(',')[0])
        return pages

    def _checkout(self, checkout, item, **kwargs):
        config = Config()
        country_url = config.countries[item['country'].upper()]['country_url']
        if country_url not in item['url']:
            item['error'] = 'parse issue'
            return True

        # sku = checkout.xpath('.//*[@*="sku"]/@content | .//*[@*="productID"]/@content').extract_first()
        # if 'sku' in kwargs and kwargs['sku'] != sku:
        #     return True

        addToBag = checkout.xpath('.//button[@data-tstid="addToBag"]').extract()
        soldOut = checkout.xpath('.//*[@data-tstid="soldOut"]').extract()
        if soldOut or not addToBag:
            return True
        else:
            return False

    def _sku(self, script, item, **kwargs):
        obj = json.loads(json.loads(script.extract_first().split("__HYDRATION_STATE__=")[-1]))

        # for key, value in obj['apolloInitialState']['ROOT_QUERY'].items():
        #     pass

        # data = value['data']['slice-product']
        data = obj['initialStates']['slice-product']

        item['sku'] = data['productViewModel']['details']['productId']
        item['name'] = data['productViewModel']['details']['shortDescription']
        item['designer'] = data['productViewModel']['designerDetails']['name']
        item['color'] = data['productViewModel']['details']['colors']
        item['description'] = data['productViewModel']['details']['description']

        item['tmp'] = data

    def _prices(self, script, item, **kwargs):
        data = item['tmp']
        default = data['productViewModel']['priceInfo']['default']

        for priceInfo in list(data['productViewModel']['priceInfo'].values()):
            if default['finalPrice'] < priceInfo['finalPrice']:
                default = priceInfo

        item['originsaleprice'] = default['formattedFinalPrice']
        item['originlistprice'] = default['formattedInitialPrice']
        # item['saleprice'] = default['finalPrice']
        # item['listprice'] = default['initialPrice']

        max_price = data['productViewModel']['priceInfo']['default']

        for priceInfo in list(data['productViewModel']['priceInfo'].values()):
            if max_price['finalPrice'] < priceInfo['finalPrice']:
                max_price = priceInfo

        # item['saleprice_max'] = max_price['finalPrice'] if max_price['finalPrice'] > item['saleprice'] else ''

    def _condition(self, data, item, **kwargs):
        conditions = data.extract()
        if 'Pre-Owned' in conditions:
            item['condition'] = 'p'

    def _images(self, response, item, **kwargs):
        imgs = item['tmp']['productViewModel']['images']['main']
        item['images'] = []
        for img in imgs:
            item['images'].append(img['large'])
        item['cover'] = item['images'][0]

    def _sizes(self, response, item, **kwargs):
        data = item['tmp']
        item['size_prices'] = {}

        orisizes = data['productViewModel']['sizes']['available']
        size_format = data['productViewModel']['sizes']['friendlyScaleName']
        item['originsizes'] = []
        for k, v in list(orisizes.items()):
            osize = '{} {}'.format(v['description'].replace(',','.'), size_format).strip()
            if k in data['productViewModel']['priceInfo'] and data['productViewModel']['priceInfo'][k]['finalPrice'] > item['saleprice']:
                item['size_prices'][osize] = {}
                item['size_prices'][osize]['listprice'] = data['productViewModel']['priceInfo'][k]['initialPrice']
                item['size_prices'][osize]['saleprice'] = data['productViewModel']['priceInfo'][k]['finalPrice']

            item['originsizes'].append(osize)

    def _get_ajax_url(self, response, item, **kwargs):
        pid = response.url.split('-')[-1].split('.')[0]
        ajaxurl = 'https://www.farfetch.com/pdpslice/product/GetInfoByIds?ids=%s&mainProductId=%s&isMoreLikeThis=false'%(pid, pid)
        config = Config()
        if item['country'] == 'US':
            pass
        else:
            base = config.countries['US']['country_url'].replace('shopping/','')
            replace = config.countries[item['country'].upper()]['country_url'].replace('shopping/','')
            if base and replace:
                ajaxurl = ajaxurl.replace(base, replace)
        item['sku'] = pid
        return ajaxurl

    def _get_formdata(self, response, item, **kwargs):
        return None

    def _sizes_chart(self, form, item):
        order_dict = OrderedDict()
        trs = form.xpath('.//tr')
        for tr in trs:
            key = tr.xpath('./td[@class="heading-bold"]/text()').extract_first()
            key = key.replace(item['designer'].upper(), '').strip()
            if key not in order_dict:
                order_dict[key] = []
            size_tds = tr.xpath('./td[@colspan]')
            for size_td in size_tds:
                for i in range(int(size_td.xpath('./@colspan').extract_first())):
                    order_dict[key].append(size_td.xpath('./text()').extract_first())
        return order_dict

    def _size_chart_json_url(self, item):
        pid = item['url'].split('-')[-1].split('.')[0]
        json_url = 'https://www.farfetch.com/pdpslice/product/GetInfoByIds?ids=%s&mainProductId=%s&isMoreLikeThis=false'%(pid,pid)
        return json_url

    def _get_size_chart_url(self, response):
        json_list = json.loads(response.text)
        size_url = ''
        designer = ''
        if len(json_list):
            size_url = urljoin(response.url, json_list[0]['sizeGuideUri'])
            designer = json_list[0]['designerDetails']['name'].upper()
            
        return size_url, designer

    def _parse_look(self, item, look_path, response, **kwargs):
        main_prd = str(response.url.split('?')[0].split('-')[-1].split('.')[0])
        time.sleep(10)
        headers = Config().merchant_headers
        data = {
            "operationName": "ShopTheLook",
            "variables": {
                "productId": main_prd,
                "includeOutfitsDetails": True
            },
            "query": "query ShopTheLook($productId: ID!, $variationId: ID, $merchantId: ID, $sizeId: ID, $includeOutfitsDetails: Boolean!, $outfitSource: OutfitSource) {\n  product(id: $productId, merchantId: $merchantId, sizeId: $sizeId) {\n    ... on Product {\n      id\n      outfit(source: $outfitSource) {\n        totalCount\n        edges @include(if: $includeOutfitsDetails) {\n          node {\n            ... on AvailableOutfitItem {\n              ...AvailableOutfitItemFields\n              __typename\n            }\n            ... on OutOfStockOutfitItem {\n              ...OutOfStockOutfitItemFields\n              __typename\n            }\n            __typename\n          }\n          cursor\n          __typename\n        }\n        id\n        source\n        outfitFlowDuration\n        __typename\n      }\n      brand {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  variation(\n    productId: $productId\n    variationId: $variationId\n    merchantId: $merchantId\n    sizeId: $sizeId\n  ) @include(if: $includeOutfitsDetails) {\n    ... on Variation {\n      id\n      ...OutfitItemImages\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment AvailableOutfitItemFields on AvailableOutfitItem {\n  item {\n    ... on Variation {\n      ...VariationFields\n      label\n      promotion {\n        label\n        __typename\n      }\n      __typename\n    }\n    ... on VariationUnavailable {\n      ...VariationUnavailableFields\n      label\n      promotion {\n        label\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  recommendationsStrategy\n  outfitFlowDuration\n  __typename\n}\n\nfragment VariationFields on Variation {\n  id\n  internalProductId\n  availabilityTypes\n  ...OutfitItemImages\n  ...OutfitItemPrice\n  ...OutfitItemDescription\n  variationProperties {\n    ... on ScaledSizeVariationProperty {\n      order\n      values {\n        id\n        order\n        scale {\n          id\n          description\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  merchandiseLabelIds\n  resourceIdentifier {\n    path\n    __typename\n  }\n  availabilityTypes\n  product {\n    id\n    brand {\n      id\n      name\n      __typename\n    }\n    gender {\n      id\n      __typename\n    }\n    scale {\n      id\n      isOneSize\n      __typename\n    }\n    variations {\n      totalCount\n      totalQuantity\n      edges {\n        node {\n          ... on Variation {\n            id\n            quantity\n            availabilityTypes\n            ...Shipping\n            ...OutfitItemPrice\n            variationProperties {\n              ... on ScaledSizeVariationProperty {\n                order\n                values {\n                  id\n                  order\n                  description\n                  scale {\n                    id\n                    abbreviation\n                    description\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment OutfitItemImages on Variation {\n  images {\n    order\n    size480 {\n      alt\n      url\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment OutfitItemPrice on Variation {\n  price {\n    value {\n      formatted\n      raw\n      __typename\n    }\n    installments {\n      value {\n        formatted\n        __typename\n      }\n      __typename\n    }\n    ... on SalePrice {\n      fullPriceValue {\n        formatted\n        raw\n        __typename\n      }\n      discountPercentage {\n        raw\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment OutfitItemDescription on Variation {\n  description {\n    short {\n      ... on TextDescription {\n        textContent\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment Shipping on Variation {\n  shipping {\n    merchant {\n      id\n      __typename\n    }\n    stockType\n    __typename\n  }\n  __typename\n}\n\nfragment VariationUnavailableFields on VariationUnavailable {\n  description {\n    short {\n      ... on TextDescription {\n        textContent\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  images {\n    order\n    size480 {\n      alt\n      url\n      __typename\n    }\n    __typename\n  }\n  resourceIdentifier {\n    path\n    __typename\n  }\n  product {\n    id\n    brand {\n      id\n      name\n      __typename\n    }\n    gender {\n      id\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment OutOfStockOutfitItemFields on OutOfStockOutfitItem {\n  item {\n    ... on Variation {\n      ...VariationFields\n      label\n      __typename\n    }\n    ... on VariationUnavailable {\n      ...VariationUnavailableFields\n      label\n      __typename\n    }\n    __typename\n  }\n  alternative {\n    ...AvailableOutfitItemFields\n    __typename\n  }\n  recommendationsStrategy\n  __typename\n}\n"
        }
        response_json = requests.post('https://www.farfetch.com/experience-gateway', headers=headers, json=data)

        if response_json.status_code != 200:
            add_farfetch_look(response.meta['sku'])
            return

        json_data = response_json.json()

        item['main_prd'] = main_prd
        try:
            item['cover'] = json_data['data']['variation']['images'][1]['size480']['url']
        except:
            item['cover'] = json_data['data']['variation']['images'][0]['size480']['url']
        outfits = []
        for outfit in json_data['data']['product']['outfit']['edges']:
            outfits.append(outfit['node']['item']['internalProductId'])

        item['products'] = outfits

        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        script = response.xpath(size_info['size_info_path']).extract_first()
        json_data = json.loads(json.loads(script.split("__HYDRATION_STATE__=")[-1]))
        measurements = json_data['initialStates']['slice-product']['productViewModel']['measurements']

        prd_info_li = []
        model_info_li = []
        if not measurements:
            return ''
        prd_measurement = measurements.get('sizes')
        if prd_measurement and len(prd_measurement) == 1:
            prd_info_li = ['Product measurements:']
            for key,values in list(prd_measurement.items()):
                # prd_info_li.append('size:'+key)
                for name,value in list(values.items()):
                    prd_info_li.append(name + ': ' + '-'.join(value))

        model_measurement = measurements.get('modelMeasurements')
        if model_measurement:
            model_info_li = ['Model Measurements:']
            for key,value in list(model_measurement.items()):
                model_info_li.append(key + ': ' + '-'.join(value))
        try:
            modelHeight = measurements['modelHeight'][-1]
            modelIsWearing = measurements['modelIsWearing'] + ' ' + measurements['friendlyScaleName']

            modelIsWear = 'Model is %s wearing size %s.' %(modelHeight, modelIsWearing)
            model_info_li.append(modelIsWear)
        except:
            pass

        size_info = '\n'.join(prd_info_li + model_info_li)
        return size_info

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//meta[@property="og:title"]/@content').extract_first()
        blog = response.xpath('//article[@class="_2bc7f0"]').extract_first()
        return title, blog.replace('meta itemprop="image" content','img src')

    def _parse_images(self, response, **kwargs):
        images = []
        img_script = response.xpath('//script[contains(text(),"__initialState_slice-pdp__")]/text()').extract_first()
        obj = json.loads(img_script.split("window['__initialState_slice-pdp__'] = ")[-1])
        imgs = obj['productViewModel']['images']['main']
        for img in imgs:
            images.append(img['large'])

        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@data-test="items-found"]/@data-total-items').extract_first().strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'farfetch'
    merchant = 'Farfetch'
    merchant_headers = {
        "origin": "https://www.farfetch.com",
        "referer": "https://www.farfetch.com/shopping/women/valentino-garavani--item-20876210.aspx",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        'Cookie':'BIcookieID=8138d220-5015-415e-9bbc-30e5470e23d6'
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html', _parser.page_num),
            items = '//ul[@data-test="product-card-list"]/li',
            designer = './/h5[@itemprop="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//script[contains(text(),"__HYDRATION_STATE__=")]/text()', _parser.sku)),
            ('images', ('//html', _parser.images)),
            ('prices', ('//html', _parser.prices)),
            ('sizes', ('//html', _parser.sizes)),
            ('condition', ('//div[@id="containerCollapser"]//span[@itemprop="name"]/text()', _parser.condition)),
            ]),
        look = dict(
            merchant_id = 'Farfetch',
            official_uid = 8158,
            type = 'html',
            url_type = 'url',
            key_type = 'sku',
            method = _parser.parse_look,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//script[contains(text(),"__HYDRATION_STATE__=")]/text()',
            ),
        designer = dict(
            link = '//ul[contains(@id,"designer")]/li/a/@href',
            designer = '//li[@data-index="2"]//span[@itemprop="name"]/text()',
            description = '//p[@data-test="headerDescription"]/text()',
            ),
        size_chart = dict(
            forms = '//div[@class="sizeguide-overflow"]',
            tstid = './h4/@data-tstid',
            sizes_chart = ('',_parser.sizes_chart),
            disp_category = './h4/text()',
            ),
        blog = dict(
            link = '//div[@id="slice-styleguide"]/div[@class="_0fe727"]//a[@class="_8e7604"]/@href',
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    size_chart_json_url = _parser.size_chart_json_url
    get_size_chart_url = _parser.get_size_chart_url

    designer_url = dict(
        EN = dict(
            f = 'https://www.farfetch.com/designers/women',
            m = 'https://www.farfetch.com/designers/men',
            ),
        ZH = dict(
            f = 'https://www.farfetch.cn/cn/designers/women',
            m = 'https://www.farfetch.cn/cn/designers/men'
            ),
        )

    blog_url = dict(
        ZH = 'https://www.farfetch.cn/cn/style-guide/'
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.farfetch.com/shopping/women/accessories-all-1/items.aspx?page=",
                "https://www.farfetch.com/shopping/women/jewellery-1/items.aspx?page=",
                "https://www.farfetch.com/shopping/women/fine-jewellery-6/items.aspx?page=",
            ],
            b = [
                "https://www.farfetch.com/shopping/women/bags-purses-1/items.aspx?page=",
            ],
            c = [
                "https://www.farfetch.com/shopping/women/clothing-1/items.aspx?page=",
            ],
            s = [
                "https://www.farfetch.com/shopping/women/shoes-1/items.aspx?page=",
            ],
        ),
        m = dict(
            a = [
                "https://www.farfetch.com/shopping/men/accessories-all-2/items.aspx?page=",
                "https://www.farfetch.com/shopping/men/jewellery-2/items.aspx?page=",
                "https://www.farfetch.com/shopping/men/watches-analog-2/items.aspx?page="
            ],
            b = [
                "https://www.farfetch.com/shopping/men/bags-purses-2/items.aspx?page=",
            ],
            c = [
                "https://www.farfetch.com/shopping/men/clothing-2/items.aspx?page=",
            ],
            s = [
                "https://www.farfetch.com/shopping/men/shoes-2/items.aspx?page=",
            ],

        params = dict(
            page = 1,
            ),
        ),

        country_url_base = '.com/shopping/',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '.com/shopping/',
            cookies = {
                'ckm-ctx-sf':'/us',
            }
            ),
        CN = dict(
            language = 'ZH',
            area = 'AS',
            currency = 'CNY',
            currency_sign ='¥',
            country_url = '.com/cn/shopping/',
            cookies = {
                'ckm-ctx-sf':'/cn',
            }
        ),
        JP = dict(
            language = 'JA',
            area = 'AS',
            currency = 'JPY',
            currency_sign = '\uffe5',
            country_url = '.com/jp/shopping/',
            cookies = {
                'ckm-ctx-sf':'/jp',
            }
        ),
        KR = dict(
            language = 'KO',
            area = 'AS',
            currency = 'KRW',
            currency_sign = '\u20a9',
            country_url = '.com/kr/shopping/',
            cookies = {
                'ckm-ctx-sf':'/kr',
            }
        ),
        SG = dict(
            area = 'AS',
            currency = 'SGD',
            currency_sign = '$',
            country_url = '.com/sg/shopping/',
            cookies = {
                'ckm-ctx-sf':'/sg',
            }
        ),
        HK = dict(
            area = 'AS',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '.com/hk/shopping/',
            cookies = {
                'ckm-ctx-sf':'/hk',
            }
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '.com/uk/shopping/',
            cookies = {
                'ckm-ctx-sf':'/uk',
            }
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = '.com/de/shopping/',
            cookies = {
                'ckm-ctx-sf':'/de',
            }
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            currency_sign = '\u20bd',
            thousand_sign = ' ',
            country_url = '.com/ru/shopping/',
            cookies = {
                'ckm-ctx-sf':'/ru',
            }
        ),
        CA = dict(
            area = 'US',
            currency = 'CAD',
            currency_sign = '$',
            country_url = '.com/ca/shopping/',
            cookies = {
                'ckm-ctx-sf':'/ca',
            }
        ),
        AU = dict(
            area = 'AS',
            currency = 'AUD',
            currency_sign = '$',
            country_url = '.com/au/shopping/',
            cookies = {
                'ckm-ctx-sf':'/au',
            }
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'USD',
            currency_sign = '$',
            country_url = '.com/no/shopping/',
            cookies = {
                'ckm-ctx-sf':'/no',
            }
        ),

        )

        


