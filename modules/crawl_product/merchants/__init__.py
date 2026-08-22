# -*- coding: utf-8 -*-
import scrapy
import sys
# import imp
# imp.reload(sys)
from utils import cfg,utils
from utils.cfg import *
from utils.size_convert import *
from utils.size_helper import *
import importlib

class Item(scrapy.Item):
    merchant = scrapy.Field()
    crawler_name = scrapy.Field()
    url = scrapy.Field()
    designer = scrapy.Field()
    name = scrapy.Field()
    saleprice = scrapy.Field()
    listprice = scrapy.Field()
    originsaleprice = scrapy.Field()
    originlistprice = scrapy.Field()
    currency = scrapy.Field()
    description = scrapy.Field()
    sku = scrapy.Field()
    styleid = scrapy.Field()
    gtin = scrapy.Field()
    mpn = scrapy.Field()
    newsku = scrapy.Field()
    images = scrapy.Field()
    sizes = scrapy.Field()
    originsizes = scrapy.Field()
    originsizes2 = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    color = scrapy.Field()
    cover = scrapy.Field()
    gender = scrapy.Field()
    error = scrapy.Field()
    country = scrapy.Field()
    area = scrapy.Field()
    language = scrapy.Field()
    jobid = scrapy.Field()
    opflag = scrapy.Field()  # mysql operation flag: insert,update,outofstock,removed
    fit_size = scrapy.Field()
    size_prices = scrapy.Field()
    tmp = scrapy.Field()
    real_id = scrapy.Field()
    condition = scrapy.Field()
    parsedsizes = scrapy.Field()


def _merchant(*args, **kwargs):
    merchant = kwargs.get('merchant')

    cm = importlib.import_module('.' + merchant, package='merchants')
    obj = cm.Config(**kwargs)

    return obj



class MerchantConfig(object):
    _params = {}
    url_split = True
    cookie_set = False
    
    def __init__(self, *args, **kwargs):
        self._params = kwargs


    @property
    def country(self):
        return self._params.get('country', 'US').upper()

    @property
    def gender(self):
        return self._params.get('gender', 'f')

    @property
    def category(self):
        return self._params.get('category', 'c')

    @property
    def language(self):
        return self.countries.get(self.country).get('language', 'EN')

    @property
    def area(self):
        return self.countries.get(self.country).get('area', 'US')

    @property
    def currency(self):
        return self.countries.get(self.country).get('currency', 'USD')

    @property
    def discurrency(self):
        return self.countries.get(self.country).get('discurrency', '')

    @property
    def currency_sign(self):
        return self.countries.get(self.country).get('currency_sign', '$')

    @property
    def thousand_sign(self):
        return self.countries.get(self.country).get('thousand_sign', ',')

    @property
    def vat_rate(self):
        return self.countries.get(self.country).get('vat_rate', 1.0)

    @property
    def translate(self):
        return self.countries.get(self.country).get('translate', [])

    @property
    def headers(self):
        if self.name in cfg.bot_merchants:
            return cfg.bot_header
        if hasattr(self, 'merchant_headers'):
            for key, value in list(self.merchant_headers.items()):
                cfg.default_header[key] = value
        return cfg.default_header

    @property
    def cookies(self):
        if self.cookie_set:
            return self.cookie(self._params)
        return self.countries.get(self.country).get('cookies', {})

    @property
    def start_urls(self):
        try:
            return self.list_urls[self.gender][self.category]
        except Exception as e:
            raise Exception(('start_url exception: {} - {} - {} - {} ').format(self.name, self.country, self.gender, self.category))

    @property
    def plist_page_num_path(self):
        return self.path['plist']['page_num']

    @property
    def plist_items_path(self):
        return self.path['plist']['items']

    @property
    def plist_designer_path(self):
        return self.path['plist']['designer']
    
    @property
    def plist_link_path(self):
        return self.path['plist']['link']

    @property
    def jobid(self):
        return self._params.get('jobid')

    

    def _url(self, url):
        if self.country == 'US':
            return url
        try:
            base = self.countries['US']['country_url']
            replace = self.countries[self.country]['country_url']
            if base and replace and replace not in url:
                url = url.replace(base, replace)
        except Exception as e:
            pass

        try:
            for pair in self.translate:
                url = url.replace(pair[0], pair[1])
        except Exception as e:
            pass

        return url

    def _init_item(self):
        item = Item()
        item['gender'] = self.gender
        item['merchant'] =self.merchant
        item['crawler_name'] = self.name
        item['category'] = self.category
        item['country'] = self.country
        item['area'] = self.area
        item['language'] = self.language
        item['currency'] = self.currency
        item['opflag'] = 'update'
        item['color'] = ''
        item['condition'] = ''
        item['jobid'] = self.jobid
        # item['url'] = ''

        return item

    def _convert_prices(self, item):
        if self.discurrency:
            rate = utils.get_currency_rate(self.discurrency, self.currency)
        else:
            rate = 1.0

        tax_rate = utils.get_tax_rate(item['merchant'], item['country'], item['category'])

        if self.currency_sign != '$' and self.currency_sign not in item['originlistprice']:
            item['error'] = 'parse issue'
        else:
            originlistprice = currency_parser(item['originlistprice'])
            originsaleprice = currency_parser(item['originsaleprice'])
            item['listprice'] = round(originlistprice * rate * tax_rate * self.vat_rate, 2)
            item['saleprice'] = round(originsaleprice * rate * tax_rate * self.vat_rate, 2)


class MerchantParser(object):
    def get_cookies(self, kwargs):
        return self._get_cookies(kwargs)

    def page_num(self, data, **kwargs):
        return self._page_num(data, **kwargs)

    def list_url(self, i, response_url, **kwargs):
        return self._list_url(i, response_url, **kwargs)

    def checkout(self, checkout, item, **kwargs):
        soldOut = self._checkout(checkout, item, **kwargs)
        if 'error' in item and item['error'] == 'parse issue':
            return self._parse_issue(item, **kwargs)
        if soldOut:
            return self._outofstock(item, **kwargs)

    def check_shipped(self, checkshipped, item, **kwargs):
        not_shipped = self._check_shipped(checkshipped, item, **kwargs)
        if not_shipped:
            return self._cannotshipped(item, **kwargs)

    def sku(self, xpath, item, **kwargs):
        self._sku(xpath, item, **kwargs)

    def name(self, xpath, item, **kwargs):
        self._name(xpath, item, **kwargs)

    def designer(self, xpath, item, **kwargs):
        self._designer(xpath, item, **kwargs)

    def images(self, xpath, item, **kwargs):
        self._images(xpath, item, **kwargs)

    def color(self, xpath, item, **kwargs):
        self._color(xpath, item, **kwargs)

    def description(self, xpath, item, **kwargs):
        self._description(xpath, item, **kwargs)

    def condition(self, xpath, item, **kwargs):
        self._condition(xpath, item, **kwargs)

    def sizes(self, xpath, item, **kwargs):
        self._sizes(xpath, item, **kwargs)

        item['sizes'] = []
        item['parsedsizes'] = []
        item['originsizes'] = ['One Size'] if item['originsizes'] == ['IT'] else item['originsizes']
        item['originsizes'] = [x.replace('\xbd','.5') for x in item['originsizes']]

        if item['originsizes']:
            # offset = utils.get_size_offset(item['merchant'], item['designer'].upper())
            offset = {}
            size_standard = utils.get_size_standard()
            orisizes = ';'.join(item['originsizes'])
            orisizes2 = ';'.join(item['originsizes2']) if 'originsizes2' in item else orisizes
            ori_sizes, parsed_sizes, sizes = parse_sizes(item, orisizes, orisizes2, offset, size_standard)
            item['originsizes'] = '####' + ori_sizes
            item['parsedsizes'] = parsed_sizes
            item['sizes'] = sizes
        else:
            item['originsizes'] = ''
            item['parsedsizes'] = ''
            item['sizes'] = ''
            item['error'] = 'Out Of Stock'


    def prices(self, xpath, item, **kwargs):
        self._prices(xpath, item, **kwargs)
        if not item['originlistprice']:
            item['originlistprice'] = item['originsaleprice']
        else:
            item['originlistprice'] = item['originlistprice'].strip()
            item['originsaleprice'] = item['originsaleprice'].strip()

        _merchant(**kwargs)._convert_prices(item)

    def parse_json(self, item, path, datas, **kwargs):
        keyword = path['keyword']
        for dat in datas:
            data = dat.xpath('./text()').extract_first()
            if data and keyword in data:
                break
        try:
            start_flag, end_flag = path['flag']
            try:
                obj = json.loads(data.split(start_flag,1)[-1].rsplit(end_flag,1)[0].strip())
            except:
                obj = json.loads(data.split(start_flag,1)[-1].split(end_flag)[0].strip())
            for field, paths in list(path['field'].items()):
                obj_tmp = obj
                for path in paths:
                    obj_tmp = obj_tmp[path]
                item[field] = obj_tmp
            self._parse_json(obj, item, **kwargs)
        except:
            item['sizes'] = ''
            item['sku'] = kwargs.get('sku', '')
            item['error'] = 'Out Of Stock'

    def parse_ajax(self, response, item, **kwargs):
        ajax_url = self._get_ajax_url(response,item)
        formdata = self._get_formdata(response,item)
        # cookies = self._get_cookies(response,item)
        headers = self._get_headers(response,item)

        result = getwebcontent(ajax_url,formdata,headers)
        result = json.loads(result)
        self._parse_ajax(result, item, **kwargs)

    def parse_color_items(self, response, item, **kwargs):
        items = self._parse_color_items(response, item, **kwargs)
        return items

    def parse_multi_items(self, response, item, **kwargs):
        for item in self._parse_multi_items(response, item, **kwargs):
            yield item

    def parse_item_url(self, response, **kwargs):
        for url in self._parse_item_url(response, **kwargs):
            yield url

    def get_review_url(self, response, **kwargs):
        review_url = self._get_review_url(response, **kwargs)
        return review_url

    def reviews(self, response, **kwargs):
        for review in self._reviews(response, **kwargs):
            yield review

    def parse_images(self, response, **kwargs):
        return self._parse_images(response, **kwargs)

    def parse_mpnmaps(self, response, **kwargs):
        return self._parse_mpnmaps(response, **kwargs)

    def parse_swatches(self, response, swatch_path, **kwargs):
        return self._parse_swatches(response, swatch_path, **kwargs)

    def parse_size_info(self, response, size_info_path, **kwargs):
        return self._parse_size_info(response, size_info_path, **kwargs)

    def parse_look(self, item, look_path, response, **kwargs):
        for item in self._parse_look(item, look_path, response, **kwargs):
            yield item

    def parse_look_url(self, url, look_path, **kwargs):
        return self._parse_look_url(url, look_path, **kwargs)

    def blog_page_num(self, data, **kwargs):
        return self._blog_page_num(data, **kwargs)

    def blog_list_url(self, i, response_url, **kwargs):
        return self._blog_list_url(i, response_url, **kwargs)

    def json_blog_links(self, responses, **kwargs):
        return self._json_blog_links(responses, **kwargs)

    def parse_blog(self, response, **kwargs):
        return self._parse_blog(response, **kwargs)

    def _outofstock(self, item, **kwargs):
        item['sizes'] = ''
        item['sku'] = kwargs.get('sku', '')
        item['error'] = 'Out Of Stock'

        return item

    def _cannotshipped(self, item, **kwargs):
        item['sku'] = kwargs.get('sku', '')
        item['error'] = 'cannot shipped'

        return item

    def _parse_issue(self, item, **kwargs):
        item['sku'] = kwargs.get('sku', '')
        return item

    def _name(self, xpath, item, **kwargs):
        pass

    def _sku(self, xpath, item, **kwargs):
        pass

    def _sizes(self, xpath, item, **kwargs):
        pass

    def _images(self, xpath, item, **kwargs):
        pass

    def _color(self, xpath, item, **kwargs):
        pass

    def _prices(self, xpath, item, **kwargs):
        pass

    def _get_formdata(self, response, item, **kwargs):
        pass

    def _get_cookies(self, kwargs):
        pass

    def _get_headers(self, response, item, **kwargs):
        pass

    def _get_review_url(self, response, **kwargs):
        pass

    def _review(self, response, **kwargs):
        pass
        
    def _parse_images(self, response, **kwargs):
        pass

    def _parse_mpnmaps(self, response, **kwargs):
        pass

    def _parse_swatches(self, response, swatch_path, **kwargs):
        pass

    def _parse_look(self, item, look_path, response, **kwargs):
        pass

    def _parse_look_url(self, url, look_path, **kwargs):
        pass

    def parse_checknum(self, response, **kwargs):
        pass

    def json_designer(self, response, **kwargs):
        urls = self._json_designer(response, **kwargs)
        return urls

    def json_blog(self, response, **kwargs):
        urls = self._json_blog(response, **kwargs)
        return urls

    def sizes_chart(self, form, item):
        order_dict = self._sizes_chart(form, item)
        return order_dict

    def size_chart_json_url(self, item):
        url = self._size_chart_json_url(item)
        return url

    def get_size_chart_url(self, response):
        url, designer = self._get_size_chart_url(response)
        return url, designer
        
    def designer_desc(self, xpath, item, **kwargs):
        self._designer_desc(xpath, item, **kwargs)
