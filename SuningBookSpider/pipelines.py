# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient


class SuningbookspiderPipeline(object):
    def open_spider(self, spider):
        client = MongoClient()
        self.collection = client['Suning']['books']

    def process_item(self, item, spider):
        print(item['href'])
        try:
            self.collection.insert_one(item)
        except Exception as e:
            print('此数据已存在')
            return item
        return item

    def close_spider(self, spider):
        self.collection.close()
