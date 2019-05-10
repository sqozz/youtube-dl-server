import os
import json
import hashlib
import subprocess
import youtube_dl
import multiprocessing as mp
from queue import Queue
from bottle import route, run, Bottle, request, static_file
from multiprocessing import Process, Manager, Array

app = Bottle()

@app.route('/')
def dl_queue_list():
    return static_file('index.html', root='./')


@app.route('/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')


@app.route('/q', method='POST')
def q_put():
    url = request.forms.get("url")
    action = request.forms.get("action")
    if "" != url:
        if "," in url:
            for url in url.split(","):
                dl.queue_action(url, action)
        else:
            dl.queue_action(url, action)
        print("Added url " + url + " to the download queue")
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return { "success": True, "url": url, "url_hash": url_hash }
    else:
        return { "success": False, "error": "no url supplied" }


@app.route("/downloader_status", method="GET")
def status():
    status_json = dict(dl.status())
    return status_json


class Downloader():
    dl_q = None
    __manager = Manager()
    __config = {}

    def __init__(self, dl_config):
        self.__ctx = mp.get_context('spawn')
        self.__running_downloads = self.__manager.dict()
        self.dl_q = self.__ctx.Queue()
        self.__config = dl_config
        pass

    def status(self):
        return self.__running_downloads

    def queue_action(self, url, action):
        self.dl_q.put({"url": url, "action": action})
        process = self.__ctx.Process(target=self.dl_worker, args=(self.dl_q, self.__running_downloads,))
        process.start()

    def dl_worker(self, queue, already_running):
        def __progress_hook(d):
            stats = already_running[url_hash]
            status = d.get("status")
            if status == "downloading":
                total_bytes = d.get("total_bytes", 0)
                downloaded_bytes = d.get("downloaded_bytes", 0)
                percent_done = (100/total_bytes)*downloaded_bytes
                stats.update({
                             "status": "downloading",
                             "filename": d.get("filename", ""),
                             "speed": d.get("speed", 0),
                             "total_bytes": total_bytes,
                             "downloaded_bytes": downloaded_bytes,
                             "percent": round(percent_done, 2),
                             "eta": d.get("eta", -1)
                             })
            elif status == "finished":
                stats.update({"status": "postprocessing"})
                print("finished downloading \"{}\" in {}s. Now converting…".format(d.get("filename"), int(d.get("elapsed", "0"))))
            else:
                print("UNKNOWN STATUS:")
                print(d)
                print()

            already_running.update({url_hash:stats})


        if queue.qsize() <= 0:
            return
        else:
            item = queue.get()

        url = item["url"]
        action = item["action"]
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        if url_hash in already_running.keys():
            print("{} is already downloading. Skipping…".format(url))
            return
        else:
            stats = { "url": url, "download_action": action ,"status": "preparing"}
            already_running.update({url_hash: stats})

        print("Starting download of " + url)
        ydl_opts = self.__config.get(action, {})
        ydl_opts.update(self.__config.get("common", {}))
        ydl_opts.update({"logger": self.__dl_logger(),
                         "progress_hooks": [__progress_hook],
                       })

        ydl = youtube_dl.YoutubeDL(params=ydl_opts)
        with ydl:
            ydl.download([url])

        print("Finished downloading " + url)
        already_running.pop(url_hash, None)

    class __dl_logger(object):
        def debug(self, msg):
            pass

        def warning(self, msg):
            print(msg)
            pass

        def error(self, msg):
            print(msg)


def read_config():
    with open("config.json", "r") as f:
        config = f.read()
        config = json.loads(config)
    return config


if __name__ == '__main__':
    config = read_config()
    print(config)
    dl = Downloader(config.get("yt-dl_settings"))
    print("Started download thread")
    app.run(host='0.0.0.0', port=8080, debug=True)
