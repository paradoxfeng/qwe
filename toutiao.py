import requests
from urllib import parse
import json
from requests import RequestException
import re
from json.decoder import JSONDecodeError
import time
import pymongo
from config import *




class Toutiao(object):
    def __init__(self,MONGO_URI,MONGO_DB,MONGO_TABLE):


        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.MONGO_TABLE = MONGO_TABLE



    def get_index_page(self,offset):
        data = {
            'offset': offset,
            'format': 'json',
            'keyword': '篮球',
            'autoload': 'true',
            'count': 20,
            'cur_tab': 3,
            'from': 'gallery'
        }
        index_url = 'https://www.toutiao.com/search_content/?'+parse.urlencode(data)
        html = requests.get(index_url).text

        return html

    def parse_index_page(self,html):
        preview = json.loads(html)
        if  'data' in preview.keys():
            for item in preview.get('data'):
                url=item.get('article_url')
                if url.find('toutiao')>-1:
                    print(url)
                    yield url




    def parse_detail_page(self,url):
        try:
            time.sleep(3)
            headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
            response = requests.get(url,headers=headers)

        except RequestException:

            print('请求详情页出错')
            return None
        text = response.text

        title = re.search('title: \'(.*?)\'', text, re.S).group(1)
        pattern = re.compile('gallery: JSON.parse\((.*?)\)', re.S)
        results = re.search(pattern, text)
        results = results.group(1)
        try:
            dict = json.loads(results)
        except JSONDecodeError:
            return None
        # dict = dict.replace('\\','')
        dict = json.loads(dict)
        if 'sub_images' in dict.keys():
            sub_images = dict.get('sub_images')
            images = [item.get('url') for item in sub_images]
            return {
                'title': title,
                'images': images,
                'url': url
            }


    def save_to_mongo(self,text):
        if self.db[self.MONGO_TABLE].insert(text):
            print('存储成功',text)
            return True
        else:
            return False



    def start(self):
        for x in range(10):
            html = self.get_index_page(20*x)
            urls = self.parse_index_page(html)
            for url in urls:
                text = self.parse_detail_page(url)
                self.save_to_mongo(text)


toutiao = Toutiao(MONGO_URI,MONGO_DB,MONGO_TABLE)
toutiao.start()