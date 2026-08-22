from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from copy import deepcopy
from lxml import html

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        sold_out = checkout.xpath('//*[text()="SOLD OUT"]').extract()
        add_to_bag = checkout.xpath('//*[text()="Add to Bag"]').extract()

        if not add_to_bag or sold_out:
            return True
        else:
            return False

    def _parse_multi_items(self, response, item, **kwargs):
        prd_script = ''
        prds_dict = json.loads(response.text.split('__INITIAL_CONFIG__ =')[-1].split('</script>')[0])

        pid = prds_dict['viewData']['id']
        sizes_data = prds_dict['sellingEssentials']['stylesById'][pid]['skus']['byId'].values()
        prices_data = list(prds_dict['sellingEssentials']['stylesById'][pid]['price']['bySkuId'].values())[0]['regular']['price']

        color_ids = prds_dict['sellingEssentials']['stylesById'][pid]['filters']['color']['allIds']
        color_infos = []
        for color_id in color_ids:
            color_id = str(color_id)
            color_dict = {}
            color_dict[color_id] = prds_dict['sellingEssentials']['stylesById'][pid]['filters']['color']['byId'][color_id]['value']
            color_infos.append(color_dict)

        item['name'] = prds_dict['viewData']['productName'].upper()
        desc = prds_dict['viewData']['description']
        desc_li = html.fromstring(desc).xpath('//p/text()')
        descs = []
        for des in desc_li:
            if des:
                descs.append(des)
        item['description'] = '\n'.join(descs)
        item['designer'] = prds_dict['sellingEssentials']['stylesById'][pid]['brand']['brandName']

        for color in color_infos:
            color_id = list(color.keys())[0]
            color_name = list(color.values())[0].upper()
            item_color = deepcopy(item)
            code = list(prds_dict['stylesById']['data'].keys())[0]
            item_color['sku'] = code + '_' + color_name
            item_color['color'] = color_name

            images = []
            medias = prds_dict['sellingEssentials']['stylesById'][pid]['mediaExperiences']['carouselsByColor']
            for media in medias:                
                if str(media['colorCode']) == color_id:
                    for img in media['orderedShots']:
                        images.append(img['url'])
            # print (images)
            item_color['images'] = images

            item_color['originsizes'] = []          
            for size_data in sizes_data:
                if size_data['colorId'] == color_id and size_data['isAvailable'] and size_data['sizeDisplayValue']:
                    item_color['originsizes'].append(size_data['sizeDisplayValue'])
            # print (item_color['originsizes'])
            if item_color['category'] in ['a','b','e']:
                if not item_color['originsizes']:
                    item_color['originsizes'] = ['IT']
            try:                    
                item_color['originsizes'] = sorted(item_color['originsizes'], key=lambda x:int(x))
            except:
                item_color['originsizes'] = sorted(item_color['originsizes'])
            self.sizes(response, item_color)

            item_color['originsaleprice'] = str(prices_data['units'])
            item_color['originlistprice'] = str(prices_data['units'])
            self.prices(response, item_color, **kwargs)

            yield item_color

    def _get_review_url(self, response, **kwargs):
        try:
            review_count = int(response.xpath('//*[@*="reviewCount"]//text()').extract_first().replace('(','').replace(')',''))
            review_pages = review_count/10 + 2
            for page in range(1,review_pages):
                base_url = 'https://public.api.nordstrom.com/review/review?apikey=2vcqwqqvpvxahbpbpys8v3y2&styleid=%s&page='
                code = response.url.split('?')[0].split('/')[-1]
                review_url = base_url % code
                review_url += str(page)
                yield review_url
        except:
            pass

    def _reviews(self, response, **kwargs):
        obj = json.loads(response.body)
        for tmp in obj['reviews']:
            review = {}
            review['user'] = tmp['userNickname']
            review['title'] = tmp['title']
            review['content'] = tmp['comment']
            review['score'] = float(tmp['starRating'])
            review['review_time'] = tmp['submissionDate'].split('T')[0]

            yield review

    def _parse_images(self, response, **kwargs):
        prd_script = ''
        for script in response.xpath('//script/text()').extract():
            if 'traceContext' in script:
                prd_script = script
                break       
        prds_dict = json.loads(prd_script.split('_INITIAL_CONFIG__ =')[-1].strip())
        color_ids = list(prds_dict['sellingEssentials'].values())[0]['filterAvailabilityById']['color']['allIds']
        color_infos = []
        for color_id in color_ids:  
            color_id = str(color_id)        
            color_dict = {}
            color_dict[color_id] = list(prds_dict['sellingEssentials'].values())[0]['filterAvailabilityById']['color']['byId'][color_id]['value']
            color_infos.append(color_dict)
        images = []
        for color in color_infos:
            color_id = list(color.keys())[0]
            color_name = list(color.values())[0].upper()            
            code = list(prds_dict['stylesById']['data'].keys())[0]
            sku = code + color_name     
            if sku != kwargs['sku']:
                continue
            images = []
            medias = list(prds_dict['stylesById']['data'].values())[0]['styleMedia']['byId'].values()
            for media in medias:                
                if str(media['colorId']) == color_id:
                    if media['mediaGroupType'] == 'Main':                       
                        images.insert(0,media['imageMediaUri']['mediumDesktop'])
                        continue
                    images.append(media['imageMediaUri']['mediumDesktop'])
                        
        return images

    def _parse_swatches(self, response, swatch_path, **kwargs):

        colors = response.xpath(swatch_path['path']).extract()
        if len(colors) > 1:
            current_pid = response.url.split('/')[-1].split('?')[0]
            swatches = []
            for color in colors:
                swatch = current_pid + color.strip().upper()
                swatches.append(swatch)
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        script = response.xpath(size_info['size_info_path']).extract_first()
        data = json.loads(script.split('=',1)[-1].strip())
        fit = data['viewData']['fitAndSize']['sizeDetail']
        size_info = '\n'.join(fit) if fit else ''
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "nordstrom"
    merchant = 'Nordstrom'
    mid = 4326

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//footer/ul/li/ul/li[last()]/a/span/text()',
            items = '//div[@class="Z1RkLid"]/div[contains(@class,"Z1aStr8")]/article',
            designer = './/a[@class="link_22Nhi"]/@href',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//html', _parser.checkout)),
            # ('name', '//*[@itemprop="name"]/text()'),
            ('designer', '//section[@itemprop="brand"]//span/text()'),
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//ul[@class="contentWrapper_Z2f90DX"]/li//img/@aria-label',
            current_path = '//meta[@itemprop="productID"]/@content',
            ),
        reviews = dict(
            get_review_url = _parser.get_review_url,
            method = _parser.reviews,
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//script[contains(text(),"botHeader")]/text()',
            ),
        )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
                "http://shop.nordstrom.com/c/womens-accessories-belts?page=",
                "http://shop.nordstrom.com/c/womens-hats-hair-accessories?page=",
                "http://shop.nordstrom.com/c/jewelry?page=",
                "http://shop.nordstrom.com/c/fine-jewelry-shop?page=",
                "http://shop.nordstrom.com/c/optical-frames-and-readers-for-women?page=",
                "http://shop.nordstrom.com/c/all-wallets-tech-cases?page=",
                "http://shop.nordstrom.com/c/scarves-wraps?page=",
                "http://shop.nordstrom.com/c/womens-sunglasses-shop?page=",
                "http://shop.nordstrom.com/c/umbrellas?page=",
                "http://shop.nordstrom.com/c/womens-watches-shop?page=",
                "http://shop.nordstrom.com/c/winter-accessories-womens?page="
                ],
            b = [
                "http://shop.nordstrom.com/c/womens-handbags?page=",
                "http://shop.nordstrom.com/c/sale-womens-wallets?page=",
                "http://shop.nordstrom.com/c/luggage-travel?page=",
                ],
            c = [
                "http://shop.nordstrom.com/c/womens-clothing?page=",
                "http://shop.nordstrom.com/c/sale-womens-clothing?page="
            ],
            s = [
                "http://shop.nordstrom.com/c/womens-shoes?page=",
                "http://shop.nordstrom.com/c/sale-womens-shoes?page=",
            ],
            e = [
                "http://shop.nordstrom.com/c/all-beauty-makeup-perfume-skincare?page="
            ]
        ),
        m = dict(
            a = [
                "http://shop.nordstrom.com/c/mens-tech-accessories-gadgets?page=",
                "http://shop.nordstrom.com/c/mens-belts-suspenders?page=",
                "http://shop.nordstrom.com/c/mens-cuff-links-jewelry?page=",    
                "http://shop.nordstrom.com/c/mens-hats-gloves-scarves?page=",
                "http://shop.nordstrom.com/c/mens-sunglasses?page=",
                "http://shop.nordstrom.com/c/mens-ties?page=",
                "http://shop.nordstrom.com/c/mens-watches?page=",
                "http://shop.nordstrom.com/c/sale-mens-belts-ties-wallets?page=",
                "http://shop.nordstrom.com/c/sale-mens-hats-scarves-sunglasses?page=",
                "http://shop.nordstrom.com/c/sale-mens-watches-jewelry?page=",
            ],
            b = [
                "http://shop.nordstrom.com/c/mens-bags-cases?page=",
                "http://shop.nordstrom.com/c/sale-mens-bags-luggage-cases?page=",
                "http://shop.nordstrom.com/c/mens-luggage?page=",
            ],
            c = [
                "http://shop.nordstrom.com/c/mens-clothing?page=",
                "http://shop.nordstrom.com/c/sale-mens-clothing?page="
            ],
            s = [
                "http://shop.nordstrom.com/c/mens-shoes?page=",
                "http://shop.nordstrom.com/c/sale-mens-shoes?page=",
            ],
            e = [
                "https://shop.nordstrom.com/c/mens-skincare?page=",
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
            ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            vat_rate = 1.061,
        ),
        )
