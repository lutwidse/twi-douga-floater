import requests, urllib.request, urllib.error, socket
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

def get_now():
    return datetime.datetime.now().strftime("%H:%M:%S")

def random_name(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for _ in range(n)]
    return ''.join(randlst)

def random_ua():
    ua = UserAgent()
    user_agent = ua.random
    return user_agent

req_count = 0
in_progress = True
URL = "https://www.nurumayu.net:443/twidouga/gettwi.php"

CLIENT_TEXT = f"[twi-douga-floater]"
DELAY = 10
TARGET_VIEWS = 100

# プロキシ
def proxy_check(proxy):
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        req=urllib.request.Request("http://www.google.com")
        urllib.request.urlopen(req, timeout=10)

        http_proxies.append(proxy)
    except urllib.error.HTTPError:
        pass
    except socket.timeout:
        pass
    except Exception:
        pass

http_proxies = []
with open(args.proxies) as f:
    lines = f.readlines()
    proxy_threads = []
    for l in lines:
        l = l.replace("\n", "")
        proxy_threads.append(threading.Thread(target=proxy_check, args=(l,)))
    f.close()

print(f"{CLIENT_TEXT} | {get_now()} | プロキシを検証中…")
for pt in proxy_threads:pt.start()
for pt in proxy_threads:pt.join()
LEN_HTTP_PROXIES = len(http_proxies)
print(f"{CLIENT_TEXT} | {get_now()} | 検証完了 | 有効なプロキシ: {LEN_HTTP_PROXIES}個")

# 動画
twitter_videos = {}
with open(args.videos) as f:
    lines = f.readlines()
    for l in lines:
        l = l.replace("\n", "")
        twitter_videos[l] = 0
    f.close()
LEN_TWITTER_VIDEOS = len(twitter_videos)

def get_len_http_proxies():
    return len(http_proxies)

def get_len_twitter_videos():
    return len(twitter_videos)

class ObserverClient(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(10)
            print(f"{CLIENT_TEXT} | {get_now()} | リクエスト:{req_count}件 | 残り:{LEN_TWITTER_VIDEOS * TARGET_VIEWS - req_count}件 | 動画: {get_len_twitter_videos()}個 | プロキシ [ 有効:{get_len_http_proxies()}個 | 規制:{LEN_HTTP_PROXIES - get_len_http_proxies()}個 ]")

            if (get_len_http_proxies() <= 0) or (get_len_twitter_videos() <= 0):
                self.disable_in_progress()
                print(f"{CLIENT_TEXT} | {get_now()} | 終了")
                input()
                exit(1)
    
    def disable_in_progress(self):
        global in_progress
        in_progress = False

class RequestClient(threading.Thread):
    def __init__(self, n, lock):
        threading.Thread.__init__(self)
        self.n = n
        self.lock = lock

    def run(self):
        while True and in_progress:
            try:
                time.sleep(random.randint(1, DELAY))

                random_http_proxy = random.choice(http_proxies)
                proxy_dict = {
                    "http": f"http://{random_http_proxy}",
                }
                key, value = self.get_random_twitter_video_pairs()

                if value > TARGET_VIEWS:
                    print(f"{CLIENT_TEXT} 完了: {key}")
                    del twitter_videos[key]
                    continue
                
                headers, data = self.get_request_context(key)
                req = requests.Session()
                req.max_redirects = 1024
                resp = req.post(URL, headers=headers, data=data, timeout=(5, 10), proxies=proxy_dict)
                
                status = resp.status_code
                if status != 200:
                    http_proxies.remove(random_http_proxy)

                self.set_twitter_videos_count(key)
                self.set_req_count()

            except Timeout:
                pass
            except requests.ConnectionError:
                    http_proxies.remove(random_http_proxy)
            except ValueError:
                pass
            except IndexError:
                pass
            except KeyError:
                pass

    def get_request_context(self, url):
        random_boundary = random_name(16)
        headers = {"Connection": "close", "Cache-Control": "max-age=0", "Upgrade-Insecure-Requests": "1", "Origin": "https://www.nurumayu.net", "Content-Type": f"multipart/form-data; boundary=----WebKitFormBoundary{random_boundary}", "User-Agent": random_ua(), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Referer": "https://www.nurumayu.net/twidouga/gettwi.php", "Accept-Encoding": "gzip, deflate", "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"}
        data = f"------WebKitFormBoundary{random_boundary}\r\nContent-Disposition: form-data; name=\"param\"\r\n\r\n{url}\r\n------WebKitFormBoundary{random_boundary}\r\nContent-Disposition: form-data; name=\"exec\"\r\n\r\n\xe6\x8a\xbd\xe5\x87\xba\r\n------WebKitFormBoundary{random_boundary}--\r\n"
        return headers, data
    def get_random_twitter_video_pairs(self):
        return random.choice(list(twitter_videos.items()))

    def set_twitter_videos_count(self, video):
        self.lock.acquire()
        twitter_videos[video] = twitter_videos.get(video, 0) + 1
        self.lock.release()

    def set_req_count(self):
        self.lock.acquire()
        global req_count
        req_count += 1
        self.lock.release()

if __name__ == "__main__":
    oc = ObserverClient()
    oc.start()
    lock = threading.Lock()
    for _ in range(args.threads):
        rc = RequestClient(random_name(3), lock)
        rc.start()