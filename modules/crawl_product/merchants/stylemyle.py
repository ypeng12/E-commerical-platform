from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *

class Parser(MerchantParser):

	def _checkout(self, checkout, item, **kwargs):
		if checkout:
			return False
		else:
			return True

	def _description(self, description, item, **kwargs):
		descs = description.extract()
		desc_str = []
		for desc in descs:
			if desc.strip():
				desc_str.append(desc.strip())
		item['description'] = '\n'.join(desc_str)

	def _prices(self, prices, item, **kwargs):
		listprice = prices.xpath('./h2[@class="price_old"]/text()').extract_first()
		saleprice = prices.xpath('./h2[@id="displayed_price"]/text()').extract_first()
		item['originlistprice'] = listprice if listprice else saleprice
		item['originsaleprice'] = saleprice

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

	def _sizes(self, sizes, item, **kwargs):
		sizes_data = sizes.extract()
		sizes = []
		for osize in sizes_data:
			if "Choose Your Size" not in osize and "SOLD OUT" not in osize:
				sizes.append(osize.split(' - ')[0])

		if not sizes and item['category'] in ['a','b']:
			sizes = ['IT']

		item['originsizes'] = sizes

	def _parse_images(self, response, **kwargs):
		images = []
		imgs = response.extract()
		for img in imgs:
			if img not in images:
				images.append(img)
			
		return images

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract()
		fits = []
		for info in infos:
			fits.append(info.strip())
		size_info = '\n'.join(fits)
		return size_info

	def _page_num(self, data, **kwargs):
		nums = data.split('&page=')[1]
		return int(nums)

	def _list_url(self, i, response_url, **kwargs):
		url = response_url.format(i)
		return url

_parser = Parser()


class Config(MerchantConfig):
	name = "stylemyle"
	merchant = "Stylemyle"

	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//div[@class="pagination_controls"]/a[contains(text(),"last")]/@href', _parser.page_num),
			list_url = _parser.list_url,
			items = '//div[@class="col-md-4 col-sm-6 col-xs-6"]',
			designer = './/div[@class="description-holder"]/h3/text()',
			link = './a[@itemprop="url"]/@href',
			),
		product = OrderedDict([
			('checkout',('//button[@id="add-to-cart-button"]', _parser.checkout)),
			('sku', '//div[@class="product_desc_code"]/span/text()'),
			('name', '//div[@class="col-md-6 product_desc"]/h3/text()'),
			('designer', '//div[@class="col-md-6 product_desc"]/h1/a/text()'),
			('color', ('//div[contains(@class,"prod_spec_visible")]/text()', _parser.color)),
			('description', ('//div[@class="product_spec_content"]/ul/li/text()',_parser.description)),
			('prices', ('//form[@id="add_to_bag_form"]', _parser.prices)),
			('images',('//div[@class="product_wrapper"]/div[@class="selectors"]/a/img[@class="selector-img"]/@src',_parser.images)),
			('sizes',('//select[@name="variant_id"]/option/text()',_parser.sizes)),
			]),
		look = dict(
			),
		swatch = dict(
			),
		image = dict(
			image_path = '//div[@class="product_wrapper"]/div[@class="selectors"]/a/img[@class="selector-img"]/@src',
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = 'class="product_spec_content prod_spec_visible"',
			),
		designer = dict(
			),
		checknum = dict(
            ),
		)


	list_urls = dict(
		f = dict(
			a = [
				"https://stylemyle.com/shop/t/women/accessories?page={}",
				],
			b = [
				"https://stylemyle.com/shop/t/women/bags?page={}"
				],
			c = [
				"https://stylemyle.com/shop/t/women/clothing?page={}"
			],
			s = [
				"https://stylemyle.com/shop/t/women/shoes?page={}"
			],
			e = [
				"https://stylemyle.com/shop/t/women/beauty?page={}"
			]
		),
		m = dict(
			a = [
				"https://stylemyle.com/shop/t/men/accessories?page={}"
			],
			b = [
				"https://stylemyle.com/shop/t/men/bags?page={}"
			],
			c = [
				"https://stylemyle.com/shop/t/men/clothing?page={}"
			],
			s = [
				"https://stylemyle.com/shop/t/men/shoes?page={}"
			],
			e = [
				"https://stylemyle.com/shop/t/men/grooming?page={}"
			],
		),
		k = dict(
			a = [
				"https://stylemyle.com/shop/t/kids/accessories?page={}"
			],
			b = [
				"https://stylemyle.com/shop/t/kids/bags?page={}"
			],
			c = [
				"https://stylemyle.com/shop/t/kids/clothing?page={}"
			],
			s = [
				"https://stylemyle.com/shop/t/kids/shoes?page={}"
			],
		)
	)

	countries = dict(
		US = dict(
			language = 'EN', 
			area = 'US',
			currency = 'USD',
		),
		)
