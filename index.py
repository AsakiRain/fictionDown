import os,sys
import queue
from threading import Lock, Thread
import requests
from fake_useragent import UserAgent
from lxml import etree

ABSPATH = os.path.dirname(os.path.abspath(__file__)) + os.path.sep
print(ABSPATH)

class Spider():  # 定义爬虫类
    def __init__(self, url, num=10):  # 初始化
        """
        :param url:小说的全部目录界面
        :param name:小说名字
        :param num:线程数量，默认为10
        """
        self.url = url
        self.name = None
        self.num = num
        self.error_num = 0  # 出错章节的数量
        self.error_list = []
        self.encode = 'utf8'  # 编码为utf8

        self.title_rule = "//div[@id='info']/h1/text()" # 提取标题的规则
        self.list_rule = "//div[@id='list']/dl/dd/a"  # 提取章节列表的规则<a>
        self.content_rule = "//div[@id='content']/text()"  # 提取正文的规则
        self.content_list = []

    def get_ua(self):  # 随机获取请求头
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        return headers

    def get_list(self):  # 获取章节列表
        html = requests.get(self.url, headers=self.get_ua())  # 请求网络
        tree = etree.HTML(html.content.decode(self.encode))  # 设置编码
        self.name = tree.xpath(self.title_rule)[0] # 自动获取标题
        aa = tree.xpath(self.list_rule)
        for a in aa:
            title = self.del_title(a.xpath('text()')[0])
            url = self.url + a.xpath("@href")[0].split('/')[-1]
            print(url)
            self.content_list.append({"title": title, "url": url})

    def del_title(self, string):  # 处理特殊字符
        res = ''
        for i in string:
            index = ord(i)
            if 19968 <= index <= 40869 or 97 <= index <= 122 or 65 <= index <= 90 or 48 <= index <= 57 or index == 32:
                res += i
        return res

    def get_content(self, q):  # "从队列中提取章节进行下载" q: 队列
        l = Lock()
        while True:
            title, url = q.get()
            if(os.path.exists(os.path.join(ABSPATH, self.name, f"{title}.txt"))):
                print('已存在：' + title)
            else:
                try:
                    html = requests.get(url, timeout=10,headers=self.get_ua())
                except:
                    print("==>网络错误：", title)
                    self.error_num += 1
                    self.error_list.append(title + "（网络错误）")
                    with open(os.path.join(ABSPATH, self.name, 'test.ml'), 'a') as ff:
                        ff.write(url + "\n")
                else:
                    tree = etree.HTML(html.content)
                    content = ''.join(tree.xpath(self.content_rule))
                    if(content):
                        l.acquire()
                        print("已下载：" + title)
                        l.release()
                        # 处理章节名称异常导致的文件错误
                        try:
                            with open(os.path.join(ABSPATH, self.name, f"{title}.txt"), 'w', encoding="utf8") as f:
                                f.write(title + "\n" + str(content) + "\n")
                        except:
                            print('==>文件名错误：' + title)
                            self.error_list.append(title + "(文件名错误)")
                            self.error_num += 1
                    else:
                        print('==>空内容，重新下载：'+ title)
                        q.put((title, url))
            q.task_done()

    def get_novel(self): #"将单章小说整合成一整部"
        file = open(os.path.join(ABSPATH, f"{self.name}.txt"), 'w', encoding="utf8")
        for i in self.content_list:
            if i['title'] in self.error_list:
                continue
            try:
                with open(os.path.join(ABSPATH, self.name, f"{i['title']}.txt"), 'r', encoding="utf8") as f2:
                    file.write(f2.read())
            except:
                pass
        file.close()

    def run(self):
        print("读取中...")
        self.get_list()
        print('下载：《' + self.name + '》')
        print("章节读取完毕，共%d章" % len(self.content_list))
        q = queue.Queue()
        if not os.path.exists(os.path.join(ABSPATH, self.name)):
            print('创建目录...')
            os.makedirs(os.path.join(ABSPATH, self.name))
        for i in range(self.num):
            t = Thread(target=self.get_content, args=(q,))
            t.daemon = True
            t.start()
        for i in self.content_list:
            q.put((i['title'], i['url']))
        q.join()
        print("下载完成，文件整合中...")
        self.get_novel()
        print("文件整合完毕！")
        print(f"共计{len(self.content_list)}章，成功下载{len(self.content_list) - self.error_num}章, 失败章节：{'、'.join(self.error_list)}")
if(len(sys.argv) != 3):
    task = Spider("https://www.xbiquge.la/84/84624/", 1)     # 链接末尾需要斜杠！
else:
    task = Spider(sys.argv[1], int(sys.argv[2]))
task.run()
