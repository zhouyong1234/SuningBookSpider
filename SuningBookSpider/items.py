# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy


class SuningbookspiderItem(scrapy.Item):
    _id = scrapy.Field()
    # 大分类
    b_tag = scrapy.Field()
    # 中分类
    m_tag = scrapy.Field()
    # 小分类
    s_tag = scrapy.Field()
    # 小分类地址
    s_tag_href = scrapy.Field()
    # 图片地址
    img = scrapy.Field()
    # 标题
    title = scrapy.Field()
    # 书店
    shop = scrapy.Field()
    # 详情页url
    href = scrapy.Field()
    # 详情信息
    book_detail = scrapy.Field()
    # 价格
    netprice = scrapy.Field()
