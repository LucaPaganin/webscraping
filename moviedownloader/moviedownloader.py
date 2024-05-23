import requests
import logging
import yaml
from requests.adapters import HTTPAdapter, Retry
import threading
from pathlib import Path

# download from altadefinizione

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def download_movie(s, m3u8url, outfile=None, verbose=False, addheaders=None):
    # retrieve segments
    headers = {
        'Accept': '*/*',
        "Accept-Encoding": "gzip, deflate, br, zstd",
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'If-Modified-Since': 'Sun, 11 Sep 2000 09:00:00 GMT',
        'If-None-Match': '-1-4325',
        'Origin': 'https://supervideo.cc',
        'Referer': 'https://supervideo.cc/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': '"Mozilla/5.0"',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    if isinstance(addheaders, dict):
        headers.update(addheaders)
    r = requests.get(m3u8url, headers=headers)
    segments = list(s for s in r.text.splitlines() if not s.startswith("#"))
    base_url = "/".join(m3u8url.split("/")[:-1])
    mode = "wb"
    logging.info(f"Start download {base_url}")
    if outfile is None:
        outfile = "/Users/lucapaganin/Downloads/mymovie.mp4"
    with open(outfile, mode) as stream:
        for seg in segments:
            if verbose:
                logging.info(f"Processing seg {seg}")
            url = base_url + f"/{seg}"
            r = s.get(url, headers=headers)
            if r.status_code == 200:
                logging.info(f"seg {seg} downloaded")
                for chunk in r.iter_content():
                    stream.write(chunk)
            else:
                logging.info(f"status code {r.status_code} for url {url}, exiting")
                break
    logging.info(f"Finish download {base_url}")


def thread_download(*args, **kwargs):
    th = threading.Thread(target=download_movie, args=args, kwargs=kwargs)
    th.start()
    return th

if __name__ == '__main__':
    sep = "#"*15
    logging.info(sep*4)
    logging.info(f"{sep} Start movie_downloader.py {sep}")
    logging.info(sep*4)
    THISDIR = Path(__file__).parent
    with open(THISDIR/"config.yaml", 'r') as stream:
        config = yaml.safe_load(stream)
    
    s = requests.Session()
    retries = Retry(total=50,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504, 400, 401, 403, 429])

    s.mount('https://', HTTPAdapter(max_retries=retries))
    outfolder = Path.home()/"Downloads"
    threads = []
    for movie in config['movies']:
        logging.info(f"Starting thread for movie {movie['title']}")
        th = thread_download(
            s,
            movie["m3u8url"],
            outfile=outfolder/f'{movie["title"]}.ts'
        )
        threads.append(th)
    
    logging.info("Joining threads")
    for th in threads:
        th.join()
    logging.info(sep*4)
    logging.info(f"{sep} Finish movie_downloader.py {sep}")
    logging.info(sep*4)