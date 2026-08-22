from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from lxml import etree

from utils.utils import *

class Parser(MerchantParser):
	def _checkout(self, checkout, item, **kwargs):
		if checkout:
			return False
		else:
			return True

	def _sku(self, data, item, **kwargs):
		pid = data.extract_first().upper()
		if item['color']:
			item['sku'] = pid + '_' + item['color'].strip().upper()
		else:
			item['sku'] = pid
		item['designer'] = "LOUIS VUITTON"

	def _prices(self, prices, item, **kwargs):
		item['originsaleprice'] = prices.xpath('./div[@class="priceValue"]/text()').extract_first()
		item['originlistprice'] = prices.xpath('./div[@class="priceValue"]/text()').extract_first()

	def _sizes(self, sizes, item, **kwargs):
		orisizes = []
		if kwargs['category'] in ['a','b','e']:
			size_sku = sizes.xpath('.//span[@class="sku"]/text()').extract_first()
			sizeurl = 'https://secure.louisvuitton.com/ajaxsecure/getStockLevel.jsp?storeLang=eng-us&pageType=product&skuIdList=' + size_sku
			result = getwebcontent(sizeurl)
			avail = json.loads(result)
			
			if avail[size_sku]['inStock']:
				orisizes = ['IT']
			else:
				orisizes = []
		else:
			size_list = sizes.xpath('.//*[@id="size"]/li/@data-sku').extract()
			size_sku = ','.join(size_list)
			sizeurl = 'https://secure.louisvuitton.com/ajaxsecure/getStockLevel.jsp?storeLang=eng-us&pageType=product&skuIdList=' + str(size_sku)
			result = getwebcontent(sizeurl)
			avail = json.loads(result)
			for size in size_list:
				if avail[size]['inStock']:
					size_path = './/*[@id="size"]/li[@data-sku="%s"]/@data-ona' %size
					osize = sizes.xpath(size_path).extract()[0].split('/')[-1]
					orisizes.append(osize)
		item['originsizes'] = orisizes

	def _images(self, images, item, **kwargs):
		imgs = images.xpath('.//ul[@class="thumbnails"]/li//source/@data-src').extract()
		if not imgs:
			imgs = images.xpath('.//meta[@property="og:image"]/@content').extract()
		item['images'] = []
		for img in imgs:
			item['images'].append(img.split('?')[0] + '?wid=600&hei=600')
		item['cover'] = item['images'][0] if item['images'] else ''

	def _parse_item_url(self, response, **kwargs):
		url = response.url
		try:
			pages = int(response.xpath('//a[contains(@href,"pagination")]/text()').extract()[-1])
		except:
			pages = 1
		for i in range(0, pages):
			url = response.url + str(i*15)
			result = getwebcontent(url)		
			html = etree.HTML(result)
			for quote in html.xpath('//a[contains(@id,"sku")]'):
				href = quote.xpath('./@href')
				if href is None:
					continue
				href = 'https://us.louisvuitton.com/'+quote.xpath('./@href')[0]
				designer='LOUIS VUITTON'
				yield href, designer

	def _parse_images(self, response, **kwargs):
		imgs = response.xpath('//ul[@class="thumbnails"]/li//source/@data-src').extract()
		if not imgs:
			imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
		images = []
		for img in imgs:
			images.append(img.split('?')[0] + '?wid=600&hei=600')

		return images

	def _parse_swatches(self, response, swatch_path, **kwargs):
		datas = response.xpath(swatch_path['path'])
		swatches = []
		pid_1 = response.xpath(swatch_path['current_path']).extract()[0].strip()
		swatches.append(pid_1)
		for data in datas:
			pid = data.xpath('./@data-sku').extract()[0]
			swatches.append(pid)

		if len(swatches)>1:
			return swatches

	def _parse_look(self, item, look_path, response, **kwargs):
		try:
			outfits = response.xpath('//*[@id="completeTheLook"]//div[@id="youMayAlsoLikeML"]//ul/li//a/@href').extract()[1:]
		except Exception as e:
			logger.info('get outfit info error! @ %s', response.url)
			logger.debug(traceback.format_exc())
			return
		if not outfits:
			logger.info('outfit info none@ %s', response.url)
			return

		pid = response.meta.get('sku')
		item['main_prd'] = pid
		try:
			cover = response.xpath('//img[@id="productMainImage"]/@data-src').extract_first()
			item['cover'] = cover.replace('{IMG_WIDTH}','600').replace('{IMG_HEIGHT}','876')
		except:
			pass
		look_key = response.xpath('//*[@id="completeTheLook"]//div[@id="youMayAlsoLikeML"]//ul/li//a/@href').extract_first()
		try:
			item['look_key'] = look_key.split('-')[-1].replace('nvprod','').replace('v','')
		except:
			pass
		item['products']= map(lambda x:str(x).split('#')[-1], outfits)
		yield item

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract()
		fits = []
		for info in infos:
			if info.strip() and info.strip() not in fits and ('cm' in info.strip().lower() or 'inche' in info.strip().lower() or 'model' in info.strip().lower() or 'mm' in info.strip().lower() or 'measurements' in info.strip().lower()):
				fits.append(info.strip())
		size_info = '\n'.join(fits)
		return size_info


_parser = Parser()


class Config(MerchantConfig):
	name = 'lv'
	merchant = 'LOUIS VUITTON'


	path = dict(
		base = dict(
			),
		plist = dict(
			# page_num = ('//html',_parser.page_num),
			parse_item_url = _parser.parse_item_url,
			items = '//div[@class="pl-page"]/a[contains(@id,"sku")]',
			designer = '//html',
			link = './@href'
			),
		product = OrderedDict([
			('checkout', ('//input[@id="addToWishListFormProductId"]/@value', _parser.checkout)),
			('name', '//*[@id="productName"]/text()'),
			('color','//li[@id="marketingColorList"]//span[@class="topPanelValue"]/text()'),
			('sku', ('//input[@id="addToWishListFormProductId"]/@value', _parser.sku)),
			('images', ('//html', _parser.images)),
			('description', '//div[@id="productDescription"]/div/text()'),
			('prices', ('//div[@class="priceBlock"]', _parser.prices)),
			('sizes',('//html',_parser.sizes)),
			]),
		look = dict(
			method = _parser.parse_look,
			type='html',
			url_type='url',
			key_type='sku',
            official_uid=62253,
            ),
		swatch = dict(
			method = _parser.parse_swatches,
			path='//ul[@class="paletteContainer Color"]/li/a',
			current_path='//div[@class="sku reading-and-link-text"]/text()',
			image_path = '//noscript/img/@src'
			),
		image = dict(
			method = _parser.parse_images,
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = '//div[@class="innerContent functional-text"]/ul/li/text()',
			),
		)

	list_urls = dict(
		f = dict(
			a = [
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/accessories/scarves-shawls-more/_/N-otpzrm?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/accessories/fashion-jewelry/_/N-uw27gv?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/accessories/leather-bracelets/_/N-1fc51io?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/accessories/belts/_/N-1nwpdde?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/accessories/sunglasses/_/N-l9u6f5?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/accessories/key-holders-bag-charms-more/_/N-q2f1wz?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/fine-jewelry/_/N-75u08p?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/timepieces/_/N-1wv8w4e?storeLang=eng-us&pageType=category&No="
			],
			b = [
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/handbags/_/N-r4xtxc?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/small-leather-goods/wallets/_/N-14qpe8r?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/travel/_/N-1pbfeqc?storeLang=eng-us&pageType=category&No="
			],
			c = [
				"https://us.louisvuitton.com/ajax/endeca/browse-frag//ready-to-wear/allcollections/_/N-foobia?storeLang=eng-us&pageType=category&No="

			],
			s = [
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/women/shoes/_/N-12x7xd9?storeLang=eng-us&pageType=category&No=",
			],
			e = [
				"https://us.louisvuitton.com/eng-us/women/fragrances/discover-the-collection/_/N-i6ksld?storeLang=eng-us&pageType=category&No="
			],
		),
		m = dict(
			a = [
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/accessories/belts/_/N-msbya5?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/accessories/scarves-ties-more/_/N-j230qx?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/accessories/fashion-jewelry/_/N-lovcfa?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/accessories/leather-bracelets/_/N-w353e?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/accessories/sunglasses/_/N-n6fzbv?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/accessories/key-holders-more/_/N-2p1ptt?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/timepieces-jewelry/timepieces/_/N-1c6buoi?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/timepieces-jewelry/fine-jewelry/_/N-11fid5w?storeLang=eng-us&pageType=category&No=",
			],
			b = [
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/small-leather-goods/wallets/_/N-cohkqb?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/bags/_/N-1nmtau6?storeLang=eng-us&pageType=category&No=",
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/travel-luggage/_/N-7rya1y?storeLang=eng-us&pageType=category&No="
			],
			c = [
				"https://us.louisvuitton.com/ajax/endeca/browse-frag//men/ready-to-wear/all-collections/_/N-8wehhh?storeLang=eng-us&pageType=category&No="
			],
			s = [
				"http://us.louisvuitton.com/ajax/endeca/browse-frag/men/shoes/_/N-1fioqoi?storeLang=eng-us&pageType=category&No="
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
			),

		)

		


