# coding: utf-8
from .cfg import *

'''
size convert
'''
# cn female size convert
F_CN_CONVERT = {
    'CN220/87': '34',
    'CN220/88': '34.5',
    'CN225/88': '35',
    'CNCN225/89': '35.5',
    'CN230/90': '36',
    'CN230/91': '36.5',
    'CN235/91': '37',
    'CN235/92': '37.5',
    'CN240/93': '38',
    'CN240/94': '38.5',
    'CN245/94': '39',
    'CN245/95': '39.5',
    'CN250/95': '40',
    'CN250/96': '40.5',
    'CN255/97': '41',
    'CN255/98': '41.5',
    'CN260/98': '42',
    'CN260/99': '42.5'
}

# cn male size convert
M_CN_CONVERT = {
    'CN235/91': '37',
    'CN235/92': '37.5',
    'CN240/93': '38',
    'CN240/94': '38.5',
    'CN245/94': '39',
    'CN245/95': '39.5',
    'CN250/96': '40',
    'CN250/97': '40.5',
    'CN255/97': '41',
    'CN255/98': '41.5',
    'CN260/99': '42',
    'CN260/100': '42.5',
    'CN265/100': '43',
    'CN265/101': '43.5',
    'CN270/102': '44',
    'CN270/103': '44.5',
    'CN275/103': '45',
    'CN275/104': '45.5',
    'CN280/105': '46',
    'CN280/106': '46.5',
    'CN285/106': '47',
    'CN285/107': '47.5',
    'CN290/108': '48',
    'CN290/109': '48.5',
}

# cy convert
CY_CONVERT = {
    '0C': 'IT15',
    '1C': 'IT16',
    '2C': 'IT17',
    '3C': 'IT18',
    '4C': 'IT19',
    '5C': 'IT20',
    '5.5C': 'IT21',
    '6C': 'IT22',
    '7C': 'IT23',
    '8C': 'IT24',
    '9C': 'IT25',
    '9.5C': 'IT26',
    '10C': 'IT27',
    '11C': 'IT28',
    '12C': 'IT29',
    '13C': 'IT30',
    '13.5C': 'IT31',
    '1Y': 'IT32',
    '2Y': 'IT33',
    '2.5Y': 'IT34',
    '3Y': 'IT34',
    '3.5Y': 'IT35',
    '4Y': 'IT36',
    '5Y': 'IT37',
    '6Y': 'IT38',
    '7Y': 'IT39',
    '8Y': 'IT40',
    '9Y': 'IT41',
    '10Y': 'IT42',
}

size_type = {
    'USA':'US',
    'UK':'UK',
    'CHINA':'CN',
    'DT':'DT',
    'UX':'UX',
    'IT/EU':'IT',
    'ITALY':'IT',
    'ITALIAN':'IT',
    'IT/FR':'IT',
    'ITALY/FRANCE':'IT',
    'ITALIAN SIZING':'IT',
    'KOREA':'KR',
    'KOREAN':'KR',
    'EUROPE':'EU',
    'EUR':'EU',
    'JAPAN':'JP',
    'FRANCE':'FR',
    'GERMANY':'DE',
    'BRAZIL':'BR',
    'SPAIN':'SP',
    'DENMARK':'DM',
    'RUSSIA':'RU',
    'AUSTRALIA':'AU',
    'AUSTRALISCH':'AU',
    'JEANS SIZE (IN)':'JEAN',
    'ITALIAN EU SIZING':'EU',
    'INCHES':'IN',
    'CENTEMETERS':'CM',
    'STANDARD SIZE':'ST',
    'WAIST':'WA',
    'CHEST':'CH',
    'NUM':'NU',
    'JEANS (WAIST)':'WA',
    '欧洲尺码':'EU',
    '美国尺码':'US',
    '英国尺码':'UK',
    '意大利尺码':'IT',
    '意大利/法国尺码':'IT',
    '意大利/欧洲尺码':'IT',
    '法国尺码':'FR',
    '澳大利亚尺码':'AU',
}

INFANT_US_SHOES_CONVERT = {
    '0.5':'IT16',
    '1':'IT16',
    '1.5':'IT17',
    '2':'IT17',
    '2.5':'IT18',
    '3':'IT18',
    '3.5':'IT19',
    '4':'IT19',
    '4.5':'IT20',
    '5':'IT20',
    '5.5':'IT21',
    '6':'IT22',
    '6.5':'IT22',
    '7':'IT23',
    '7.5':'IT23',
    '8':'IT24',
    '8.5':'IT25',
    '9':'IT25',
    '9.5':'IT26',
    '10':'IT27',
}

CHILD_US_SHOES_CONVERT = {
    '10.5':'IT27',
    '11':'IT28',
    '11.5':'IT29',
    '12':'IT30',
    '12.5':'IT30',
    '13':'IT31',
    '13.5':'IT31',
    '1':'IT32',
    '1.5':'IT33',
    '2':'IT33',
    '2.5':'IT34',
    '3':'IT34',
    '3.5':'IT35',
    '4':'IT36',
    '4.5':'IT36',
    '5':'IT37',
    '5.5':'IT37',
    '6':'IT38',
    '6.5':'IT38',
    '7':'IT39',
}

def toItSize(size, gender='f'):
    if '/' in size:
        size = size.split('/')[0].strip()
    if '(' in size:
        size = size.split('(')[0].strip()
    postfix = ''
    if ':' in size:
        parts = size.split(':')
        postfix = ':' + parts[1].lower()
        size = parts[0]

    try:
        size = size.upper().strip()
    except:
        pass

    if size in CY_CONVERT:
        return CY_CONVERT[size]

    if 'YRS' in size or 'YEAR' in size or size.endswith('Y') or 'TODDLER' in size or (size.endswith('T') and not size.endswith('IT')):
        size = size.split('-')[0].upper()
        size = 'ITY' + size.replace('.0', '').replace('YEARS', '').replace('YEAR', '').replace('YRS', '').replace('Y', '').replace('TODDLER', '').replace('T', '').strip()
        return size

    if 'MTH' in size or 'MONTH' in size or (size not in ['M','MEDIUM'] and size.endswith('M') and 'CM' not in size):
        size = size.split('-')[0].upper()
        size = 'ITM' + size.replace('.0', '').replace('MONTHS', '').replace('MONTH', '').replace('MTHS', '').replace('MTH', '').replace('M', '').strip()
        return size

    if gender in ['r','y','i']:
        size = INFANT_US_SHOES_CONVERT.get(size.replace('.0', ''),size)
    if gender in ['g','b','c']:
        size = CHILD_US_SHOES_CONVERT.get(size.replace('.0', ''),size)

    try:
        size = float(size.strip())
        if size < 20:
            size = 'US%s' % size
        else:
            size = "IT%s" % size
    except:
        # print 'Not float'
        pass

    if 'UX' in size:
        tmp = size[2:]
        if tmp in CY_CONVERT:
            size = CY_CONVERT[tmp]

    if 'IT' in size:
        size = 'IT' + size.replace('.0', '').replace('IT', '').strip()
        return size

    if size == 'M':
        if gender == 'm':
            return 'IT39.5;IT40;IT40.5;IT41'
        else:
            return 'IT37;IT37.5;IT38'

    if size == 'L':
        if gender == 'm':
            return 'IT41.5;IT42;IT42.5;IT43'
        else:
            return 'IT38.5;IT39;IT39.5'

    if size == 'XL':
        if gender == 'm':
            return 'IT43.5;IT44;IT44.5;IT45'
        else:
            return 'IT40;IT40.5;IT41;IT41.5;IT42'

    if size == 'XXL':
        if gender == 'm':
            return 'IT45.5;IT46;IT46.5;IT47'
        else:
            return ''

    if size == 'XXXL' or size == '3XL':
        if gender == 'm':
            return 'IT47.5;IT48;IT49'
        else:
            return ''

    if size == 'S':
        if gender == 'm':
            return 'IT37.5;IT38;IT38.5;IT39'
        else:
            return 'IT35.5;IT36;IT36.5'

    if size == 'XS':
        if gender == 'm':
            return 'IT36.5;IT36;IT37'
        else:
            return 'IT35.5;IT36;IT36.5'

    if size == '2XS':
        if gender == 'm':
            return 'IT35.5;IT35.5'
        else:
            return 'IT34.5;IT35'

    if 'MEDIUM' in size:
        if gender == 'm':
            return 'IT39.5;IT40;IT40.5;IT41'
        else:
            return 'IT37;IT37.5;IT38'

    if 'LARGE' in size:
        if gender == 'm':
            return 'IT41.5;IT42;IT42.5;IT43'
        else:
            return 'IT38.5;IT39;IT39.5'

    if 'SMALL' in size:
        if gender == 'm':
            return 'IT37.5;IT38;IT38.5;IT39'
        else:
            return 'IT35.5;IT36;IT36.5'

    if gender == 'm' and size in M_CN_CONVERT:
        return 'IT' + M_CN_CONVERT[size]
    elif gender == 'f' and size in F_CN_CONVERT:
        return 'IT' + F_CN_CONVERT[size]

    try:
        parts = size.split(':')

        try:
            c = parts[0][:2]
            s = float(parts[0][2:])
        except:
            try:
                c = parts[0][-2:]
                s = float(parts[0][0:-2])
            except:
                s = float(parts[0])
                if s < 30:
                    c = "US"
                else:
                    c = "IT"

        if len(parts) > 1:
            n = ':%s' % parts[1]
        else:
            n = ''
        result = size
        if 'UX' in c:
            if gender == 'm':
                result = 'IT%s%s' % (s + 33.5, n)
            else:
                result = 'IT%s%s' % (s + 30.5, n)
        elif 'US' in c:
            if gender == 'm':
                result = 'IT%s%s' % (s + 33, n)
            else:
                result = 'IT%s%s' % (s + 30, n)

        elif 'FR' in c:
            if gender == 'm':
                result = 'IT%s%s' % (s, n)
            else:
                result = 'IT%s%s' % (s - 1, n)
        elif 'UK' in c:
            if gender == 'm':
                result = 'IT%s%s' % (s + 34, n)
            else:
                result = 'IT%s%s' % (s + 33, n)
        elif 'JP' in c:
            if gender == 'm':
                result = 'IT%s%s' % (s + 15, n)
            else:
                result = 'IT%s%s' % (s + 13.5, n)
        elif 'KR' in c:
            if gender == 'm':
                result = 'IT%s%s' % (s / 10 + 14, n)
            else:
                result = 'IT%s%s' % (s / 10 + 13, n)
        elif 'CN' in c:
            if gender == 'm':
                result = 'IT%s%s' % (s + 14, n)
            else:
                result = 'IT%s%s' % (s + 13, n)
        elif 'EU' in c:
            result = 'IT%s%s' % (s, n)
        elif 'BZ' in c:
            result = 'IT%s%s' % (s + 2, n)
        elif 'BR' in c:
            if s > 30:
                result = 'IT%s%s' % (s + 2, n)
            else:
                if gender == 'm':
                    result = 'IT%s%s' % (s + 33, n)
                else:
                    result = 'IT%s%s' % (s + 34, n)
        return result.replace('.0', '')
    except Exception as ex:
        # print ex
        return size.replace('.0', '')


def clothToItSize(size, gender='f'):
    if '/' in size:
        size = size.split('/')[0].strip()
    if '(' in size:
        size = size.split('(')[0].strip()
    postfix = ''
    if ':' in size:
        parts = size.split(':')
        postfix = ':' + parts[1].lower()
        size = parts[0]

    try:
        size = size.upper().strip()
    except:
        pass

    if 'YRS' in size or 'YEAR' in size or size.endswith('Y') or 'TODDLER' in size or (size.endswith('T') and not size.endswith('IT')):
        size = size.split('-')[0].upper()
        size = 'ITY' + size.replace('.0', '').replace('YEARS', '').replace('YEAR', '').replace('YRS', '').replace('Y', '').replace('TODDLER', '').replace('T', '').strip()
        return size

    if 'MTH' in size or 'MONTH' in size or (size not in ['M','MEDIUM'] and size.endswith('M') and 'CM' not in size):
        size = size.split('-')[0].upper()
        size = 'ITM' + size.replace('.0', '').replace('MONTHS', '').replace('MONTH', '').replace('MTHS', '').replace('MTH', '').replace('M', '').strip()
        return size

    if gender == 'm':
        size = size.replace('\n', '').replace('.0', '').upper()

        try:
            size = float(size.strip())
            if size < 18:
                size = 'US%s' % size
            elif size < 20:
                size = 'JP%s' % size
            elif size > 60:
                size = 'KR%s' % size
            else:
                size = "IT%s" % size
        except:
            # print 'Not float'
            pass

        if 'NU' in size:
            size = 'NUM' + size.replace('NUM','').replace('NU','').strip()

        if 'IT' in size:
            size = 'IT' + size.replace('.0', '').replace('IT', '').strip()
            return size

        if size in ['XXXS', 'XXX-SMALL', 'XXXSML', 'XXX SMALL'] or '155/76' in size:
            return 'IT40'
        elif size in ['2XS', 'XXS', 'XX-SMALL', 'XXSML', 'XX SMALL'] or '160/80' in size:
            return 'IT42'
        elif size in ['P', 'PETITE', 'XS', 'X SMALL', 'X-SMALL', 'XSML', 'XSML', 'X SMALL', 'EXTRASMALL', 'EXTRA SMALL','NUM0'] or '165/84' in size:
            return 'IT44'
        elif size in ['S', 'SMALL', 'SML', 'SM', 'I', 'NUM1'] or '170/88' in size:
            return 'IT46'
        elif size in ['M', 'MEDIUM', 'MED', 'MD', 'II', 'NUM2'] or '175/92' in size:
            return 'IT48'
        elif size in ['L', 'LARGE', 'LRG', 'LG', 'III', 'NUM3'] or '180/96' in size:
            return 'IT50'
        elif size in ['XL', 'X-LARGE', 'XLRG', 'X LARGE', 'EXTRALARGE', 'EXTRA LARGE', 'XLARGE', 'IV', 'NUM4'] or '185/100' in size:
            return 'IT52'
        elif size in ['2XL','XXL', 'XX-LARGE', 'XXLRG', 'XX LARGE', 'XXLARGE', 'V', 'NUM5'] or '190/104' in size:
            return 'IT54'
        elif size in ['3XL', 'XXXL', 'XXX-LARGE', 'XXXLRG', 'XXX LARGE', 'XXXLARGE', 'VI', 'NUM6'] or '195/108' in size:
            return 'IT56'
        elif size in ['4XL','XXXXL', 'XXXX-LARGE', 'XXXXLRG', 'XXXX LARGE', '4XL', '4X LARGE', 'XXXXLARGE', '4XLARGE', 'VII', 'NUM7'] or '200/112' in size:
            return 'IT58'
        elif size in ['5XL','XXXXXL', 'XXXXX-LARGE', 'XXXXXLRG', 'XXXXX LARGE', '5XL', '5X LARGE', 'XXXXXLARGE', '5XLARGE']:
            return 'IT'
        elif size in ['6XL','XXXXXXL', 'XXXXXX-LARGE', 'XXXXXXLRG', 'XXXXXX LARGE', '6XL', '6X LARGE', 'XXXXXXLARGE', '6XLARGE']:
            return 'IT'
        if size in ['4XS','XXXXS', 'XXX-SMALL', 'XXXXSML', 'XXXX SMALL']:
            return 'IT'
        if size in ['5XS','XXXXXS', 'XXXXX-SMALL', 'XXXXXSML', 'XXXXX SMALL']:
            return 'IT'
        if size in ['6XS','XXXXXXS', 'XXXXXX-SMALL', 'XXXXXXSML', 'XXXXXX SMALL']:
            return 'IT'
        if '00' in size:
            return 'IT40'

        try:
            parts = size.split(':')

            try:
                c = parts[0][:2]
                s = float(parts[0][2:])
            except:
                try:
                    c = parts[0][-2:]
                    s = float(parts[0][0:-2])
                except:
                    s = float(parts[0])
                    if s < 10:
                        c = "JP"
                    elif s > 60:
                        c = 'KR'
                    else:
                        c = "IT"

            if len(parts) > 1:
                n = ':%s' % parts[1]
            else:
                n = ''

            result = size
            if 'CHEST' in c:
                result = 'IT%s%s' % (s + 10, n)
            elif 'WA' in c:
                result = 'IT%s%s' % (s + 16, n)
            elif 'UK' in c or 'USA' in c:
                result = 'IT%s%s' % (s + 32, n)
            elif 'US' in c or 'USA' in c:
                result = 'IT%s%s' % (s + 16, n)
            elif 'DT' in c:
                result = 'IT%s%s' % (s, n)
            elif 'FRANCE' in c or 'FR' in c:
                result = 'IT%s%s' % (s, n)
            elif 'JAPAN' in c or 'JP' in c:
                if s < 20:
                    result = 'IT%s%s' % (s * 2 + 42, n)
                else:
                    result = 'IT%s%s' % (s + 10, n)
            elif 'EU' in c:
                result = 'IT%s%s' % (s, n)
            elif 'DE' in c:
                result = 'IT%s%s' % (s, n)
            elif 'GERMANY' in c or 'GM' in c:
                result = 'IT%s%s' % (s, n)
            elif 'BRAZIL' in c or 'BZ' in c:
                result = 'IT%s%s' % (s + 2, n)
            elif 'RUSSIA' in c or 'RU' in c:
                result = 'IT%s%s' % (s, n)
            elif 'AUSTRALIA' in c or 'AU' in c:
                result = 'IT%s%s' % (s + 16, n)
            elif 'JEAN' in c:
                result = 'IT%s%s' % (s + 11, n)

            elif 'BR' in c:
                result = 'IT%s%s' % (s - 2, n)

            return result.replace('.0', '')
        except Exception as ex:
            # print ex
            return size.replace('.0', '')
    else:
        size = size.replace('\n', '').replace('.0', '').upper()

        try:
            size = float(size.strip())
            if size < 18:
                size = 'US%s' % size
            elif size < 34:
                size = 'WA%s' % size
            else:
                size = "IT%s" % size
        except:
            # print 'Not float'
            pass

        if 'NU' in size:
            size = 'NUM' + size.replace('NUM','').replace('NU','').strip()

        if 'IT' in size:
            size = 'IT' + size.replace('.0', '').replace('IT', '').strip()
            return size

        if size in ['3XS', 'XXXS', 'XXX-SMALL', 'XXXSML', 'XXX SMALL'] or '145/73' in size:
            return 'IT36'
        elif size in ['2XS', 'XXS', 'XX-SMALL', 'XXSML', 'XX SMALL', 'XP'] or '150/76' in size:
            return 'IT38'
        elif size in ['P', 'PETITE', 'XS', 'X-SMALL', 'XSML', 'X SMALL', 'EXTRASMALL', 'EXTRA SMALL', 'XS/S', 'NUM0'] or '155/80' in size:
            return 'IT40'
        elif size in ['S', 'SMALL', 'SM','SML', 'S/M', 'I', 'NUM1'] or '160/84' in size:
            return 'IT42'
        elif size in ['M', 'MEDIUM', 'MED', 'M/L', 'II', 'NUM2'] or '165/88' in size:
            return 'IT44'
        elif size in ['L', 'LARGE', 'LRG', "LG", 'III', 'NUM3'] or '170/92' in size:
            return 'IT46'
        elif size in ['XL', 'X-LARGE', 'XLRG', 'X LARGE', 'EXTRALARGE', 'EXTRA LARGE', 'XLARGE', 'IV', 'NUM4'] or '175/96' in size:
            return 'IT48'
        elif size in ['2XL','XXL', 'XX-LARGE', 'XXLRG', 'XX LARGE', 'XXLARGE', 'V', 'NUM5'] or '180/100' in size:
            return 'IT50'
        elif size in ['3XL', 'XXXL', 'XXX-LARGE', 'XXXLRG', 'XXX LARGE', 'XXXLARGE', 'VI', 'NUM6'] or '185/104' in size:
            return 'IT52'
        elif size in ['4XL','XXXXL', 'XXXX-LARGE', 'XXXXLRG', 'XXXX LARGE', '4XL', '4X LARGE', 'XXXXLARGE', '4XLARGE'] or '200/112' in size:
            return 'IT58'
        elif size in ['5XL','XXXXXL', 'XXXXX-LARGE', 'XXXXXLRG', 'XXXXX LARGE', '5XL', '5X LARGE', 'XXXXXLARGE', '5XLARGE']:
            return 'IT'
        elif size in ['6XL','XXXXXXL', 'XXXXXX-LARGE', 'XXXXXXLRG', 'XXXXXX LARGE', '6XL', '6X LARGE', 'XXXXXXLARGE', '6XLARGE']:
            return 'IT'
        if size in ['4XS','XXXXS', 'XXX-SMALL', 'XXXXSML', 'XXXX SMALL']:
            return 'IT'
        if size in ['5XS','XXXXXS', 'XXXXX-SMALL', 'XXXXXSML', 'XXXXX SMALL']:
            return 'IT'
        if size in ['6XS','XXXXXXS', 'XXXXXX-SMALL', 'XXXXXXSML', 'XXXXXX SMALL']:
            return 'IT'
        if '00' in size or 'US00' in size:
            return 'IT34'

        try:
            parts = size.split(':')

            try:
                c = parts[0][:2]
                s = float(parts[0][2:])
            except:
                try:
                    c = parts[0][-2:]
                    s = float(parts[0][0:-2])
                except:
                    s = float(parts[0])
                    if s < 30:
                        c = "US"
                    else:
                        c = "IT"

            if len(parts) > 1:
                n = ':%s' % parts[1]
            else:
                n = ''

            result = size
            if 'USA' in c or 'US' in c:
                result = 'IT%s%s' % (s + 36, n)
            elif 'WA' in c:
                result = 'IT%s%s' % (s + 12, n)
            elif 'DT' in c:
                result = 'IT%s%s' % (s + 4, n)
            elif 'FRANCE' in c or 'FR' in c:
                result = 'IT%s%s' % (s + 4, n)
            elif 'UK' in c:
                result = 'IT%s%s' % (s + 32, n)
            elif 'JAPAN' in c or 'JP' in c:
                result = 'IT%s%s' % (s + 31, n)
            elif 'EU' in c:
                result = 'IT%s%s' % (s, n)
            elif 'DE' in c:
                result = 'IT%s%s' % (s + 6, n)
            elif 'GERMANY' in c or 'GM' in c:
                result = 'IT%s%s' % (s + 4, n)
            elif 'BRAZIL' in c or 'BZ' in c:
                result = 'IT%s%s' % (s + 1, n)
            elif 'SPAIN' in c or 'SP' in c:
                result = 'IT%s%s' % (s + 6, n)
            elif 'DENMARK' in c or 'DM' in c:
                result = 'IT%s%s' % (s + 6, n)
            elif 'RUSSIA' in c or 'RU' in c:
                result = 'IT%s%s' % (s - 2, n)
            elif 'AUSTRALIA' in c or 'AU' in c:
                result = 'IT%s%s' % (s + 32, n)
            elif 'JEAN' in c:
                result = 'IT%s%s' % (s + 11, n)

            elif 'BR' in c:
                if s > 30:
                    result = 'IT%s%s' % (s + 2, n)
                else:
                    result = 'IT%s%s' % (s + 33, n)

            return result.replace('.0', '')
        except Exception as ex:
            # print ex
            return size.replace('.0', '')
