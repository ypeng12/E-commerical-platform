import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import re
import requests
import json
# Extract text from hxs node, by xpath query and idx (th) result


def extract_text(hxs, xpaths, idx=0):

    if isinstance(xpaths, list) == False:
        xpaths = [xpaths]

    for xpath in xpaths:

        # exec query
        els = hxs.xpath(xpath)

        if len(els) > idx:
            # check if xpath query on attribute of node
            # //a/@href
            end = xpath.split('/')[-1]
            if len(end) > 0 and end[0] == '@':
                return els[idx].extract().strip()
            else:
                # get all text of nodes in side els[idx]
                return '  '.join(els[idx].xpath('.//text()').extract()).strip()
    return ''


def getwebcontent(url, data=None, cookies=None, headers=None):
    if data:
        data = urllib.parse.urlencode(data)
    if not headers:
        user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0'
        headers = {'User-Agent': user_agent}
    if cookies:
        headers['Cookies'] = "; ".join(
            [str(x) + "=" + str(y) for x, y in list(cookies.items())])

    req = urllib.request.Request(url, headers=headers, data=data)
    response = urllib.request.urlopen(req)
    return response.read()


def getwebcontent2(url, data=None, cookies=None, headers=None):
    if type(data) is dict:
        data = urllib.parse.urlencode(data)
    if not headers:
        user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0'
        headers = {'User-Agent': user_agent}
    if cookies:
        if type(cookies) is dict:
            headers['Cookie'] = "; ".join(
                [str(x) + "=" + str(y) for x, y in list(cookies.items())])
        else:
            headers['Cookie'] = cookies

    req = urllib.request.Request(url, headers=headers, data=data)
    response = urllib.request.urlopen(req)
    return response.read(), response.info().get('Set-Cookie')


def getwebcontent3(url, data=None, cookies=None, headers=None):
    if data:
        data = urllib.parse.urlencode(data)
    if not headers:
        user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0'
        headers = {'User-Agent': user_agent}
    if cookies:
        headers['Cookies'] = "; ".join(
            [str(x) + "=" + str(y) for x, y in list(cookies.items())])

    req = urllib.request.Request(url, headers=headers, data=data)
    response = urllib.request.urlopen(req)
    return response.info()


def get_json_data(url, data=None, cookies=None, headers=None):
    if type(data) is dict:
        data = urllib.parse.urlencode(data)
    if not headers:
        user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0'
        headers = {'User-Agent': user_agent}
    if cookies:
        if type(cookies) is dict:
            headers['Cookie'] = "; ".join([str(x) + "=" + str(y) for x, y in list(cookies.items())])
        else:
            headers['Cookie'] = cookies

    req = urllib.request.Request(url, headers=headers, data=data)
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())

    return data


def get_redirect_url(url, headers=None):
    if not headers:
        user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0'
        headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    return response.url


def extract_text_re(pattern, text, group=1):
    match = re.search(pattern, text)

    if match != None:
        return match.group(group)
    else:
        return ''


def degzip(data):
    try:
        from io import StringIO
        from gzip import GzipFile
        data2 = GzipFile('', 'r', 0, StringIO(data)).read()
        data = data2
    except:
        # print "decompress error %s" % err
        pass
    return data

def currency_parser(cur_str):
    # Remove any non-numerical characters
    # except for ',' '.' or '-' (e.g. EUR)
    cur_str = re.sub("[^-0-9.,]", '', cur_str)
    # Remove any 000s separators (either , or .)
    cur_str = re.sub("[.,]", '', cur_str[:-3]) + cur_str[-3:]

    if '.' in list(cur_str[-3:]):
        price = float(cur_str)
    elif ',' in list(cur_str[-3:]):
        price = float(cur_str.replace(',', '.'))
    else:
        price = float(cur_str)

    return round(price, 2)
