from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *

class Parser(MerchantParser):

	def _page_num(self, data, **kwargs):
		pages = int(data)/18 + 1
		return pages

	def _list_url(self, i, response_url, **kwargs):
		url = response_url.split('?')[0] + '?page=%s'%i
		return url

	def _checkout(self, checkout, item, **kwargs):
		if checkout:
			return True
		else:
			return False

	def _sku(self, res, item, **kwargs):
		json_data = json.loads(res.extract_first())
		item['sku'] = json_data[0]['productMasterID']

	def _designer(self, res, item, **kwargs):
		json_data = json.loads(res.extract_first())
		item['designer'] = json_data['brand']['name']
		item['name'] = json_data['name'].upper()
		item['color'] = json_data['color'].upper()

	def _images(self, images, item, **kwargs):
		imgs = json.loads(images.xpath('//script[@type="application/ld+json"][contains(text(),"images")]/text()').extract_first())
		item['images'] = []

		for img in imgs['image']:
			image = urllib.parse.urljoin("https://www.casadei.com/",img)
			item['images'].append(image.split('?')[0])
		item['cover'] = item['images'][0] if item['images'] else ''

	def _sizes(self, sizes, item, **kwargs):
		osizes = sizes.extract()
		sizes = []
		for osize in osizes:
			sizes.append(osize.replace(',', '.'))
		item['originsizes'] = sizes

	def _prices(self, prices, item, **kwargs):
		try:
			item['originlistprice'] = prices.xpath('./div/div[contains(@class,"b-product_price-standard")]/text()').extract()[0]
			item['originsaleprice'] = prices.xpath('./div/span[contains(@class,"b-product_price-sales")]/text()').extract()[0]
		except:
			item['originsaleprice'] = prices.xpath('.//div[contains(@class,"b-product_price-standard")]/text()').extract()[0]
			item['originlistprice'] = item['originsaleprice']

	def _description(self,desc, item, **kwargs):
		description = []
		for d in desc.extract():
			if d.strip():
				description.append(d.strip())
		item['description'] = '\n'.join(description)

	def _parse_images(self, response, **kwargs):
		imgs_json = json.loads(response.xpath('//script[@type="application/ld+json"][contains(text(),"images")]/text()').extract_first())
		imgs = imgs_json['image']
		# images = []
		# for img in imgs:
		# 	image = img.split('?')[0] + '?sw=804&amp;sh=1200&amp;sm=fit'
		# 	images.append(image)
		return imgs

	def _parse_swatches(self, response, swatch_path, **kwargs):
		datas = response.xpath(swatch_path['path'])
		swatches = []
		for data in datas:
			pid = data.xpath('./@href').extract()[0].split('.html')[0].split('-')[-1]
			swatches.append(pid)

		if len(swatches)>1:
			return swatches

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract_first()
		descs = infos.split('.')
		desc_li = []
		skip = False
		for i in range(len(descs)):            
			if skip:
				try:
					num1 = int(descs[i][-1])
					num2 = int(descs[i+1][0])
					desc_li[-1] = desc_li[-1] + '.' + descs[i+1]
				except:
					skip = False
				continue
			if 'INCHES' in descs[i] or 'MM' in descs[i] or '/' in descs[i]:
				try:
					try:
						num1 = int(descs[i][-1])
						num2 = int(descs[i+1][0])
						desc = descs[i] + '.' + descs[i+1]
						skip = True
					except:
						num1 = int(descs[i][0])
						num2 = int(descs[i-1][-1])
						desc = descs[i-1] + '.' + descs[i]
				except:
					desc = descs[i]
				desc_li.append(desc.strip())

		size_info = '\n'.join(desc_li)
		return size_info
	def _parse_checknum(self, response, **kwargs):
		number = int(response.xpath('//div[@class="l-secondary_content l-refinements"]/@data-productsearch-count').extract_first().strip())
		return number
			
_parser = Parser()


class Config(MerchantConfig):
	name = "casadei"
	merchant = "CASADEI"
	merchant_headers = {'accept-language':'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'}

	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//div[@class="l-secondary_content l-refinements"]/@data-productsearch-count', _parser.page_num),
			list_url = _parser.list_url,
			items = '//a[contains(@class,"js-producttile_link b-product_image-wrapper")]',
			designer = './/div[@class="brand"]/a/text()',
			link = './@href',
			),
		product = OrderedDict([
			('checkout',('//h1[@class="b-error_page-title"]', _parser.checkout)),
			('sku',('//script[contains(@class,"js-gtm_product_variants_info")]/text()', _parser.sku)),
			('designer', ('//script[@type="application/ld+json"][contains(text(),"images")]/text()', _parser.designer)),
			('description', ('//div[@class="b-product_bottom_details"]//text()',_parser.description)),
			('prices', ('//div[@class="b-product_container-price"]', _parser.prices)),
			('images',('//html',_parser.images)), 
			('sizes',('//div[@class="b-variation-value Size"]/ul[@class="js-swatches b-swatches_size"]//a[not(contains(@title,"not available"))]/@title',_parser.sizes)),
			]),
		look = dict(
			),
		swatch = dict(
			method = _parser.parse_swatches,
			path='//ul[@class="js-swatches b-swatches_color"]/li/a',
			),
		image = dict(
			method = _parser.parse_images,
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = '//div[@class="b-product_bottom_details"]/p/text()',			
			),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
		)

	list_urls = dict(
		f = dict(
			s = [
				"https://www.casadei.com/en/shoes/?page="
			]
		)
	)

	countries = dict(
		US = dict(
			language = 'EN', 
			area = 'US',
			currency = 'USD',
			currency_sign = '$',
			thousand_sign = '.',
			cookies = {'preferredCountry':'US'},
			),

		CN = dict(
			currency = 'CNY',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'CN'
			},
		),
		JP = dict(
			currency = 'JPY',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'JP'
			},
		),
		KR = dict(
			currency = 'KRW',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'KR'
			},
		),
		SG = dict(
			currency = 'SGD',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'SG'
			},
		),
		HK = dict(
			currency = 'HKD',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'HK'
			},
		),
		GB = dict(
			currency = 'GBP',
			currency_sign = '\xa3',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'GB'
			},
		),
		RU = dict(
			currency = 'RUB',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'RU'
			},
		),
		CA = dict(
			currency = 'CAD',
			discurrency = 'USD',
			currency_sign = '$',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'CA'
			},
		),
		AU = dict(
			currency = 'AUD',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'AU'
			},
		),
		DE = dict(
			currency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'DE'
			},
		),
		NO = dict(
			currency = 'NOK',
			discurrency = 'EUR',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			cookies = {
			'preferredCountry':'NO'
			},
		),

		)
