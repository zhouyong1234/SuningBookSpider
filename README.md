# SuningBookSpider
基于redisscrapy的分布式爬虫

## 环境
- redis数据库
- mongoDB数据库
- python 3.6 (scrapy, scrapy-redis, pymongo)

## 启动
默认 redis_url = 'redis://127.0.0.1:6379/1'

- 初始化: 需要向 redis/1 中的 suning:start_urls 中传入初始url

```
# redis操作
select 1  # 选择db（1）
flushdb   # 清空db
lpush suning:start_urls http://book.suning.com/   # 添加初始url
```

- 命令行启动spider
```python
scrapy crawl suning
```

