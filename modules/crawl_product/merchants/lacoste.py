from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *

class Parser(MerchantParser):

	def _checkout(self, checkout, item, **kwargs):
		body = checkout.extract_first().lower()
		if 'sold out' in body:
			return True
		if checkout.xpath('.//button[contains(@class,"add-to-cart")]'):
			return False
		else:
			return True

	def _sku(self, data, item, **kwargs):
		data = json.loads(data.extract_first().strip())
		image = data['image']
		item['sku'] = '_'.join(image.split('.jpg')[0].split('/')[-1].upper().split('_')[0:2])
		item['designer'] = 'LACOSTE'

	def _images(self, images, item, **kwargs):
		item['images'] = []
		imgs = images.extract()
		for img in imgs:
			if 'http' not in img:
				img = 'https:' + img
			image = img.split('?')[0]
			if image not in item['images']:
				item['images'].append(image)
		item['cover'] = item['images'][0]

	def _description(self, description, item, **kwargs):
		descs = description.extract()
		desc_str = []
		for desc in descs:
			if desc.strip():
				desc_str.append(desc.strip())
		item['description'] = '\n'.join(desc_str)

	def _prices(self, prices, item, **kwargs):
		listprice = prices.xpath('./p[contains(@class,"l-vmargin--small")]/text()').extract_first()
		saleprice = prices.xpath('./p[contains(@class,"ff-semibold")]/text()').extract_first()
		item['originlistprice'] = listprice if listprice else saleprice
		item['originsaleprice'] = saleprice

	def _sizes(self, sizes, item, **kwargs):
		data = json.loads(sizes.extract_first())
		sizes = []
		for osize in data['data']['manufacturedSizes']:
			if osize['available']:
				sizes.append(osize['id'])

		if not sizes and item['category'] in ['a','b']:
			sizes = ['IT']

		item['originsizes'] = sizes

	def _parse_images(self, response, **kwargs):
		images = []
		imgs = response.xpath('//ul[contains(@class,"js-slideshow-thumbs")]/li//img/@data-src').extract()
		for img in imgs:
			if 'http' not in img:
				img = 'https:' + img
			if img not in images:
				images.append(img.split('?')[0])
			
		return images

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract()
		fits = []
		for info in infos:
			if info.strip() and info.strip() not in fits and ('dimensions' in info.strip().lower() or 'measures' in info.strip().lower() or 'mm' in info.strip().lower() or 'width' in info.strip().lower() or 'model' in info.strip().lower() or 'cm' in info.strip().lower()):
				fits.append(info.strip())
		size_info = '\n'.join(fits)
		return size_info
	def _parse_checknum(self, response, **kwargs):
		number = int(response.xpath('//div/@data-nb-products').extract_first().strip())
		return number

_parser = Parser()


class Config(MerchantConfig):
	name = "lacoste"
	merchant = "Lacoste"
	url_split = False

	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = '//a[@class="pagination-item"][last()]/text()',
			items = '//div[@class="js-plp-tiles grid"]/div',
			designer = './/div[@class="brand"]/a/text()',
			link = './div/div[1]/a/@href',
			),
		product = OrderedDict([
			('checkout',('//html', _parser.checkout)),
			('sku', ('//script[contains(text(),"mainEntityOfPage")]/text()',_parser.sku)),
			('name', '//h1[@class="title--medium l-vmargin--medium padding-m-2"]/text() | //h1[@class="title--medium l-vmargin--medium padding-m-1"]/text()'),
			('color', '//meta[@name="product:color"]/@content | //meta[@name="og:product:color"]/@content'),
			('description', ('//meta[@name="description"]/@content | //ul[@class="dashed-list fs--medium text-grey l-vmargin--xlarge"]/li/text()',_parser.description)),
			('prices', ('//div[contains(@class,"js-pdp-price")]', _parser.prices)),
			('images',('//ul[contains(@class,"js-slideshow-thumbs")]/li//img/@data-src',_parser.images)),
			('sizes',('//section[contains(@class,"js-fitanalytics-datas")]/@data-fitanalytics',_parser.sizes)),
			]),
		look = dict(
			),
		swatch = dict(
			),
		image = dict(
			method = _parser.parse_images,
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = '//ul[@class="dashed-list fs--medium text-grey l-vmargin--xlarge"]/li/text()',
			),
		designer = dict(
			),
		checknum = dict(
            method = _parser._parse_checknum,
            ),
		)


	list_urls = dict(
		f = dict(
			a = [
				"https://www.lacoste.com/us/lacoste/women/accessories/watches/?page=",
				"https://www.lacoste.com/us/lacoste/women/accessories/sunglasses/?page=",
				"https://www.lacoste.com/us/lacoste/women/accessories/scarves-gloves/?page="
				"https://www.lacoste.com/us/lacoste/women/leather-goods/belts/?page=",
				"https://www.lacoste.com/us/lacoste/women/leather-goods/small-leather-goods/?page=",
				],
			b = [
				"https://www.lacoste.com/us/lacoste/women/leather-goods/bags/?page=",
				],
			c = [
				"https://www.lacoste.com/us/lacoste/women/clothing/?page=",
			],
			s = [
				"https://www.lacoste.com/us/lacoste/women/shoes/?page=",
			],
			e = [
				"https://www.lacoste.com/us/lacoste/women/accessories/fragrance/?page=",
			]
		),
		m = dict(
			a = [
				"https://www.lacoste.com/us/lacoste/men/accessories/watches/?page=",
				"https://www.lacoste.com/us/lacoste/men/accessories/sunglasses/?page=",
				"https://www.lacoste.com/us/lacoste/men/accessories/caps-hats/?page=",
				"https://www.lacoste.com/us/lacoste/men/accessories/scarves-gloves/?page=",
				"https://www.lacoste.com/us/lacoste/men/leather-goods/belts/?page=",
				"https://www.lacoste.com/us/lacoste/men/leather-goods/small-leather-goods/?page="
			],
			b = [
				"https://www.lacoste.com/us/lacoste/men/leather-goods/bags/?page=",
			],
			c = [
				"https://www.lacoste.com/us/lacoste/men/clothing/?page=",
				"https://www.lacoste.com/us/lacoste/men/accessories/socks/?page="
			],
			s = [
				"https://www.lacoste.com/us/lacoste/men/shoes/?page=",
			],
			e = [
				"https://www.lacoste.com/us/lacoste/men/accessories/fragrance/?page="
			],

		params = dict(
			page = 1,
			),
		),
	)

	countries = dict(
		US = dict(
			language = 'EN', 
			area = 'US',
			currency = 'USD',
			currency_sign = '$',
			country_url = 'www.lacoste.com/us/',
		),
		GB = dict(
			currency = 'GBP',
			currency_sign = '\xa3',
			country_url = 'www.lacoste.com/gb/',
		),
		CA = dict(
			currency = 'CAD',
			currency_sign = 'C$',
			country_url = 'www.lacoste.com/ca/en/',
		),
		# CN = dict(
		# 	currency = 'CNY',
		# 	country_url = 'www.lacoste.cn/',
		# ),
		# JP = dict(
		# 	currency = 'JPY',
		# 	country_url = 'www.lacoste.jp/',
		# 	translate = [
		# 	('lacoste/women/clothing/','women/clothing/'),
		# 	]
		# ),
		# KR = dict(
		# 	currency = 'KRW',
		# 	country_url = 'www.lacoste.com/kr/',
		# 	currency_sign = u'\uc6d0',
		# 	translate = [
		# 		('/women/clothing/','/women/%EC%9D%98%EB%A5%98/'),
		# 		# ('/women/shoes/','/women/%EC%8B%A0%EB%B0%9C/'),
		# 	]
		# ),
		# SG = dict(
		# 	currency = 'SGD',
		# ),
		# HK = dict(
		# 	currency = 'HKD',
		# ),
		# RU = dict(
		# 	currency = 'RUB',
		# ),
		
		# AU = dict(
		# 	currency = 'AUD',
		# ),
		# DE = dict(
		# 	currency = 'EUR',
		# ),
		# NO = dict(
		# 	currency = 'NOK',
		# ),

		)
