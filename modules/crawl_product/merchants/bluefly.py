from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *

class Parser(MerchantParser):
	def _page_num(self, data, **kwargs):
		try:
			pages = int(data.strip().split('Item')[0].replace(',',''))/48 + 1
		except:
			pages = 0
		if pages>50:
			 pages=50
		return pages

	def _checkout(self, checkout, item, **kwargs):
		sold_out = checkout.xpath('.//div[@class="stock unavailable"]')
		add_to_bag = checkout.xpath('.//button[@title="Add to Cart"]/span/text()')
		if not add_to_bag or sold_out:
			return True
		else:
			return False

	def _images(self, scripts, item, **kwargs):
		image_script = ''
		for script in scripts.extract():
			if 'data-role=swatch-options' in script:
				image_script = script
				break
		images = json.loads(image_script.split('images":')[-1].split(',"index')[0].strip())
		item['images'] = []
		for img in list(images.values())[0]:
			item['images'].append(img['img'])
		item['cover'] = item['images'][0]
		item['tmp'] = image_script

	def _color(self, data, item, **kwargs):
		script = item['tmp']
		color = script.split('","products"')[0].split('label":"')[-1]
		item['color'] = color.upper()

	def _sizes(self, sizes, item, **kwargs):
		script = item['tmp']
		item['originsizes'] = []

		if kwargs['category'] in ['c','s']:
			size_list = json.loads(script.split('size')[-1].split('options":')[-1].split(',"position"')[0])
			for size in size_list:
				item['originsizes'].append(size['label'])

		elif kwargs['category'] in ['a','b','e']:
			item['originsizes'] = ['IT']
		
	def _sku(self, skus, item, **kwargs):
		skus = skus.extract()
		if skus:
			sku = skus[0].split('#')[-1].strip()
			item['sku'] = sku
		else:
			item['sku'] = ''

	def _prices(self, prices, item, **kwargs):
		listprice = prices.xpath('.//span[@class="old-price"]//span[@class="price"]/text()').extract()
		saleprice = prices.xpath('.//span[@class="special-price"]//span[@class="price"]/text()').extract()
		try:
			item['originsaleprice'] = saleprice[0].strip()
		except:
			item['error'] = "sale price can't be processed"
		if len(listprice) > 0:
			try:
				item['originlistprice'] = listprice[-1].strip()
			except:
				item['error'] = "Price can't ba processed"
		else:
			item['originlistprice'] = item['originsaleprice']


	def _description(self,desc, item, **kwargs):
		description = []
		for d in desc.extract():
			if d.strip():
				description.append(d.strip())
		item['description'] = '\n'.join(description)
		try:
			item['description'] = re.sub(r'[\xbf]','"', item['description'])
			item['description'] = re.sub(r'[\xbd]',".5", item['description']).replace(' .5','.5')
			item['description'] = re.sub(r'[\xbe]',".75", item['description']).replace(' .75','.75')
			item['description'] = re.sub(r'[\xbc]',".25", item['description']).replace(' .25','.25')
		except:
			pass

	def _list_url(self, i, response_url, **kwargs):
		url = response_url  + str(i * 48)
		return url

	def _parse_images(self, response, **kwargs):
		scripts = response.xpath('//script/text()').extract()
		image_script = ''
		for script in scripts:
			if 'data-role=swatch-options' in script:
				image_script = script
				break
		images = json.loads(image_script.split('images":')[-1].split(',"index')[0].strip())
		image_li = []
		for img in list(images.values())[0]:
			image_li.append(img['img'])
		return image_li

	def _parse_swatches(self, response, swatch_path, **kwargs):
		datas = response.xpath(swatch_path['path'])
		swatches = []
		for data in datas:
			pid = data.xpath('./@href').extract()[0].split('?')[0].split('/')[-1]
			swatches.append(pid)

		if len(swatches) > 1:
			return swatches

_parser = Parser()


class Config(MerchantConfig):
	name = "bluefly"
	merchant = 'Bluefly'


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//div[@class="page-itemcount"]/text()', _parser.page_num),
			list_url = _parser.list_url,
			items = '//ul/li[@class="mz-productlist-item"]',
			designer = './/div[@class="product-grid-brand"]/text()',
			link = './/div[@class="mz-productlisting-image-wrapper"]/a/@href',
			),
		product = OrderedDict([
			('checkout',('//html', _parser.checkout)),
			('images',('//script/text()',_parser.images)), 
			('sku',('//div[@itemprop="productID"]/text()',_parser.sku)),
			('name', '//meta[@name="twitter:title"]/@content'),
			('designer', '//span[@data-ui-id="page-title-wrapper"]/text()'),
			('description', ('//meta[@name="description"]/@content',_parser.description)),
			('color',('//html', _parser.color)),
			('prices', ('//div[@class="product-info-price"]', _parser.prices)),
			('sizes',('//html',_parser.sizes)),
			]),
		look = dict(
			),
		swatch = dict(
			method = _parser.parse_swatches,
			path='//ul[@class="product-color-list"]/li/a',
			),
		image = dict(
			method = _parser.parse_images,
			),
		size_info = dict(
			),
		)

	list_urls = dict(
		f = dict(
			a = [
				"https://www.bluefly.com/women/women-accessories?startIndex=",
				],
			b = [
				"https://www.bluefly.com/women/handbags-wallets?startIndex="
				],
			c = [
				"https://www.bluefly.com/women/clothing?startIndex="
			],
			s = [
				"https://www.bluefly.com/women/shoes?startIndex="
			],
			e = [
				"https://www.bluefly.com/beauty/women-beauty-fragrance/skincare?startIndex=",
				"https://www.bluefly.com/beauty/women-beauty-fragrance/fragrance?startIndex=",
				"https://www.bluefly.com/beauty/women-beauty-fragrance/cosmetics?startIndex=",
				"https://www.bluefly.com/beauty/women-beauty-fragrance/bath-and-body?startIndex=",
				"https://www.bluefly.com/beauty/women-beauty-fragrance/hair?startIndex=",
			],
		),
		m = dict(
			a = [
				"https://www.bluefly.com/men/men-accessories/watches?startIndex=",
				"https://www.bluefly.com/men/men-accessories/belts?startIndex=",
				"https://www.bluefly.com/men/men-accessories/ties-pocket-squares?startIndex=",
				"https://www.bluefly.com/men/men-accessories/sunglasses?startIndex=",
				"https://www.bluefly.com/men/men-accessories/jewelry-cufflinks/cufflinks?startIndex=",
				"https://www.bluefly.com/men/men-accessories/jewelry-cufflinks/jewelry?startIndex=",
				"https://www.bluefly.com/men/men-accessories/hats?startIndex=",
				"https://www.bluefly.com/men/men-accessories/gloves?startIndex=",
				"https://www.bluefly.com/men/men-accessories/wallets-clips-keychains?startIndex="
			],
			b = [
				"https://www.bluefly.com/men/men-accessories/bags-briefcases?startIndex=",
			],
			c = [
				"https://www.bluefly.com/men/clothing?startIndex="
			],
			s = [
				"https://www.bluefly.com/men/shoes?startIndex="
			],
			e = [
				"https://www.bluefly.com/beauty/men-grooming-cologne?startIndex=",
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

		CN = dict(
			currency = 'CNY',
			discurrency = 'USD',
		),
		JP = dict(
			currency = 'JPY',
			discurrency = 'USD',
		),
		KR = dict(
			currency = 'KRW',
			discurrency = 'USD',
		),
		SG = dict(
			currency = 'SGD',
			discurrency = 'USD',
		),
		HK = dict(
			currency = 'HKD',
			discurrency = 'USD',
		),
		GB = dict(
			currency = 'GBP',
			discurrency = 'USD',
		),
		RU = dict(
			currency = 'RUB',
			discurrency = 'USD',
		),
		CA = dict(
			currency = 'CAD',
			discurrency = 'USD',
		),
		AU = dict(
			currency = 'AUD',
			discurrency = 'USD',
		),
		DE = dict(
			currency = 'EUR',
			discurrency = 'USD',
		),
		NO = dict(
			currency = 'NOK',
			discurrency = 'USD',
		),

		)
