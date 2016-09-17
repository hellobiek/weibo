# encoding=utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import re
import datetime
import time
import traceback
from scrapy.spider import CrawlSpider
from scrapy.selector import Selector
from scrapy.http import Request
from Sina_spider1.items import InformationItem, TweetsItem, FollowsItem, FansItem, CommentInfo

class Spider(CrawlSpider):
    name = "sinaSpider"
    host = "http://weibo.cn"
    start_urls = ["cctv5"]
    def start_requests(self):
        while True:
            url_tweets = "http://weibo.cn/cctv5"
            yield Request(url=url_tweets, callback=self.parse)

    def parse(self, response):
        selector = Selector(response)
        text1 = selector.xpath('/html/body/div[@id="pagelist"]/form/div').extract_first()
        page_num_list = re.findall(u'1/(\d+)\u9875', text1)# 总页数
        try:
            page_num = int(page_num_list[0]) + 1
        except Exception as e:
            traceback.print_exc()
            import pdb
            pdb.set_trace()
        for page in xrange(1, page_num):
            url_tweets = "http://weibo.cn/cctv5?page=%d" % page
            yield Request(url=url_tweets, callback=self.parse_page)

    def parse_page(self, response):
        """ 抓取微博数据 """
        selector = Selector(response)
        tweets = selector.xpath('body/div[@class="c" and @id]')
        for tweet in tweets:
            id = tweet.xpath('@id').extract_first()  # 微博ID
            content = tweet.xpath('div/span[@class="ctt"]/text()').extract_first()  # 微博内容
            ctime = tweet.xpath('div/span[@class="ct"]/text()').extract() #微博创建时间
            cooridinates = tweet.xpath('div/a/@href').extract_first()  # 定位坐标
            allinks = re.findall(u"<a.*?href=.*?[\d+].*?<\/a>", tweet.extract(), re.I|re.S|re.M)
            like = re.findall(u'\u8d5e\[(\d+)\]', tweet.extract())  # 点赞数
            transfer = re.findall(u'\u8f6c\u53d1\[(\d+)\]', tweet.extract())  # 转载数
            comment = re.findall(u'\u8bc4\u8bba\[(\d+)\]', tweet.extract())  # 评论数
            comment_link = ""
            for link in allinks:
                like_link_list = re.findall(u'"(http.*)">\u8d5e.*', link)
                if len(like_link_list) > 0:
                    like_link = like_link_list[0]
                transfer_link_list = re.findall(u'"(http.*)">\u8f6c\u53d1.*', link)
                if len(transfer_link_list) > 0:
                    transfer_link = transfer_link_list[0]
                comment_link_list = re.findall(ur'"(http.*?)" class="cc".*>\u8bc4\u8bba\[\d+\]</a>', link)
                if len(comment_link_list) > 0:
                    comment_link = comment_link_list[0]
            tweetsItems = TweetsItem()
            others = tweet.xpath('div/span[@class="ct"]/text()').extract_first()  # 求时间和使用工具（手机或平台）
            tweetsItems["ID"] = "cctv"
            if content:
                tweetsItems["Content"] = content.strip(u"[\u4f4d\u7f6e]")  # 去掉最后的"[位置]"
            if ctime:
                tweetsItems["Time"] = ctime
            if cooridinates:
                cooridinates = re.findall('center=([\d|.|,]+)', cooridinates)
                if cooridinates:
                    tweetsItems["Co_oridinates"] = cooridinates[0]
            if like:
                tweetsItems["Like"] = int(like[0])
            if transfer:
                tweetsItems["Transfer"] = int(transfer[0])
            if comment:
                tweetsItems["Comment"] = int(comment[0])
            if comment_link != "":
                yield Request(url=comment_link, meta={'tweetsItems': tweetsItems, 'comment_link': comment_link}, callback=self.parse_fans_name)

    def parse_fans_name(self, response):
        item = response.meta['tweetsItems']
        link = response.meta['comment_link']
        selector = Selector(response)
        try:
            comments = selector.xpath('/html/body/div[@class="c" and @id]')
        except Exception as e:
            traceback.print_exc()
            import pdb
            pdb.set_trace()
        item["CommentInfo"] = []
        for comment in comments:
            try:
                #get comment time
                cid=re.findall('<div class="c" id="(.*?)">', comment.extract())[0]
                if cid != "M_":
                    ctime = re.findall(u'<span class="ct">(.*?)</span>', comment.extract())[0].strip()
                    uinfo = re.findall('<a href="/u/(\d+)">(.*?)</a>', comment.extract())
                    uid = uinfo[0][0]
                    uname = uinfo[0][1]
                    content = re.findall('<span class="ctt">(.*?)</span>', comment.extract())[0]
                    commentInfo = CommentInfo()
                    commentInfo["ID"] = cid
                    commentInfo["Uid"] = uid
                    commentInfo["Uname"]= uname
                    commentInfo["Content"] = content
                    commentInfo["Time"] = ctime
                    item["CommentInfo"].append(commentInfo)
                    yield item
            except Exception as e:
                traceback.print_exc()
                import pdb
                pdb.set_trace()
