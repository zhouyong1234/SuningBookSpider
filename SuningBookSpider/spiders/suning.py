# -*- coding: utf-8 -*-
import re
import scrapy
from copy import deepcopy
from SuningBookSpider.items import SuningbookspiderItem
from scrapy_redis.spiders import RedisSpider


class SuningSpider(RedisSpider):
    name = 'suning'
    allowed_domains = ['suning.com']
    redis_key = 'suning:start_urls'
    # start_urls = ['http://book.suning.com/']

    def parse(self, response):
        # 提取大标题分类
        item_div_list = response.xpath('//div[@class="menu-list"]/div[@class="menu-item"]')
        sub_div_list = response.xpath('//div[@class="menu-list"]/div[@class="menu-sub"]/div[@class="submenu-left"]')
        for div in item_div_list:
            item = SuningbookspiderItem()
            item['b_tag'] = div.xpath('.//h3/a/text()').extract_first()
            # 提取中标题分类
            sub_div = sub_div_list[item_div_list.index(div)]
            m_tags = sub_div.xpath('./p')
            # 包含中标签
            if len(m_tags):
                for m_tag in m_tags:
                    item['m_tag'] = m_tag.xpath('./a/text()').extract_first()
                    # 提取小标签分类
                    s_tags = m_tag.xpath('./following-sibling::ul[1]/li/a/text()').extract()
                    s_tag_hrefs = m_tag.xpath('./following-sibling::ul[1]/li/a/@href').extract()
                    for s_tag in s_tags:
                        item['s_tag'] = s_tag
                        item['s_tag_href'] = s_tag_hrefs[s_tags.index(s_tag)]
                        yield scrapy.Request(item['s_tag_href'], callback=self.parse_book_list, meta={'item': deepcopy(item)})
                        # 请求下半页的数据
                        lower_page_url = ''
                        re_num = re.findall(r'\d+', item['s_tag_href'])
                        # 部分小标题url规律不一样（CET-4 CET-6 雅思 托福 CRE）
                        if len(re_num) >= 3:
                            ci = re_num[1]
                            cp = re_num[2]
                            lower_page_url = 'https://list.suning.com/emall/showProductList.do?ci={type}&pg=03&cp={page}&il=0&iy=-1&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAAB&id=IDENTIFYING&paging=1&sub=0'.format(page=cp, type=ci)
                        elif len(re.findall(r'keyword=(.*)', item['s_tag_href'])):
                            key_word = re.findall(r'keyword=(.*)', item['s_tag_href'])[0]
                            lower_page_url = 'https://search.suning.com/emall/searchProductList.do?keyword={}&ci=0&pg=01&cp=0&il=0&st=0&iy=0&n=1&ch=4&sesab=BCAABAAB&id=IDENTIFYING&paging=1&sub=0'.format(key_word)
                        yield response.follow(lower_page_url, callback=self.parse_book_list, meta={'item': deepcopy(item)})
            else:
                # 不包含中标签
                div_list = response.xpath('//div[@class="menu-list"]/div[contains(@class, "menu-sub") and position()>last()-3]')
                s_tags = div_list[item_div_list.index(div) - 7].xpath('.//ul/li/a/text()').extract()
                s_tag_hrefs = div_list[item_div_list.index(div) - 7].xpath('.//ul/li/a/@href').extract()
                for s_tag in s_tags:
                    item['s_tag'] = s_tag
                    item['s_tag_href'] = s_tag_hrefs[s_tags.index(s_tag)]
                    yield response.follow(item['s_tag_href'], callback=self.parse_book_list, meta={'item': deepcopy(item)})
                    # 请求下半页的数据
                    re_num = re.findall(r'\d+', item['s_tag_href'])
                    if re_num[2]:
                        ci = re_num[1]
                        cp = re_num[2]
                        lower_page_url = 'https://list.suning.com/emall/showProductList.do?ci={type}&pg=03&cp={page}&il=0&iy=-1&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAAB&id=IDENTIFYING&paging=1&sub=0'.format(page=cp, type=ci)
                        yield response.follow(lower_page_url, callback=self.parse_book_list, meta={'item': deepcopy(item)})

    def parse_book_list(self, response):  # 解析书城列表页
        item = response.meta['item']
        li_list = response.xpath('//li[contains(@class, "product      book")]')
        for li in li_list:
            item['img'] = li.xpath('.//img[@class="search-loading"]/@src2').extract_first()
            item['title'] = ''.join([i.strip() for i in li.xpath('.//p[@class="sell-point"]/a[@class="sellPoint"]/text()').extract()])
            item['shop'] = li.xpath('.//a[@sa-data="{eletp:shop}"]/text()').extract_first()
            item['href'] = li.xpath('.//div[@class="img-block"]/a/@href').extract_first()
            # 发送详情页请求
            yield response.follow(item['href'], callback=self.parse_detail, meta={'item': deepcopy(item)})

        # 请求下一页
        re_num = re.findall(r'\d+', item['s_tag_href'])
        if re_num[2]:
            temp_url_1 = 'https://list.suning.com/emall/showProductList.do?ci={}&pg=03&cp={}&il=0&iy=0&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAAB&id=IDENTIFYING&cc=023'
            temp_url_2 = 'https://list.suning.com/emall/showProductList.do?ci={}&pg=03&cp={}&il=0&iy=0&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAAB&id=IDENTIFYING&paging=1&sub=0'
            ci = re_num[1]
            current_page = int(re.findall(r'currentPage = "(.*?)"', response.body.decode(), re.S)[0])
            tatol_pages = int(re.findall(r'pageNumbers = "(.*?)"', response.body.decode(), re.S)[0])
            if current_page < tatol_pages - 1:
                # 构造前半页
                next_page = current_page + 1
                next_url_1 = temp_url_1.format(ci, next_page)
                yield response.follow(next_url_1, callback=self.parse_book_list, meta={'item': item})
                # 构造后半页
                next_url_2 = temp_url_2.format(ci, next_page)
                yield response.follow(next_url_2, callback=self.parse_book_list, meta={'item': item})
        # 特殊url处理
        elif len(re.findall(r'keyword=(.*?)]&', item['s_tag_href'])):
            temp_url_1 = 'https://search.suning.com/emall/searchProductList.do?keyword={}&ci=0&pg=01&cp={}&il=0&st=0&iy=0&adNumber=0&n=1&ch=4&sesab=BCAABAAB&id=IDENTIFYING&cc=023'
            temp_url_2 = 'https://search.suning.com/emall/searchProductList.do?keyword={}&ci=0&pg=01&cp={}&il=0&st=0&iy=0&adNumber=0&n=1&ch=4&sesab=BCAABAAB&id=IDENTIFYING&paging=1&sub=0'
            key_word = re.findall(r'keyword=(.*?)&', item['s_tag_href'])[0]
            current_page = int(re.findall(r'currentPage = "(.*?)"', response.body.decode(), re.S)[0])
            tatol_pages = int(re.findall(r'pageNumbers = "(.*?)"', response.body.decode(), re.S)[0])
            if current_page < tatol_pages - 1:
                # 构造前半页
                next_page = current_page + 1
                next_url_1 = temp_url_1.format(key_word, next_page)
                yield response.follow(next_url_1, callback=self.parse_book_list, meta={'item': item})
                # 构造后半页
                next_url_2 = temp_url_2.format(key_word, next_page)
                yield response.follow(next_url_2, callback=self.parse_book_list, meta={'item': item})

    def parse_detail(self, response):  # 解析详情页数据
        item = response.meta['item']
        # 确认商品是否存在
        if not len(response.xpath('//div[@class="search404"]')):
            author = response.xpath('//ul[@class="bookcon-param clearfix"]/li[contains(text(), "作者")]/span/text()').extract_first()
            item['book_detail'] = response.xpath('//ul[@class="bookcon-param clearfix"]/li[not(contains(text(), "作者"))]/text()').extract()
            if author is not None:
                author = "作者：" + author
                item['book_detail'].insert(0, author)

            # 拼装提取价格的页面
            catenIds = re.findall(r'"catenIds":"(.*?)"', response.body.decode(), re.S)[0]
            weight =  re.findall(r'"weight":"(.*?)"', response.body.decode(), re.S)[0]
            re_num = re.findall(r'/(\d+)', response.url)
            # 位数不足11位需要在前面补零
            if len(re_num[1]) < 11:
                len_couunt = 11 - len(re_num[1])
                re_num[1] = '0' * len_couunt + re_num[1]
            price_url = 'https://pas.suning.com/nspcsale_0_0000000{}_0000000{}_{}_320_023_0230101_502282_1000333_9325_12583_Z001___{}_{}___.html?callback=pcData'.format(re_num[1], re_num[1], re_num[0], catenIds, weight)
            yield response.follow(price_url, callback=self.parse_parice_url, meta={'item': item})
        else:
            item['book_detail'] = '此商品已不存在'
            yield item

    def parse_parice_url(self, response):  # 提取商品价格
        item = response.meta['item']
        resp_json = response.body.decode()
        # 不使用json提取的原因是返回的json不规范，开头有个pcData()
        item['netprice'] = re.findall(r'"netPrice":"(.*?)"', resp_json, re.S)[0]
        yield item

