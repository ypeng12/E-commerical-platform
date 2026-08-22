from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.extract_helper import *
from copy import deepcopy
from utils.cfg import *
import re

class Parser(MerchantParser):

	def _page_num(self, data, **kwargs):
		pages = 10
		return pages

	def _list_url(self, i, response_url, **kwargs):
		start = (i - 1) * 80
		url = response_url + '&page=' + str(i) + '&start=' + str(start)
		return url

	def parse_item_url(self, response, **kwargs):
		html = json.loads(response.body)
		for product in html['products']:
			ids = product['id']
			designer = product['author']['name']
			block_designers = [
				'GUCCI',
				'COS',
				'COACH',
				'MICHAEL KORS',
				'CLUB MANACO',
				'TORY BURCH',
				'ALEXANDER WANG',
				'SCOTCH + SODA',
				'WHAT GOES AROUND COMES AROUND',
			]
			if ids == '' or designer in block_designers:
				continue
			# elif designer and not check_designer(designer.strip().upper()):
			# 	self.crawler.stats.inc_value("uncarried")
			# 	continue
			url = 'https://www.shopspring.com/products/' + str(ids)
			yield url, designer

	def _checkout(self, checkout, item, **kwargs):
		if checkout:
			return True
		else:
			return False

	def _name(self, data, item, **kwargs):
		item['name'] = data.extract()[0].split(' by ')[0].strip()
		item['designer'] = data.extract()[0].split(' by ')[1].strip().upper()

	def _parse_json(self, obj, item, **kwargs):
		item['originlistprice'] = obj['original_price']
		item['originsaleprice'] = obj['price']
		self.prices(obj, item, **kwargs)
		item['tmp'] = obj

	def _parse_multi_items(self, response, item, **kwargs):
		obj = item['tmp']
		product_id = obj['id']
		colors = []
		for dimension in obj['dimensions']:
			if dimension['name'].lower() == 'color':
				colors = dimension['values']

		if len(colors) > 1:
			images_ = obj['images']
			if images_[0]['attributes'] == {} or images_[0]['attributes'] == None or 'Color' not in images_[0]['attributes']:
				colors = [colors[0]]
			for color in colors:
				item_color = deepcopy(item)
				count = 0
				item_color['sku'] = str(product_id) + '_' + color.upper()
				images = []
				cover = ''

				for image in images_:
					if image['attributes'] == {} or image['attributes'] == None or 'Color' not in image['attributes']:
						images.append(image['url'].split('?')[0])
					elif image['attributes']['Color'][0] == color:
						cover = image['url'].split('?')[0]
						images.append(image['url'].split('?')[0])
				# if len(images) == 0:
				#     for image in images_:
				#         images.append(image['url'].split('?')[0])
				if len(cover) == 0:
					cover = images[0] if images else ''
				originsizes = []
				sizes = []
				if item['category'] in ['c', 's']:
					for instock in obj['inventory']:
						if instock['attributes']['Color'] == color and instock['count'] != 0:
							count += instock['count']
							if 'Size' in instock['attributes']:
								size = instock['attributes']['Size']
							elif 'U.S. Men/Women Size' in instock['attributes']:
								size = instock['attributes'][
									'U.S. Men/Women Size']
							elif 'Waist' in instock['attributes']:
								size = instock['attributes']['Waist']
							elif 'Shirt Size' in instock['attributes']:
								size = instock['attributes']['Shirt Size']
							elif 'Title' in instock['attributes']:
								size = instock['attributes']['Title']
							else:
								size = 'IT'
							if size not in originsizes:
								originsizes.append(size)
					for size in originsizes:
						if '1/2' in size:
							size = size.replace(' 1/2', '.5')
						if '(' in size:
							size = size.split('(')[0].strip()
						if '/' in size:
							size = size.split('/')[0].strip()
						if ':' in size:
							size = size.split(':')[-1].strip()
						if '=' in size:
							size = size.split('=')[0].strip()
						if re.findall('\D',size.replace(' ', '')) and re.findall('\D',size.replace(' ', ''))[0] == 'M' and len(size) > 1:
							size = size.replace('M','')
						osize = size.replace('Width', '').replace('Womens', '').replace('D', '').replace('W', '').replace('B', '').replace('US', '').replace(',', '.').replace('TAN', '').replace('UK', '').strip()
						osize = osize.encode('utf-8').replace('\xc2', '').replace('\xbd', '.5').replace('1/2', '.5').replace('\xbe', '.75').replace(' ', '')
				if item['category'] in ['b', 'a', 'e']:
					sizes.append('IT') if not sizes else sizes
					originsizes.append('IT')
					for instock in obj['inventory']:
						if instock['attributes']['Color'] == color:
							count = instock['count']
				item_color['originsizes'] = originsizes
				self.sizes(obj, item_color)
				item_color['images'] = images
				item_color['color'] = color.upper()
				item_color['cover'] = item_color['images'][0] if item_color['images'] else ''

				if count == 0:
					item_color['error'] = 'Out Of Stock'
					item_color['originsizes'] = ''
					item_color['sizes'] = ''
				if not item_color['images']:
					continue
				yield item_color
		else:

			if len(colors) == 0:
				sku = str(product_id)
				color = ""
			else:
				color = colors[0].upper()
				sku = str(product_id) + '_' + color
				return
			images = []
			images_ = obj['images']
			cover = ''
			for image in images_:
				if image['attributes'] == {} or image['attributes'] == None or 'Color' not in image['attributes']:
					images.append(image['url'].split('?')[0])
				elif 'Color' in image['attributes'] and image['attributes']['Color'][0] == color:
					# elif image['attributes']['Color'][0] == color:
					cover = image['url'].split('?')[0]
					images.append(image['url'].split('?')[0])

			if len(images) == 0:
				for image in images_:
					images.append(image['url'].split('?')[0])
			if len(cover) == 0:
				cover = images[0]
			originsizes = []
			sizes = []
			if item['category'] in ['c', 's']:
				for instock in obj['inventory']:
					if instock['count'] != 0:
						if 'Size' in instock['attributes']:
							osize = instock['attributes']['Size']
						elif 'U.S. Men/Women Size' in instock['attributes']:
							osize = instock['attributes'][
								'U.S. Men/Women Size']
						elif 'Waist' in instock['attributes']:
							osize = instock['attributes']['Waist']
						elif 'Shirt Size' in instock['attributes']:
							osize = instock['attributes']['Shirt Size']
						elif 'Title' in instock['attributes']:
							osize = instock['attributes']['Title']
						else:
							osize = 'IT'
						if osize not in originsizes:
							originsizes.append(osize)
				for size in originsizes:
					if '1/2' in size:
						size = size.replace(' 1/2', '.5')
					if '(' in size:
						size = size.split('(')[0].strip()
					if '/' in size:
						size = size.split('/')[0].strip()
					if ':' in size:
						size = size.split(':')[-1].strip()
					if '=' in size:
						size = size.split('=')[0].strip()
					if re.findall('\D',size.replace(' ', '')) and re.findall('\D',size.replace(' ', ''))[0] == 'M' and len(size) > 1:
						size = size.replace('M','')
					osize = size.replace('Width', '').replace('Womens', '').replace('D', '').replace('W', '').replace('B', '').replace('US', '').replace(',', '.').replace('TAN', '').replace('UK', '').strip()
					osize = osize.encode('utf-8').replace('\xc2', '').replace('\xbd', '.5').replace('1/2', '.5').replace('\xbe', '.75').replace(' ', '')
			if item['category'] in ['b', 'a', 'e']:
				sizes.append('IT') if not sizes else sizes
				originsizes.append('IT')
			count = obj['inventory_count']
			item['sizes'] = sizes
			item['originsizes'] = originsizes
			self.sizes(obj, item)
			item['images'] = images
			item['color'] = color
			item['cover'] = images[0]
			item['sku'] = sku
			if count == 0:
				item['error'] = 'Out Of Stock'
				item['originsizes'] = ''
				item['sizes'] = ''
				yield item
				return
			yield item



	def _parse_images(self, response, **kwargs):
		pass
		#DB returning MatchFashion Link
		# json = response.xpath('//script//text()').extract()
		# script = ''
		# for j in json:
		# 	if 'injectedProduct' in j:
		# 		script = j
		# 		break
		# print json
		# script = script.split('injectedProduct = ')[-1].split(';\n')[0]
		# print script
		# obj = json.loads(script)
		# print obj

	def _parse_swatches(self, response, swatch_path, **kwargs):
		product_info = re.findall('injectedProduct =(.*)', response.body)
		product_info = product_info[0].strip().replace(';', '')
		product = json.loads(product_info)
		colors = []
		try:
			for dimension in product['dimensions']:
				if dimension['name'].lower() == 'color':
					colors = dimension['values']
		except:
			return
		images = product['images']
		
		if len(colors) <= 1 or 'Color' not in images[0]['attributes']:
			return
		images = product['images']
		swatches = []
		for color in colors:
			pid = str(product['id']) + '_' + color.upper()
			for image in images:
				if image['attributes'] and image['attributes']['Color'][0].lower() == color.lower():
					img = image['url'].split('?')[0] + '?w=80&h=80'
					swatch = {
						'img': img,
						'pid': pid,
					}
					break
			swatches.append(swatch)
		return swatches

_parser = Parser()



class Config(MerchantConfig):
	name = 'spring'
	merchant = 'SPRING'


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//*[@id="pc-top"]/div[1]/span/text()', _parser.page_num),
			list_url = _parser.list_url,
			parse_item_url = _parser.parse_item_url,
			items = '//div[@data-xfe-testid="products_list"]/ul/li',
			designer = './/span[@data-xfe-testid="brand_name"]/text()',
			link = './a/@href',
			),
		product = OrderedDict([
			# ('checkout',('//span[contains(@class,"itemSoldOutMessageText")]', _parser.checkout)),
			('name', ('//meta[@property="og:title"]/@content', _parser.name)),
			('description','//meta[@property="og:description"]/@content'),
			]),
		look = dict(
			),
		swatch = dict(
			method = _parser.parse_swatches,
			path='//div[@id="colors"]/div[@class="colors"]/ul/div',
			current_path='//input[@name="ProductCode"]/@value',
			),
		image = dict(
			method = _parser.parse_images,
			),
		size_info = dict(
			),
		)

	json_path = dict(
		method = _parser.parse_json,
		obj_path = '//script',
		keyword = 'injectedProduct',
		flag = ('injectedProduct = ',';\n'),
		field = dict(
			)
		)

	parse_multi_items = _parser.parse_multi_items

	list_urls = dict(
		f = dict(
			a = [
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Ajewelry_accessories%3Aaccessories&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Ajewelry_accessories%3Ajewelry&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Ajewelry_accessories&refine_flags=on_sale&sortBy=popular&sortOrder=DESC'
			],
			b = [
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Ahandbags&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Ahandbags&refine_flags=on_sale&sortBy=popular&sortOrder=DESC'
			],
			c = [
				"https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Aclothing&sortBy=popular&sortOrder=DESC",
				"https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Aclothing&refine_flags=on_sale&sortBy=popular&sortOrder=DESC",
			],
			s = [
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Ashoes&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=women%3Ashoes&refine_flags=on_sale&sortBy=popular&sortOrder=DESC'
			],
			e = [
				"https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=beauty%3Awomens_beauty&sortBy=popular&sortOrder=DESC&_=1518978173495",
				"https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=beauty&refine_flags=on_sale&sortBy=popular&sortOrder=DESC&_=1518978362388",
			]
		),
		m = dict(
			a = [
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Abags_leather_goods%3Awallets_cardholders&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Abelts_suspenders&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Awatches&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Aties_pocket_squares&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Acufflinks_jewelry&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Ascarves&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Ahats&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Agloves&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Asunglasses&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Aoptical&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Aother_accessories&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Abags_leather_goods%3Awallets_cardholders&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Abelts_suspenders&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Awatches&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Aties_pocket_squares&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Acufflinks_jewelry&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Ascarves&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Ahats&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Agloves&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Asunglasses&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Aoptical&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Aother_accessories&refine_flags=on_sale&sortBy=popular&sortOrder=DESC',
			],
			b = [
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Abags_leather_goods%3Abags_backpacks&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aaccessories%3Abags_leather_goods%3Abags_backpacks&refine_flags=on_sale&sortBy=popular&sortOrder=DESC'
			],
			c = [
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aclothing&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Aclothing&refine_flags=on_sale&sortBy=popular&sortOrder=DESC'
			],
			s = [
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Ashoes&sortBy=popular&sortOrder=DESC',
				'https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=men%3Ashoes&refine_flags=on_sale&sortBy=popular&sortOrder=DESC'
			],
			e = [
				"https://www.shopspring.com/api/1/productsWithRefinements/?taxonomy=beauty%3Amens_grooming&sortBy=popular&sortOrder=DESC&_=1518978319652",
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

		


