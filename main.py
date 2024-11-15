import time
import logging
import schedule
from prometheus_client import start_http_server, Gauge
import speedtest
import requests

logging_format = '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=logging_format)

PORT = 8000
PAGE_LOAD_FREQ_IN_SEC = 15
SPEEDTEST_FREQ_IN_SEC = 900
URL = "https://google.com"

speedtest_upload = Gauge('watchdog_speedtest_upload_mb', 'Speedtest upload speed in MB.')
speedtest_download = Gauge('watchdog_speedtest_download_mb', 'Speedtest download speed in MB.')
page_load_in_sec = Gauge('watchdog_pageload_in_sec', 'Google.com page load in seconds.')

def get_page_load_time(url: str) -> None:
    logging.info(f"Running page load time test against {url}.")
    try:
        page_load_in_sec.set(requests.get(url, allow_redirects=True).elapsed.total_seconds())
    except Exception as e:
        logging.error(f"Exception while running page load test: {e}")
        page_load_in_sec.set(-1)

def get_speed_test_results() -> None:
    logging.info("Running internet speed test.")
    try:
        test = speedtest.Speedtest()
        test.get_best_server()
        download = test.download() / 1000000
        upload = test.upload() / 1000000
    except Exception as e:
        logging.error(f"Exception while running speedtest: {e}")
        download = -1
        upload = -1
    speedtest_download.set(round(download, 2))
    speedtest_upload.set(round(upload, 2))

def main():
    logging.info("Hydrating gauges...")
    get_page_load_time(url=URL)
    get_speed_test_results()
    logging.info("Creating scheduled jobs.")
    schedule.every(PAGE_LOAD_FREQ_IN_SEC).seconds.do(get_page_load_time, url=URL)
    schedule.every(SPEEDTEST_FREQ_IN_SEC).seconds.do(get_speed_test_results)
    logging.info(f"Starting Prometheus web server on port {PORT}.")
    start_http_server(PORT)
    while True:
        schedule.run_pending()
        time.sleep(1)

main()