from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.utils import *

class Parser(MerchantParser):
	def _checkout(self, checkout, item, **kwargs):
		script = checkout.extract_first()
		if not script:
			return True

		data = json.loads(script)
		availability = data['offers']['availability']
		if 'InStock' in availability:
			item['tmp'] = data
			return False
		elif 'OutOfStock' in availability:
			return True

	def _sku(self, data, item, **kwargs):
		data = item['tmp']
		item['sku'] = item['tmp']['sku'][0:8]
		item['name'] = item['tmp']['name']
		item['designer'] = item['tmp']['brand']['name']
		item['description'] = item['tmp']['description']

	def _images(self, images, item, **kwargs):
		imgs = images.extract()
		images = []
		for img in imgs:
			image = 'https:' + img if 'http' not in img else img
			images.append(image)
		item['images'] = images
		item['cover'] = item['images'][0]

	def _sizes(self, sizes, item, **kwargs):
		osizes = sizes.extract()
		originsizes = []
		item['originsizes'] = []
		for osize in osizes:
			originsizes.append(osize.strip())
		if item['category'] in ['a','b'] and not originsizes:
			originsizes = ['IT']
		item['originsizes'] = originsizes

	def _prices(self, prices, item, **kwargs):
		sale_price = prices.xpath('.//span[@class="product__price on-sale"]/text()').extract()
		regular_price = prices.xpath('.//span[@class="product__price product__price--compare"]/text()').extract()

		if len(regular_price) == 0:
			item['originlistprice'] = prices.xpath('.//span[@class="product__price"]/text()').extract_first()
			item['originsaleprice'] = item['originlistprice']
		else:
			item['originlistprice'] = regular_price[0].strip()
			item['originsaleprice'] = sale_price[0].strip()

		if item['country'] == 'CN' and item['originlistprice'] != item['originsaleprice']:
			item['error'] = 'Out Of Stock'
			item['originsizes'] = ''
			item['sizes'] = ''

	def _parse_images(self, response, **kwargs):
		imgs = response.xpath('//img[@class="photoswipe__image lazyload"]/@data-photoswipe-src').extract()
		images = []
		for img in imgs:
			image = 'https:' + img if 'http' not in img else img
			images.append(image)
		return images

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract()
		fits = []
		for info in infos:
			if info and info.strip() not in fits and ('Measurements' in info or ' x ' in info.lower() or 'cm' in info or 'mm' in info):
				fits.append(info.strip())
		size_info = '\n'.join(fits)
		return size_info

	def _parse_checknum(self, response, **kwargs):
		number = int(response.xpath('//div[contains(@class,"collection-filter__item--count")]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('products',''))
		return number
_parser = Parser()


class Config(MerchantConfig):
	name = 'savannahs'
	merchant = 'Savannahs'

	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = '//div[@class="pagination"]/span[@class="page"][last()]/a/text()',
			items = '//div[@class="grid grid--uniform grid--collection"]/div/div',
			designer = './/div[@class="product-brand"]/a/text()',
			link = './a/@href',
			),
		product = OrderedDict([
			('checkout', ('//script[@type="application/ld+json"]/text()', _parser.checkout)),
			('sku', ('//html',_parser.sku)),
			('color', '//input[@id="pr_color"]/@value'),
			('images', ('//img[@class="photoswipe__image lazyload"]/@data-photoswipe-src', _parser.images)),
			('sizes', ('//input[@name="Size"][not(contains(@class,"disabled"))]/@value', _parser.sizes)),
			('prices', ('//html', _parser.prices))
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
			size_info_path = '//div[@class="product-detail__tab-content"][1]/ul/li/text()',
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
				"https://savannahs.com/collections/accessories?&page=",
			],
			b = [
				"https://savannahs.com/collections/bags?&page=",
			],
			s = [
				"https://savannahs.com/collections/shoes?page=",
			],
		),
		m = dict(
		),
		country_url_base = '/us/',
	)

	countries = dict(
		US = dict(
			language = 'EN',
			currency = 'USD',
			country_url = 'https://savannahs.com/',
			),
		CN = dict(
			area = 'CN',
			currency = 'CNY',
			discurrency = 'USD',
			country_url = 'https://savannahs.com/',
		),
		GB = dict(
			currency = 'GBP',
			currency_sign = '\xa3',
			country_url = 'https://uk.savannahs.com/'
		),
		DE = dict(
			currency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			country_url = 'https://eu.savannahs.com/'
		),
		AU = dict(
			currency = 'AUD',
			currency_sign = 'A$',
			country_url = 'https://au.savannahs.com/'
		)
		)

		


