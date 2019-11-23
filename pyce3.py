#coding=utf-8
import re
import chardet
import hashlib
import dateutil.parser as dtparser
import lxml
import lxml.html
import lxml.etree
try:
    import urlparse
except:
    import urllib.parse as urlparse

try:
    import htmlentitydefs
except:
    import html.entities as htmlentitydefs

url_validation_regex = re.compile(r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def is_valid_url(url):
    return url_validation_regex.match(url) is not None

##
# http://effbot.org/zone/re-sub.htm#unescape-html
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

RE_MULTI_NEWLINE = r'\n+'

RE_IGNORE_BLOCK = {
'doctype' : r'(?is)<!DOCTYPE.*?>', # html doctype
'comment' : r'(?is)<!--.*?-->', # html comment
'script' : r'(?is)<script.*?>.*?</script>', # javascript
'style' : r'(?is)<style.*?>.*?</style>', # css
#'special' : r'&.{2,5};|&#.{2,5};',
}

RE_NEWLINE_BLOCK = {
'div' : r'(?is)<div.*?>',
'p' : r'(?is)<p.*?>',
'br' : r'(?is)<br.*?>',
'hr' : r'(?is)<hr.*?>',
'h' : r'(?is)<h\d+.*?>',
'li' : r'(?is)<li\d+.*?>',
}

RE_IMG = r'(?is)(<img.*?>)'

RE_IMG_SRC = r'(?is)<img.+?src=(\'|")(.+?)(\'|").*?>'

RE_TAG = r'(?is)<.*?>'

RE_TITLE = r'(?is)<title.*?>(.+?)</title>'
RE_H = r'(?is)<h\d+.*?>(.*?)</h\d+>'

RE_DATETIME = r'(((\d{4}年){0,1}\d{1,2}月\d{1,2}日|(\d{4}-){0,1}\d{1,2}-\d{1,2})\s*(\d{1,2}:\d{1,2}(:\d{1,2}){0,1}){0,1})'

## parameters
BLOCKS_WIDTH = 3
THRESHOLD = 100

## 导航条特征
NAV_SPLITERS = [
    r'\|',
    r'┊',
    r'-',
    r'\s+',
]

def get_unicode_str(html):
    enc = chardet.detect(html)['encoding']
    return enc, html.decode(enc, 'ignore')

def strtotime(t):
    if t == '': return ''
    RE_DT_REPLACE = r'年|月'
    t = re.sub(RE_DT_REPLACE,'-',t).replace(u'日',' ')
    try:
        s = str(dtparser.parse(t, fuzzy=True))
    except:
        s = ''
    return s

def is_useful_line(line):
    for sep in NAV_SPLITERS:
        items = re.split(sep, line)
        if len(items) >= 5:
            return False
    return True

def get_raw_info(html):
    title = ''.join(re.findall(RE_TITLE, html))# + re.findall(RE_H, html)
    html = re.sub(r"(?is)</a><a",'</a> <a',html)
    h = re.findall(RE_H, html)
    for ht in h:
        ht = ht.strip()
        if ht == '': continue
        if title.startswith(ht):
            title = ht
            break
    for k,v in RE_IGNORE_BLOCK.items():
        html = re.sub(v, '', html)
    for k,v in RE_NEWLINE_BLOCK.items():
        html = re.sub(v, '\n', html)
    html = re.sub(RE_MULTI_NEWLINE, '\n', html)
    
    return unescape(title), unescape(html)

def get_main_content(html):
    html_lines_len = [len(x.strip()) for x in html.split('\n')]

    # 保存图片信息
    images = {}
    for img in re.findall(RE_IMG, html):
        md5 = hashlib.md5(img.encode('utf-8')).hexdigest()[:16]
        html = html.replace(img, md5)
        r = re.findall(RE_IMG_SRC, img)
        if len(r) == 1: src = r[0][1]
        else: src = ''
        images[md5] = "<img src='%s'>" % src#img

    # 去除所有的html标签
    text = re.sub(RE_TAG, '', html)

    # 抽取发表时间
    time = ''
    t = re.findall(RE_DATETIME, text)
    if len(t) > 0:
        time = t[0][0]

    lines = [x.strip() if is_useful_line(x) else '' for x in text.split('\n')]
    index_dist = []
    size = len(lines)
    for i in range(size - BLOCKS_WIDTH + 1):
        char_num = 0
        for j in range(i, i + BLOCKS_WIDTH):
            strip = re.sub(r'\s+', '', lines[j])
            char_num += len(strip)
        index_dist.append(char_num)
    main_text = ''
    fstart = -1
    start = -1
    end = -1
    flag_s = False
    flag_e = False
    first_match = True
    for i in range(len(index_dist) - 1):
        if first_match and not flag_s:
            if index_dist[i] > THRESHOLD / 2:
                if index_dist[i+1] != 0 or index_dist[i+2] != 0:
                    first_match = False
                    flag_s = True
                    start = i
                    fstart = i
                    continue
        if index_dist[i] > THRESHOLD and not flag_s:
            if index_dist[i+1] != 0 or index_dist[i+2] != 0 or index_dist[i+3] != 0:
                flag_s = True
                start = i
                continue
        if flag_s:
            if index_dist[i] == 0 or index_dist[i+1] == 0:
                end = i
                flag_e = True
        tmp = ''
        if flag_e:
            for ii in range(start, end+1):
                if (len(lines[ii]) < 1): continue
                tmp += lines[ii] + '\n'
            main_text += tmp
            flag_s = flag_e = False

    for md5,img in images.items():
        main_text = main_text.replace(md5, img)
    return strtotime(time), main_text

def get_next_page_link(url, doc):
    nodes = doc.xpath(u"//a[text() = '下一页'] | //a[text() = '>'] | //a[text() = '下页']")
    if len(nodes) > 0:
        if "href" in nodes[0].attrib:
            href = nodes[0].attrib["href"]
            link = urlparse.urljoin(url, href).strip()
            if link:
                return link
    return None

def parse(url, html):
    encoding, html = get_unicode_str(html)
    if encoding == '': return '', '', '', '', ''
    try:
        doc = lxml.html.document_fromstring(html)
        doc.make_links_absolute(url)
        html = lxml.etree.tounicode(doc, method='html')
    except:
        return '', '', '', '', ''
    title, text = get_raw_info(html)
    
    time, text = get_main_content(text)

    link = get_next_page_link(url, doc)
    return encoding, time, title, text, link

if __name__ == "__main__":
    #url = "http://caijing.chinadaily.com.cn/a/201911/21/WS5dd62455a31099ab995ed438.html"
    import sys
    if len(sys.argv) < 2:
        print("Usage: %s <url>" % sys.argv[0])
        sys.exit(1)
    url = sys.argv[1]
    import requests
    html = requests.get(url).content
    encoding, time, title, text, next_link = parse(url, html)
    print("编码："+encoding)
    print('='*10)
    print("标题："+title)
    print("时间："+time)
    print('='*10)
    print("内容："+text)
    print("NextPageLink: ", next_link)
