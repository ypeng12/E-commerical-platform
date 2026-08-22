# -*- coding: utf-8 -*-
import re
import json
from .size_convert import *
from .utils import *
from functools import cmp_to_key

SIZE_CONVERT_PATTERNS = [
    '(?P<age>[\d+\.]+)\s*(?P<format>YEAR|YAR|Y|MON|MTH|M)',
    '(?P<format>YEAR|YAR|Y|MON|MTH|M)\s*(?P<age>[\d+\.]+)',
    '(?P<num>\d*)(?P<x>x*)(\-|\s)*((?P<s>S|SM|SML|SMALL)|(?P<m>M|MED|MEDIUM)|(?P<l>L|LG|LRG|LARGE))*',
    '(?P<format>AG|AU|CM|DE|DK|DT|EU|FR|GE|IT|IN|JP|KR|NU|RU|UK|US|OZ|ML|WA)\s*(?P<code>[\d+\.]+)',
    '(?P<code>[\d+\.]+)\s*(?P<format>AG|AU|CM|DE|DK|DT|EU|FR|GE|IT|IN|JP|KR|NU|RU|UK|US|OZ|ML|WA)',
    # TODO: ...
]

code_size_fmt = "{}{}"
std_size_fmt = "{}{}{}"
age_size_fmt = "{}{}"
num_size_fmt = "{}{}"


def parseSize(item, orisize, gender, category, size_standard, size_tag):
    merchant = item['merchant']
    designer = item['designer'].upper()
    if designer in size_standard and 'merged_to_id' in size_standard[designer]:
        designer = size_standard[designer]['merged_to_id']
    orisize = 'US00' if orisize == '00' and size_tag != 'NU' else orisize
    parsed_size = orisize

    try:
        num = float(orisize)
        size_tag = size_tag if size_tag else get_size_tag(merchant, num, gender, category, designer, size_standard)

        parsed_size = num_size_fmt.format(size_tag, num)
    except:
        for pattern in SIZE_CONVERT_PATTERNS:
            match = re.match(pattern, orisize, re.IGNORECASE)
            if match:
                match = match.groupdict()
                if match.get('num') and match.get('m'):
                    continue
                if match.get('s') or match.get('m') or match.get('l'):
                    x = match.get('x','')
                    num = match.get('num', '') or len(x) or ''
                    num = '' if num == 1 else num
                    size_ = match.get('s') or match.get('m') or match.get('l')
                    size_ = size_[:1]
                    x = x[0] if x else ''
                    parsed_size = std_size_fmt.format(num, x, size_)
                    size_tag = 'ST'
                    break
                elif match.get('code'):
                    code = match.get('code')
                    size_tag = match.get('format','')
                    if size_tag in ['CM','IN','ML','OZ']:
                        parsed_size = code_size_fmt.format(code, size_tag)
                    else:
                        parsed_size = code_size_fmt.format(size_tag, code)
                    break
                elif match.get('age'):
                    code = match.get('age')
                    parsed_size = age_size_fmt.format(code, match.get('format','')[0])
                    size_tag = 'AG'
                    break

    parsed_size = parsed_size.replace('.0', '').upper() if parsed_size.endswith('.0') else parsed_size.upper()
    size_tag = size_tag if size_tag else parsed_size[:2]

    if size_tag == 'NU' and orisize == '00':
        parsed_size = '00'

    return size_tag, parsed_size

def get_size_tag(merchant, num, gender, category, designer, size_standard):
    size_type_1 = ['US', 'UK', 'NU', 'AU']
    size_type_2 = ['IT', 'EU', 'FR', 'DE', 'DK', 'GE', 'RU']
    size_tag = ''
    if category == 'c':
        if gender == 'm':
            if num < 18:
                size_tag = 'US'
            elif num < 38:
                size_tag = 'WA'
            else:
                size_tag = "IT"
        else:
            if num < 18:
                size_tag = 'US'
            elif num < 32:
                size_tag = 'WA'
            else:
                size_tag = 'IT'
    if category == 's':
        if num < 20:
            size_tag = 'US'
        else:
            size_tag = 'IT'

    if category in ['c', 's'] and size_tag in ['UK', 'US']:
        try:
            merchant_id = merchant if merchant in size_standard[designer] else 'default'
            size_tag = size_standard[designer][merchant_id][gender][category]
        except:
            pass

        if merchant in ['Nordstrom', 'Nordstrom Rack'] and size_tag != 'NU':
            size_tag = 'US'
        elif merchant in ['24S', 'BURBERRY', 'Harrods', 'Harvey Nichols', 'Liberty', 'Modes', 'Selfridges', 'Superdry', 'Fenwick', 'GIGLIO.COM'] and size_tag != 'NU':
            size_tag = 'UK'

        # try:
        #     merchant = merchant if merchant in size_standard[designer] else 'default'
        #     size_tag_tmp = size_standard[designer][merchant][gender][category]
        # except:
        #     size_tag_tmp = None

        # if size_tag_tmp == 'NU':
        #     size_tag = 'NU'

        return size_tag

    if designer in size_standard and size_tag != 'WA':
        size_tag_1 = size_tag
        try:
            merchant_id = merchant if merchant in size_standard[designer] else 'default'
            size_tag = size_standard[designer][merchant_id][gender][category]
        except:
            pass

        if (size_tag_1 == 'US' and size_tag in size_type_2) or (size_tag_1 == 'IT' and size_tag in size_type_1):
            size_tag = size_tag_1

    return size_tag

def size_cmp(s1, s2):
    try:
        s1 = s1.split('-')[1].strip()
        s2 = s2.split('-')[1].strip()
    except:
        pass
    s1 = s1.upper().replace(' ','')
    s2 = s2.upper().replace(' ','')

    if s1 == s2:
        return 0

    std_sizes = [ '5XS', '4XS', '3XS', '2XS', 'XS', 'S', 'M',
                       'L', 'XL', '2XL', '3XL', '4XL', '5XL', '6XL' ]
    if s1 in std_sizes and s2 in std_sizes:
        return -1 if std_sizes.index(s1) < std_sizes.index(s2) else 1
    elif s1 in std_sizes and not s2 in std_sizes:
        return 1
    elif not s1 in std_sizes and s2 in std_sizes:
        return -1

    pattern = r'^([A-Z]+)(\d+|\d+\.\d+)$'
    match1 = re.match(pattern, s1)
    match2 = re.match(pattern, s2)

    if match1 and match2 and match1.group(1) == match2.group(1):
        return -1 if float(match1.group(2)) < float(match2.group(2)) else 1

    pattern = r'^(\d+|\d+\.\d+)([A-Z]+)$'
    match1 = re.match(pattern, s1)
    match2 = re.match(pattern, s2)

    if match1 and match2 and match1.group(2) == match2.group(2):
        return -1 if float(match1.group(1)) < float(match2.group(1)) else 1

    return -1 if s1 < s2 else 1


def size_sorted(ori_sizes, parsed_sizes, sizes, category):
    if category in ['a' ,'b', 'e', 'h']:
        ori_sizes = ';'.join(sorted([x[0].strip()+'-'+x[1]+'-'+x[2] for x in zip(sizes,parsed_sizes,ori_sizes)], key=cmp_to_key(size_cmp))) + ';'
    else:
        ori_sizes = ';'.join(sorted([x[0].replace('IT','').strip()+'-'+x[1]+'-'+x[2] for x in zip(sizes,parsed_sizes,ori_sizes)], key=cmp_to_key(size_cmp))) + ';'
    parsed_sizes = ';'.join(sorted(parsed_sizes, key=cmp_to_key(size_cmp))) + ';'
    sizes = ';'.join(sorted(sizes, key=cmp_to_key(size_cmp))) + ';'

    return ori_sizes, parsed_sizes, sizes


def parse_sizes(item, ori_sizes, ori_sizes2, offset=None, size_standard={}):
    parsed_sizes = []
    sizes = []
    ori_sizes = ori_sizes if ori_sizes else 'One Size'
    ori_sizes2 = ori_sizes2 if ori_sizes2 else ori_sizes

    if item['gender'] in ['f','u']:
        gender = 'f'
    elif item['gender'] in ['k','c','g','b','i','r','y']:
        gender = 'k'
    else:
        gender = item['gender']
    category = item['category']
    designer = item['designer'].upper()

    if ':p' in ori_sizes:
        memo = ':p;'
    elif ':b' in ori_sizes:
        memo = ':b;'
    elif ':f' in ori_sizes:
        memo = ':f;'
    else:
        memo = ';'

    ori_sizes = ori_sizes.replace('\xbd','.5').replace(';;',';')
    ori_sizes2 = ori_sizes2.upper().replace(':P','').replace(':B','').replace(':F','').replace('\xbd','.5').replace('OZ.','OZ').replace('FL OZ','OZ').replace('NUM','NU').replace('WAIST US', 'WA').replace(',','.').replace(';;',';').replace(' CM','CM').replace(' ML','ML').replace('EUR','IT')
    ori_sizes2 = ';'.join([size.split(':')[0] for size in ori_sizes2.split(';')]) if ':' in ori_sizes2 else ori_sizes2

    uni_size = ori_sizes2.replace(' ','').replace('-','').replace('/','')
    if category in ['a', 'b', 'e', 'h'] and uni_size in ['U','IT','OS','NO','NS','NA','N/A','TU','PZ','01','ONE','ALL','FFF','IT00','OSFA','\u5747\u7801','EINHEITSGRÖßE','EINHEITSGRÖSSE','ワンサイズ'] or 'ONESIZE' in uni_size or 'NOSIZE' in uni_size or ('UNI' in uni_size and 'JUNIOR' not in uni_size):
        if ':' in ori_sizes and ori_sizes.split(':')[-1].isdigit():
            memo = '{}:{};'.format(memo.replace(';',''), ori_sizes.split(':')[-1])
        ori_sizes = 'IT-IT-One Size;'
        return ori_sizes.replace(';',memo), 'IT;', 'IT;'

    if category in ['a', 'b', 'e', 'h']:
        if not ori_sizes:
            return 'IT-IT-One Size;', 'IT;', 'IT;'

        for ori_size in ori_sizes2.split(';'):
            size_tag, parsed_size = parseSize(item, ori_size, gender, category, size_standard, None)

            if category in ['a', 'e'] and size_tag in SIZES_CONVERT['u'][category]:
                parsed_size = SIZES_CONVERT['u'][category][size_tag].get(parsed_size, parsed_size)
            else:
                parsed_size = ori_size

            parsed_sizes.append(parsed_size)
            size = parsed_size[:-2].strip() if parsed_size.endswith('ML') or parsed_size.endswith('CM') else parsed_size
            sizes.append(size)

        ori_sizes, parsed_sizes, sizes = size_sorted(ori_sizes.split(';'), parsed_sizes, sizes, category)
        sizes = 'IT;'

    elif category in ['c', 's']:
        size_tag = ''
        if category == 'c' and any(ori_size in ['1', '3', '5', '7', '01', '0P', '0/P', 'I', 'II', 'III', 'IV', 'V'] for ori_size in ori_sizes2.split(';')):
            size_tag = 'NU'
        for ori_size in ori_sizes2.split(';'):
            size_tag, parsed_size = parseSize(item, ori_size.strip(), gender, category, size_standard, size_tag)

            if size_tag == 'GE':
                size_tag = 'DE'
                parsed_size = parsed_size.replace('GE', 'DE')
            if size_tag == 'NU':
                parsed_size = parsed_size.replace('NU', '')
            if size_tag == 'WA' and any(ori_size in ['40', '42', '44', '46'] for ori_size in ori_sizes2.split(';')):
                size_tag = 'IT'
                parsed_size = parsed_size.replace('WA', 'IT')

            parsed_sizes.append(parsed_size)

            try:
                if designer in size_standard and 'merged_to_id' in size_standard[designer]:
                    designer = size_standard[designer]['merged_to_id']

                if 'block' in size_standard[designer] and item['merchant'] in size_standard[designer]['block']:
                    size = 'IT' + size_standard[designer]['sizechart'][gender][category]['IT'][index]

                index = size_standard[designer]['sizechart'][gender][category][size_tag].index(parsed_size.replace(size_tag,''))
                size = 'IT' + size_standard[designer]['sizechart'][gender][category]['IT'][index]

            except Exception as e:
                if size_tag in SIZES_CONVERT[gender][category]:
                    size = SIZES_CONVERT[gender][category][size_tag].get(parsed_size, parsed_size)
                    try:
                        size = SizeFix.objects.fix_size(item['merchant'],designer,item['gender'],item['category'],size_tag,float(size.replace('IT','')))
                        size = 'IT' + str(size)
                        size = size[:-2] if size.endswith('.0') else size
                    except Exception as e:
                        pass
                else:
                    size = parsed_size
            sizes.append(size)

        ori_sizes, parsed_sizes, sizes = size_sorted(ori_sizes.split(';'), parsed_sizes, sizes, category)

    return ori_sizes, parsed_sizes, sizes



