# -*- coding: utf-8 -*-
# 解析优酷视频真实地址，运行后直接粘贴优酷视频链接回车即可
# （pycharm中回车会直接跳转浏览器，可以粘贴连接后按下空格，再回车）
# 2017/4/12/22:50
# by malone
from urllib import parse as urlparse
import requests, time, json, re, urllib.parse
from fake_useragent import UserAgent
import hashlib
import os
import sys
import subprocess
import shutil

class Youku():
    def __init__(self):
        #print(sys.argv[1])
        self.url_input = input(
            "粘贴你想解析的优酷视频链接粘贴到此处，如:http://v.youku.com/v_show/id_XMTU3NTkxNDIwMA==.html,然后按回车键执行！" + '\n' + '>>>')
        #self.url_input = sys.argv[2]
        # 浏览器头
        self.headers = {"accept-encoding": "gzip, deflate, sdch",
                        "accept-language": "zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4",
                        "referer": self.url_input,
                        "user-agent": UserAgent().random,
                        }

        # cookies中的cna，优酷请求不能禁用cookies，这是我的本地浏览器浏览优酷的cookies，直接复制过来用
        self.utid = urllib.parse.quote('onBdERfZriwCAW+uM3cVByOa')

    def get_video_info(self):
        video_id = self.extract_id()
        # 解析视频真实地址的最最最关键的请求！！！所有信息都在返回的json格式文件中。
        # 通过抓包过程中可以得到F12监控加载信息。Ctrl+F搜索json?vid=就可以看到返回的json信息，复制粘贴到json在线解析网站（www.json.cn）对照分析
        # 根据分析，包括四个参数，然后程序生成相应参数，构造URL并进行模拟请求，得到返回数据
        url = 'https://ups.youku.com/ups/get.json?vid={}&ccode=0401&client_ip=192.168.1.1&utid={}&client_ts={}'.format(
            video_id, self.utid, int(time.time()))
        response = requests.get(url, headers=self.headers).text
        self.parse_res(response)

    # 正则提取输入链接中的优酷视频唯一id
    def extract_id(self):
        video_url = self.url_input
        pattern = re.compile('id_(.*)\.html')
        video_id = pattern.findall(video_url)[0]
        return video_id

    def parse_res(self, response):
        # 对json数据进行处理
        res_json = json.loads(response)
        video = res_json.get('data').get('video')
        print('\n''视频标题：', video.get('title'))
        if video.get('stream_types').get('default') != None:
            # 随便找了几个视频链接试了下，大部分视频格式是在json文件的'default'标签中
            print('\n', '该视频有以下几种格式：', video.get('stream_types').get('default'), '\n')
        else:
            # 试了优酷首页的人民的名义，视频格式在'guoyu'标签中，这里直接连父标签打出来
            print('\n', '该视频有以下几种格式：', video.get('stream_types'), '\n')
            # print('\n','该视频有以下几种格式：',video.get('stream_types').get('guoyu'),'\n')
        for stream in res_json.get('data').get('stream'):
            print('*' * 100)
            print('视频类型：', stream.get('stream_type'))
            print("视频总时长：", self.milliseconds_to_time(stream.get('milliseconds_video')))
            print('视频总大小:', '%.2f MB' % (float(stream.get('size') / (1024 ** 2))))
            #if isset(sys.argv[1]) and sys.argv[1] == stream.get('stream_type'):
            if sys.argv[1] == stream.get('stream_type'):
                self.get_seg(stream,video.get('title'),stream.get('stream_type'))
            #else:
                #self.get_seg(stream,video.get('title'),stream.get('stream_type'))

    # 信息中的视频时长是ms，用此函数转成时分秒的格式
    def milliseconds_to_time(self, milliseconds):
        seconds = milliseconds / 1000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)

    # 每个视频分成若干段，用此函数获得各段的信息
    def get_seg(self, stream,titlex,typex):
        titlemd5 = self.md5(titlex.strip())
        if os.path.exists(titlemd5) == False:
            os.mkdir(titlemd5)
        seg_num = len(stream.get('segs'))
        print('+' * 20, '该视频共%d段' % seg_num, '+' * 20)
        #f=open(titlex.strip()+'_'+typex+'.txt','a')
        #f2=open(titlex.strip()+'_'+typex+'.bat','a')
        #f2.write('mkdir '+titlemd5+'\n')
        concatstr = ''
        for i in range(seg_num):
            seg = stream.get('segs')[i]
            #print("第%d段时长：" % (i + 1), self.milliseconds_to_time(seg.get('total_milliseconds_video')))
            #print("第%d段大小：" % (i + 1), '%.2f MB' % (float(seg.get('size') / (1024 ** 2))))
            print("第%d段视频地址：" % (i + 1), seg.get('cdn_url'))
            #print("aria2c -c -o %s" % titlex , "_%d.mp4 " % (i + 1), seg.get('cdn_url') )
            #f2.write('ffmpeg -i "'+seg.get('cdn_url').replace('%','%%')+'" -c copy -vbsf h264_mp4toannexb '+titlemd5+'/'+str(i + 1)+'.ts\n')
            subprocess.call('ffmpeg -i "'+seg.get('cdn_url')+'" -c copy -vbsf h264_mp4toannexb '+titlemd5+'/'+str(i + 1)+'.ts',shell=True)
            concatstr = concatstr + titlemd5+'/'+str(i + 1)+'.ts|'
            #f.write('file "'+titlex.strip()+"_"+str(i+1)+'.mp4"\n')
        #f.close()
        #f2.write('ffmpeg -i concat:"'+concatstr.strip('|')+'" -c copy -absf aac_adtstoasc "' + titlex.strip() + '.mp4"\n')
        subprocess.call('ffmpeg -i concat:"'+concatstr.strip('|')+'" -c copy -absf aac_adtstoasc "' + titlex.strip() + '.mp4"')
        shutil.rmtree(titlemd5)
        #f2.write('del /q '+titlemd5+'/*.*\n')
        #f2.write('rd /q '+titlemd5+'\n')
        #f2.close()

    # 根据上面的到的链接下载视频
    def video_download(self):
        pass

    def md5(self,titlex):
        titlex = titlex.encode('utf-8')
        myMd5 = hashlib.md5()
        myMd5.update(titlex)
        myMd5_Digest = myMd5.hexdigest()
        return myMd5_Digest

if __name__ == '__main__':
    youku = Youku()
    youku.get_video_info()
    #exit = input('按任意键退出')
    print(u"下载完成。")
