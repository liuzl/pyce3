# pyce3: Multilingual Web Page Content Extractor for Python3

## Introduction

`pyce3` is python3 ggpackage for multilingual web page content extraction. It is used to extract the content of article type web pages, such as news, blog posts, etc.

## Usage

```python
import pyce3
import requests

url = "http://caijing.chinadaily.com.cn/a/201911/21/WS5dd62455a31099ab995ed438.html"
html = requests.get(url).content
encoding, time, title, text, next_link = pyce3.parse(url, html)
print("编码："+encoding)
print('='*10)
print("标题："+title)
print("时间："+time)
print('='*10)
print("内容："+text)
print("NextPageLink: ", next_link)
```
