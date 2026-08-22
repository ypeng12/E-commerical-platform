from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import json
from utils.utils import *
import requests
from lxml import etree
# from utils.ladystyle import blog_parser, parseProdLink

class Parser(MerchantParser):
    def _checkout(self, scripts, item, **kwargs):
        script = scripts.extract_first()
        if not script:
            return True
        data = json.loads(script)
        if 'offers' in data and 'InStock' in data['offers']['availability'] or 'PreOrder' in data['offers']['availability']:
            item['tmp'] = data
            return False
        else:
            return True

    def _sku(self, code, item, **kwargs):
        pid = code.extract_first()
        color_id = item['tmp']['productID']
        if pid and pid.isdigit() and color_id.isdigit():
            item['sku'] = pid + '_' + color_id
        else:
            item['sku'] = ''
        item['name'] = item['tmp']['name'].strip()
        item['designer'] = item['tmp']['brand']['name']
        item['color'] = item['tmp']['color']
        item['description'] = item['tmp']['description']

    def _prices(self, prices_data, item, **kwargs):
        saleprice = prices_data.xpath('//*[@class="PDPProductPrice__current-price"]//text()').extract_first()
        listprice = prices_data.xpath('//*[@class="PDPProductPrice__original-price"]//text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _sizes(self, html, item, **kwargs):
        preorder = html.xpath('.//div[@class="AddToBagButton__text"]/text()').extract_first()
        final_sale = html.xpath('.//ul[contains(@class,"ShippingAndReturns")]/li[contains(text(),"Final Sale")]').extract_first()
        json_datas = json.loads(html.xpath('.//script[contains(text(),"window.__APOLLO_STATE__")]/text()').extract_first().split('window.__APOLLO_STATE__ = ')[-1].split(';window.__ENV__ =')[0])
        memo = ''
        if preorder and preorder == 'Preorder':
            memo = ':p'
        if final_sale:
            memo = ':f'
        orisizes = []
        dict_keys_li = [i for i in json_datas['readOnlyQueryData'].keys()]

        for data in json_datas['readOnlyQueryData'].values():
            if 'variant' not in data.keys():
                continue
            for size in data['variant']['masterVariant']['inventory']:
                if int(size['available']) > 0:
                    orisizes.append(size['size'] + memo)

        item['originsizes'] = orisizes if orisizes else ['IT' + memo]

    def _images(self, scripts, item, **kwargs):
        script = json.loads(scripts.extract_first().split("window.__APOLLO_STATE__ = ")[-1].split(";window.__ENV__")[0])
        for value in script['readOnlyQueryData'].values():
            if 'variant' not in value.keys():
                continue
            images = []
            item['cover'] = value['variant']['masterVariant']['primaryImageUrls']['medium']
            images.append(item['cover'])
            for img in value['variant']['masterVariant']['alternateImages']:
                images.append(img['medium'])
            item['images'] = images

    def _parse_images(self, response, **kwargs):
        scripts = response.xpath('//script[contains(text(),"__APOLLO_STATE__")]/text()').extract_first()
        script = json.loads(scripts.split("window.__APOLLO_STATE__ = ")[-1].split(";window.__ENV__")[0])
        for value in script['readOnlyQueryData'].values():
            if 'variant' not in value.keys():
                continue
            images = []
            cover = value['variant']['masterVariant']['primaryImageUrls']['medium']
            images.append(cover)
            for img in value['variant']['masterVariant']['alternateImages']:
                images.append(img['medium'])
            return images

    def _page_num(self, script, **kwargs):
        pages = script.split('"num_pages":')[-1].split(',')[0]      
        return int(pages)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('page=1', 'page=%s'%i)
        return url

    def parse_item_url(self, response, **kwargs):
        prds_script = ''
        scripts = response.xpath('//script/text()').extract()
        for script in scripts:
            if 'master_variants_data' in script:
                prds_script = script
                break
        if not prds_script:
            for script in scripts:
                if 'window.__APOLLO_STATE__ =' in script:
                    prds_script = script
                    break

        if kwargs['gender'] == 'f':
            url_title = 'women'
        else:
            url_title = 'home'
        prds = json.loads(prds_script.split("window.__APOLLO_STATE__ = ")[-1].split(";window.__ENV__")[0])
        for p in prds['readOnlyQueryData'].keys():
            if 'ProductListPageCategoryQuery' in p:
                for itm in prds['readOnlyQueryData'][p]['categoryResult']['variants']['edges']:
                    link_item = 'https://www.modaoperandi.com/'+url_title+'/p/'+itm['node']['designerSlug']+'/'+itm['node']['productSlug']+'/'+itm['node']['id']
                    yield link_item,'designer'

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = []
            variant_id = response.xpath('//div[@data-variant_id]/@data-variant_id').extract_first()
            href = response.url.split('.com')[-1]
            base_url = 'https://api.modaoperandi.com/public/v3.1/variants/wear_it_with_variants?vid=%s&href=%s'%(variant_id, href)
            res = requests.get(base_url)
            look_dict = json.loads(res.text)
            look_li = look_dict['data']
            for look in look_li:
                outfits.append(look['attributes']['variants_data'][0]['href'])
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.url
        cover = response.xpath('//img[@class="specific_background_color"]/@src').extract()
        if len(cover)>0:
            item['cover'] = cover[0].replace('/medium_','/c/medium_')

        item['products']= list(map(lambda x: ('https://www.modaoperandi.com'+str(x)), outfits))

        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        fit_lists = response.xpath('//div[@class="Expandable"]//ul/li/text()').extract()
        fits = []
        for fit in fit_lists:
            fits.append(fit)
        size_info = '\n'.join(fits)
        return size_info

    def _get_cookies(self, kwargs):
        country = kwargs['country'].upper()
        url = 'https://www.modaoperandi.com/change_country?country=%s&p_ret=https%3A%2F%2Fwww.modaoperandi.com%2F'%country
        result, cookiesstr = getwebcontent2(url)
        jsession_id = cookiesstr.split('_mojo_session=')[-1].split(';')[0]

        cookies = {'_mojo_session': jsession_id}

        return cookies

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _json_blog_links(self, response, **kwargs):
        urls = []
        links = response.xpath('//a[contains(@href,"/editorial/")]/@href').extract()
        for link in links:
            url = 'https://www.modaoperandi.com' + link
            if url in urls:
                continue
            urls.append(url)
        return urls

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//title/text()').extract_first().split('|')[0]
        key = response.url.split('?')[0].split('/')[-1]

        html_origin = response.xpath('//main[@class="PageLayout__content"]').extract_first().encode('utf-8')
        cover = response.xpath('//main[@class="PageLayout__content"]//img/@src').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        mods = []
        
        for div in response.xpath('//main[@class="PageLayout__content"]/section/div'):
            if div.xpath('./@class').extract_first() not in ['SwiperCarousel', 'Breakpoint Breakpoint--gt-md', 'SinglePumoModule']:
                continue
            if div.xpath('./@class').extract_first() == 'SwiperCarousel':
                products = {"type": "products","pids":[]}
                links = div.xpath('.//a[@class="VariantCell__image"]/@href').extract()
                for link in links:
                    if 'https://www.modaoperandi' not in link:
                        link = 'https://www.modaoperandi.com/' + link
                        prod = parseProdLink(link)
                        if prod[0]:
                            for product in prod[0]:
                                pid = product.id
                                products['pids'].append(pid)
                if products['pids']:
                    html_parsed['items'].append(products)

                continue

            img = div.xpath('.//img/@src').extract_first()
            if img:
                images = {"type": "image","alt": ""}
                images['src'] = img
                html_parsed['items'].append(images)
            txts = div.xpath('.//div[@class="PumoModuleEditorialText__text"]/div').extract()
            for txt in txts:
                if txt:
                    texts = {"type": "html"} if '<a' not in txt else {"type": "html_ext"}
                    texts['value'] = re.sub(r'style=(.*?)>','>',txt.strip())
                    if texts not in html_parsed['items']:
                        html_parsed['items'].append(texts)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="GridItemCount"]/text()[1]').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('items',''))
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = "moda"
    merchant = 'Moda Operandi'
    merchant_headers = {'User-Agent': 'ModeSensBot-Moda'}
    # cookie_set = True
    # cookie = _parser.get_cookies

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"num_pages")]/text()', _parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout',('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('sku',('//div[@data-product-id]/@data-product-id', _parser.sku)),
            ('images', ('//script[contains(text(),"__APOLLO_STATE__")]/text()', _parser.images)),
            ('prices', ('//html', _parser.prices)),
            ('sizes', ('//html', _parser.sizes)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=72746,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//script/text()',
            ),
        blog = dict(
            official_uid = 72746,
            blog_list_url = _parser.blog_list_url,
            json_blog_links = _parser.json_blog_links,
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.modaoperandi.com/women/accessories?page=1",
                "https://www.modaoperandi.com/women/fine-jewelry?page=1",
                "https://www.modaoperandi.com/women/jewelry?page=1",
                "https://www.modaoperandi.com/sale/women/accessories?page=1",
                "https://www.modaoperandi.com/sale/women/jewelry?page=1",
                "https://www.modaoperandi.com/women/products/sale/accessories",
            ],
            b = [
                "https://www.modaoperandi.com/women/bags?page=1",
                "https://www.modaoperandi.com/sale/women/bags?page=1",
                "https://www.modaoperandi.com/women/products/sale/bags",
            ],
            c = [
                "https://www.modaoperandi.com/women/clothing?page=1",
                "https://www.modaoperandi.com/sale/women/clothing?page=1",
                "https://www.modaoperandi.com/women/products/sale/clothing?page=1",
            ],
            s = [
                "https://www.modaoperandi.com/women/shoes?page=1",
                "https://www.modaoperandi.com/sale/women/shoes?page=1",
                "https://www.modaoperandi.com/women/products/sale/shoes",
            ],
        ),
    )

    blog_url = dict(
        EN = [
            'https://www.modaoperandi.com/editorial/the-edit'
        ]
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22840%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = u'\xa5',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22156%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = u'HK$',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22344%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CAD',
            cookies={
                'preferences':'%7B%22countryId%22%3A%22124%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%2C%22showEmailSignup%22%3Afalse%2C%22showLandingPageForRussia%22%3Atrue%7D',
            }
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'A$',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22036%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D',
            }
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22840%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22840%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22840%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = u'\xa3',
            thousand_sign = '.',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22826%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%2C%22showEmailSignup%22%3Afalse%2C%22showLandingPageForRussia%22%3Atrue%7D'
            }
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = u'\u20ac',
            thousand_sign = '.',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22276%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22840%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = u'\u20ac',
            thousand_sign = '.',
            cookies = {
                'preferences':'%7B%22countryId%22%3A%22578%22%2C%22vertical%22%3A%22women%22%2C%22shoppingBagNotifications%22%3Atrue%7D'
            }
        ),

        )
