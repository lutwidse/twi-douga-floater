import requests, urllib.request, urllib.error, socket, struct
from requests import Timeout
import random, string, datetime, time, threading
from fake_useragent import UserAgent
import argparse
from pathlib import Path

parser = argparse.ArgumentParser("れ～どめ～")
parser.add_argument("-t", "--threads", help="スレッド数", type=int, default=5, required=False)
parser.add_argument("-p", "--proxies", help="プロキシ", type=lambda p: Path(p).absolute(), required=True)
parser.add_argument("-v", "--videos", help="動画", type=lambda p: Path(p).absolute(), required=True)
args = parser.parse_args()

class Config(object):
    def __init__(self):
        self.URL = "http://www.nurumayu.net:443/twidouga/gettwi.php"
        self.CLIENT_TEXT = f"[twi-douga-floater]"
        self.PROXY_TIMEOUT = 10
        self.DELAY = 10
        self.TARGET_VIEWS = 100
        self.BLOCKLISTED_THRESHOLD = 3

        self.req_count = 0

        self.len_proxies = 0
        self.len_twitter_videos = 0

        self.proxies = []
        self.twitter_videos = {}

        # プロキシ
        temp_proxies = []
        with open(args.proxies) as f:
            lines = f.readlines()
            for l in lines:
                l = l.replace("\n", "")
                temp_proxies.append(l)
            f.close()

        print(f"{self.get_CLIENT_TEXT()} プロキシを検証中…")

        # socks5
        pt = []

        for proxy in temp_proxies:
            pt.append(threading.Thread(target=self._proxy_check_socks5, args=(proxy,)))
        for t in pt:t.start()
        for t in pt:t.join()

        pt.clear()
        for p in self.proxies:
            if p in temp_proxies:
                temp_proxies.remove(p)

        # http
        for proxy in temp_proxies:
            pt.append(threading.Thread(target=self._proxy_check_http, args=(proxy,)))  
        for t in pt:t.start()
        for t in pt:t.join()

        self.update_len_proxies()
        print(f"{self.get_CLIENT_TEXT()} 検証完了 | 有効なプロキシ: {self.get_len_proxies()}個")
        
        # 動画
        with open(args.videos) as f:
            lines = f.readlines()
            for l in lines:
                l = l.replace("\n", "")
                self.twitter_videos[l] = [0, 0]
            f.close()
            self.update_len_twitter_videos()
        
        self.LEN_PROXIES = self.get_len_proxies()
        self.LEN_TWITTER_VIDEOS = self.get_len_twitter_videos()

    # Getter
    def get_req_count(self):
        return self.req_count
    
    def get_len_proxies(self):
        return len(self.proxies)
        
    def get_len_twitter_videos(self):
        return len(self.twitter_videos)

    def get_CLIENT_TEXT(self):
        return f"{self.CLIENT_TEXT} | {self.get_now()} |"

    def progress_check(self):
        return self.get_len_proxies() and self.get_len_twitter_videos()
    
    # Setter
    def set_req_count(self):
        self.req_count += 1

    # Deleter
    def del_proxy(self, proxy):
        self.proxies.remove(proxy)

    def del_twitter_video(self, key):
        self.twitter_videos.pop(key)

    # Updater
    def update_len_proxies(self):
        self.len_proxies = len(self.proxies)

    def update_len_twitter_videos(self):
        self.len_twitter_videos = len(self.twitter_videos)
    
    # プロキシ
    def _proxy_check_socks5(self,proxy):
        try:
            ip, port = proxy.split(":")
            packet = struct.pack('BBB', 0x05, 0x01, 0x00)
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.PROXY_TIMEOUT)
            s.connect((ip, int(port)))
            s.sendall(packet)
            
            data = s.recv(2)
            version, auth = struct.unpack('BB', data)
            if(version == 5 and auth == 0):
                self.proxies.append(f"socks5://{proxy}")
                s.close()
        except Exception:
            pass

    def _proxy_check_http(self,proxy):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": f"{proxy}"})
            opener = urllib.request.build_opener(proxy_handler)
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            req=urllib.request.Request("http://www.google.com")
            urllib.request.urlopen(req, timeout=self.PROXY_TIMEOUT)
            
            self.proxies.append(proxy)
        except Exception:
            pass

    def random_ua(self):
        ua = UserAgent()
        user_agent = ua.random
        return user_agent

    def get_now(self):
        return datetime.datetime.now().strftime("%H:%M:%S")
        
    def random_name(self, n):
        randlst = [random.choice(string.ascii_letters + string.digits) for _ in range(n)]
        return ''.join(randlst)

    # random range number
    def rrn(self, n):
        return random.randrange(9**n, 10**n)

class ObserverClient(threading.Thread):
    def __init__(self, conf):
        threading.Thread.__init__(self)
        self.conf = conf

    def run(self):
        while self.conf.progress_check():
            time.sleep(10)
            req_count = self.conf.get_req_count()
            info_text = "{}{}{}".format(
                f"{self.conf.get_CLIENT_TEXT()} リクエスト [ 送信:{req_count}件 | 残り:{self.conf.len_twitter_videos * self.conf.TARGET_VIEWS - req_count}件 ] | ",
                f"動画 [ 完了:{self.conf.LEN_TWITTER_VIDEOS - self.conf.get_len_twitter_videos()}個 | 残り:{self.conf.get_len_twitter_videos()}個 ] |",
                f"プロキシ [ 有効:{self.conf.get_len_proxies()}個 | 規制:{self.conf.LEN_PROXIES - self.conf.get_len_proxies()}個 ]"
                )
            
            print(info_text)

            if (self.conf.get_len_proxies() <= 0) or (self.conf.get_len_twitter_videos() <= 0):
                print(f"{self.conf.get_CLIENT_TEXT()} 終了")
                input()
                exit(1)

class RequestClient(threading.Thread):
    def __init__(self, lock, conf):
        threading.Thread.__init__(self)
        self.lock = lock
        self.conf = conf

    def run(self):
        while self.conf.progress_check():
            try:
                time.sleep(random.randint(1, self.conf.DELAY))

                random_proxy = self.get_random_proxy()
                proxy_dict = {
                    "http": random_proxy,
                }

                key, values = self.get_random_twitter_video_pairs()
                video_count = values[0]
                restriction_count = values[1]

                self.lock.acquire()
                if video_count == self.conf.TARGET_VIEWS:
                    print(f"{self.conf.CLIENT_TEXT} 完了: {key}")
                    self.conf.del_twitter_video(key)
                    self.conf.update_len_twitter_videos()
                    continue
                self.lock.release()
                
                headers, data = self.get_request_context(key)
                req = requests.Session()
                req.max_redirects = 1024
                resp = req.post(self.conf.URL, headers=headers, cookies=self.get_random_cookies(), data=data, timeout=(3, 0.1), proxies=proxy_dict)
                
                status = resp.status_code
                if status != 200:
                    self.conf.del_proxy(random_proxy)
                    self.set_twitter_videos_restriction_count(key)
                    if self.conf.BLOCKLISTED_THRESHOLD <= restriction_count:
                        print(f"{self.conf.get_CLIENT_TEXT()} 動画またはプロキシのブロックを検知しました: {key}")
                        self.conf.del_twitter_video(key)
                        self.conf.update_len_twitter_videos()
                        continue
                    continue

                self.set_twitter_videos_count(key)
                self.conf.set_req_count()

            except Timeout:
                pass
            except requests.ConnectionError:
                    self.conf.del_proxy(random_proxy)
            except ValueError:
                pass
            except IndexError:
                pass
            except KeyError:
                pass

    def get_request_context(self, url):
        random_boundary = self.conf.random_name(16)
        headers = {"Connection": "close", "Cache-Control": "max-age=0", "Upgrade-Insecure-Requests": "1", "Origin": "https://www.nurumayu.net", "Content-Type": f"multipart/form-data; boundary=----WebKitFormBoundary{random_boundary}", "User-Agent": self.conf.random_ua(), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Referer": "https://www.nurumayu.net/twidouga/gettwi.php", "Accept-Encoding": "gzip, deflate", "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"}
        data = f"------WebKitFormBoundary{random_boundary}\r\nContent-Disposition: form-data; name=\"param\"\r\n\r\n{url}\r\n------WebKitFormBoundary{random_boundary}\r\nContent-Disposition: form-data; name=\"exec\"\r\n\r\n\xe6\x8a\xbd\xe5\x87\xba\r\n------WebKitFormBoundary{random_boundary}--\r\n"
        return headers, data

    def get_random_cookies(self):
        return {"_ga": f"GA1.2.{self.conf.rrn(9)}.{self.conf.rrn(10)}", "_gid": f"GA1.2.{self.conf.rrn(9)}.{self.conf.rrn(10)}", "_gat": "1", "adr_id": f"{self.conf.random_name(48)}"}

    def get_random_twitter_video_pairs(self):
        return random.choice(list(list(self.conf.twitter_videos.items())))

    def get_random_proxy(self):
        return random.choice(self.conf.proxies)

    def set_twitter_videos_count(self, video):
        self.lock.acquire()
        self.conf.twitter_videos[video][0] += 1
        self.lock.release()

    def set_twitter_videos_restriction_count(self, video):
        self.lock.acquire()
        self.conf.twitter_videos[video][1] += 1
        self.lock.release()

if __name__ == "__main__":
    conf = Config()
    oc = ObserverClient(conf)
    oc.start()
    lock = threading.Lock()
    for _ in range(args.threads):
        rc = RequestClient(lock, conf)
        rc.start()