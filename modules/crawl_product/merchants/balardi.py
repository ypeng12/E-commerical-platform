from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import unquote

class Parser(MerchantParser):
    def _parse_num(self,pages,**kwargs):
        item_num = []
        if pages not in item_num:
            item_num.append(pages)
        return item_num[-2]

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?p=1','').replace('?p=','') + '?p=' + str(i)
        return url

    def _checkout(self, checkout, item, **kwargs):
        sold_out = checkout.extract()
        if sold_out:
            return True
        else:
            return False

    def _sku(self,sku,item,**kwargs):
        sku = sku.extract_first()
        item['sku'] = (re.findall(r'ReferenceIdentifier: \\"([\d]+?)\\"',sku.strip()))[0]

    def _designer(self,designer,item, **kwargs):
        item['designer'] = designer.extract()[0].upper().strip()

    def _description(self, desc, item, **kwargs):
        description = []
        for d in desc.extract():
            if d.strip():
                description.append(d.strip("\n"))
        item['description'] = '\n'.join(description)

    def _color(self, colors, item, **kwargs):
        color_li = []
        for c in colors.extract():
            try:
                if "Color" in c:
                    color1 = c.split("Color")[1].split("<br>")[0]
                    if "span" in color1:
                        try:
                            color = color1.split(';">')[1].split("</")[0]
                            color_li.append(color.strip().strip(":").strip("</b>").strip("</p").strip("span").strip(">"))
                        except:
                            if "span>" in color1:
                                color_li.append(color1.split('span>')[1].split(' ')[0])
                            else:
                                color_li.append(color1.strip('span>').rsplit(';">')[1].strip('</p'))
                    else:
                        color_li.append(color1.strip(":").strip("</b>").strip("</p").strip())
                item["color"] = ((color_li[0] if color_li else []).strip("</b>")).upper()
            except:
                for i in c:
                    if "Color" in i:
                        color = colors[(colors.index("Color:")) + 1]
                        item["color"] = (color.strip("</p")).upper()
                item["color"] = ''

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath(".//span[1]/span/text()").extract_first()
        saleprice = prices.xpath(".//span[@class='notranslate']/span/text()").extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _images(self, images, item, **kwargs):
        images_li = images.xpath('//script[contains(text(),"productImagesGSUrls")]/text()').extract()
        list_image = []
        for img in images_li:
            images_json = re.findall(r'productImagesGSUrls.push\((.*?)\)',img)
            for images in images_json:
                image = unquote(re.search(r'"(.*?)"',images).group(1))
                image_dict = json.loads('{"a":"' + image.rsplit('\\',1)[0] + '"}')
                if "https:" not in image_dict['a']:
                    list_image.append("https:" + image_dict['a'].replace('_240x','_960x'))
        item["images"] = list_image
        item["cover"] = list_image[0]

    def _sizes(self, sizes, item, **kwargs):
        osizes = sizes.extract()
        sizes = []
        for size in osizes:
            if size not in sizes:
                sizes.append(size)
        item['originsizes'] = sizes

    def _name(self,res,item,**kwargs):
        try:
            name = res.extract()[1]
        except:
            name = res.extract_first()
        item["name"] = name.strip("\n").strip()

    def _parse_images(self,response,**kwargs):
        images_li = response.xpath('//script[contains(text(),"productImagesGSUrls")]/text()').extract()
        list_image = []
        for img in images_li:
            images_json = re.findall(r'productImagesGSUrls.push\((.*?)\)',img)
            for images in images_json:
                image = unquote(re.search(r'"(.*?)"',images).group(1))
                image_dict = json.loads('{"a":"' + image.rsplit('\\',1)[0] + '"}')
                if "https:" not in image_dict['a']:
                    list_image.append("https:" + image_dict['a'].replace('_240x','_960x'))

        return list_image

_parser = Parser()


class Config(MerchantConfig):
    name = "balardi"
    merchant = "BALARDI"

    path = dict(
        base=dict(
        ),
        plist=dict(
            page_num=('//div[@class="pagination"]/div/span', _parser.page_num),
            list_url=('//html',_parser.list_url)
        ),
        product=OrderedDict([
            ('checkout', (
            "//div[@class='product-page-info__title mb-15 text-lg-left']/p/text()",
            _parser.checkout)),
            ('sku', ('//script[contains(text(),"LimeSpot.PageInfo = ")]',_parser.sku)),
            ('name', ('//div[@class="product-page-info"]/div/h1/text()',_parser.name)),
            ('designer', ('//div["product-page-info"]/div/h1/span/text()',_parser.designer)),
            ('description', ('//div[@class="chen-desc55"]/table/tr/td/text()', _parser.description)),
            ('color', ('//div[@class="chen-desc55"]//p', _parser.color)),
            ('prices', ('//span[@class="price price--sale notranslate"]', _parser.prices)),
            ('images', ('//html', _parser.images)),
            ('sizes', ('//div[@class="product-page-info__variants mb-15 d-none"]/select/option/text()', _parser.sizes)),
        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look=dict(
        ),
        swatch=dict(
        ),
    )

    countries = dict(
        US=dict(
            language='EN',
            area='US',
            currency='USD',
        ),
        GB=dict(
            currency='GBP',
            duscurrency='USD',

        ),
        DE=dict(
            currency='EUR',
            duscurrency='USD'
        ),
        CA=dict(
            currency='CAD',
            duscurrency='USD',
        ),
        AU=dict(
            currency='AUD',
            duscurrency='USD',
        ),
        RU=dict(
            currency='RUB',
            duscurrency="USD",
        ),
    )