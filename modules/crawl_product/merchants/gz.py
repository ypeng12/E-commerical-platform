from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import base64
from lxml import etree
import json

class Parser(MerchantParser):

	def _page_num(self, data, **kwargs):
		pages = int(data)/18 + 1
		return pages

	def _checkout(self, checkout, item, **kwargs):
		if not checkout:
			return True
		else:
			return False

	def _sku(self, data, item, **kwargs):
		item['sku'] = data.extract_first().split('-')[-1].strip().upper()

	def _sizes(self, scripts, item, **kwargs):
		if item['category'] in ['a','b', 'e']:
			size_li.append('IT')
		else:
			country = item['country'].lower() if item['country'].lower() != 'gb' else 'uk'
			ajax_url = 'https://www.giuseppezanotti.com/%s/ajaxcontent/' %country
			product_info = ''
			data = json.loads(scripts.extract_first().strip())
			pid = data['*']['GDL_CdnAjax/js/ajaxcontent']['jsonData']['product_id']

			data = {
				'page': 'catalog-product-view',
				'controller': 'product',
				'action': 'view',
				'module': 'catalog',
				'product_id': pid,
			}
			headers = {
			'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
			'accept': 'application/json, text/javascript, */*; q=0.01',
			'x-requested-with': 'XMLHttpRequest'
			}
			res = requests.post(ajax_url,headers=headers,data=data)
			infos_dict = json.loads(res.text)
			infos = infos_dict['blocks']['product-info-options-configurable']

			infos_html = etree.HTML(base64.b64decode(infos))
			spts = infos_html.xpath('//script[@type="text/x-magento-init"]/text()')[0].strip()
			sp_dic = json.loads(spts)
			options = list(sp_dic['#product_addtocart_form']['configurable']['spConfig']['attributes'].values())[0]['options']

			sizes = []
			for size in options:
				if not size['products']:
					continue
				sizes.append(size['label'].replace(',','.'))
			item['originsizes'] = [x.replace(',','.') for x in sizes]
			item['tmp'] = sp_dic if sizes else ''

	def _prices(self, data, item, **kwargs):
		prices = item['tmp']['#product_addtocart_form']['configurable']['spConfig']['prices']
		listprice = str(prices['oldPrice']['amount'])
		saleprice = str(prices['basePrice']['amount'])
		item['originsaleprice'] = saleprice if saleprice else listprice
		item['originlistprice'] = listprice

	def _images(self, images, item, **kwargs):
		item['images'] = []
		imgs = images.extract()
		for img in imgs:
			image = img
			if image not in item['images']:
				item['images'].append(image)
		item['cover'] = item['images'][0] if item['images'] else ''

	def _description(self,desc, item, **kwargs):
		description = []
		for des in desc.extract():
			if des.strip():
				description.append(des.strip())
		item['description'] = '\n'.join(description)

	def _parse_images(self, response, **kwargs):
		imgs = response.xpath('//div[@class="gallery"]//img/@src').extract()
		images = []
		for i in imgs:
			img = i.replace('150x150','700x700').replace('1000x1000','700x700')
			if img not in images:
				images.append(img)
		return images

	def _parse_swatches(self, response, swatch_path, **kwargs):
		datas = response.xpath(swatch_path['path']).extract()
		swatches = []
		swatches.append(kwargs['sku'])
		for data in datas:
			pid = data.split('?')[0].split('-')[-1].upper()
			if pid in swatches:
				continue
			swatches.append(pid)

		if len(swatches)>1:
			return swatches

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract()
		fits = []
		for info in infos:
			if info.strip() and info.strip() not in fits and ('"' in info.strip() or 'heel' in info.strip().lower() or 'width' in info.strip().lower() or 'height' in info.strip().lower() or 'depth' in info.strip().lower()):
				fits.append(info.strip())
		size_info = '\n'.join(fits)
		return size_info			


_parser = Parser()


class Config(MerchantConfig):
	name = "gz"
	merchant = "Giuseppe Zanotti"

	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//div[@class="l-secondary_content l-refinements"]/@data-productsearch-count', _parser.page_num),
			items = '//div[@class="product"]//div[@class="name"]',
			designer = './a[@class="product"]/text()',
			link = './a/@href',
			),
		product = OrderedDict([
			('checkout',('//button[@id="product-addtocart-button"]', _parser.checkout)),
			('sku',('//meta[@property="og:url"]/@content',_parser.sku)),
			('name', '//meta[@property="og:title"]/@content'),
			('designer', '//meta[@property="og:site_name"]/@content'),
			('color', '//meta[@property="product:color"]/@content'),
			('sizes', ('//script[contains(text(),"product_id")]/text()',_parser.sizes)),
			('prices', ('//html',_parser.prices)),
			('description', ('//div[@id="productTabsContent"]/div[@id="product-info"]//text()',_parser.description)),
			('images',('//div[@class="product-gallery"]/div[@class="gallery"]/div[@class="gallery-item"]//img/@data-original',_parser.images)),
			]),
		look = dict(
			),
		swatch = dict(
			method = _parser.parse_swatches,
			path='//li[@class="variation"]/a/@href',
			),
		image = dict(
			method = _parser.parse_images,
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = '//div[@class="product-info"]/ul/ul/li/text()',			
			),
		)

	list_urls = dict(
		f = dict(
			a = [
				"https://www.giuseppezanotti.com/us/woman/accessories?page=",
			],
			b = [
				"https://www.giuseppezanotti.com/us/woman/bags?page=",
			],
			c = [
				"https://www.giuseppezanotti.com/us/woman/ready-to-wear?page=",
			],
			s = [
				"https://www.giuseppezanotti.com/us/woman/shoes?page=",
				"https://www.giuseppezanotti.com/us/woman/sneakers?page=",
			],
		),
		m = dict(
			a = [
				"https://www.giuseppezanotti.com/us/man/accessories?page=",
			],
			b = [
				"https://www.giuseppezanotti.com/us/man/bags?page=",
			],
			c = [
				"https://www.giuseppezanotti.com/us/man/ready-to-wear?page=",
			],
			s = [
				"https://www.giuseppezanotti.com/us/man/shoes?page=",
				"https://www.giuseppezanotti.com/us/man/sneakers?page="
			],

		params = dict(
			# TODO:
			page = 1,
			),
		),
	)

	countries = dict(
		US = dict(
			area = 'US',
			currency = 'USD',
			country_url = '.com/us/',
		),
		GB = dict(
			area = 'GB',
			currency = 'GBP',
			country_url = '.com/uk/',
		),
		CN = dict(
			language = 'ZH',
			currency = 'CNY',
			country_url = '.cn/',
		),
		JP = dict(
			currency = 'JPY',
			country_url = '.com/jp/',
			language = 'JA',
		),
		HK = dict(
			currency = 'HKD',
			country_url = '.com/hk/',
		),
		RU = dict(
			currency = 'RUB',
			country_url = '.com/ru/',
			language = 'RU',
		),
		CA = dict(
			area = 'CA',
			currency = 'CAD',
			country_url = '.com/ca/',
		),
		AU = dict(
			area = 'AU',
			currency = 'AUD',
			country_url = '.com/au/',
		),
		DE = dict(
			currency = 'EUR',
			country_url = '.com/de/',
		),
		NO = dict(
			currency = 'NOK',
			discurrency = 'EUR',
			country_url = '.com/no/',
		)

		)
