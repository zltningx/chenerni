# -*- coding: utf-8 -*-
# @Time : 2019/6/20 16:40
# @Author : zltningx

"""
多进程版本~~~~
"""


import requests
import re
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

from concurrent.futures import ProcessPoolExecutor, wait, ALL_COMPLETED


def get_cities():
    """
    get all cities's name from page
    :return:  list object ['北京', '上海', '广州', '深圳',...]
    """
    response = requests.get("https://www.aqistudy.cn/historydata/")
    content = response.content.decode('utf-8')
    pattern = re.compile(r'<a href="monthdata.php\?city=(.*?)">')
    return re.findall(pattern, content)


def get_months():
    """
    get all months from page
    :return:  list object ['201312', '201401', '201402', '201403', '201404',...]
    """
    response = requests.get("https://www.aqistudy.cn/historydata/monthdata.php?city=北京")
    content = response.content.decode('utf-8')
    pattern = re.compile(r'<a href="daydata.php\?city=北京&month=(.*?)">')
    return re.findall(pattern, content)


def do_it(months, city, options):
    driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=options)
    headers = ['日期', 'AQI', '质量等级' 'PM2.5', 'PM10', 'SO2', 'CO', 'NO2', 'O3_8h']
    # 写进文件
    with open(f'./output/{city}.csv', 'w') as f:
        csv_f = csv.writer(f)
        csv_f.writerow(headers)
        for month in months:
            url = f"https://www.aqistudy.cn/historydata/daydata.php?city={city}&month={month}"
            driver.get(url)
            try:
                # 等待时间15s， 已获取js解析后的页面
                # 如果网络不好可能会获取不了数据
                # 注意!!
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "td"))
                )
            except:
                # 打印这个说明
                # 1. 页面没有数据。
                # 2. 15秒时间你还没加载出js
                print(f'no found td: {url}')
            try:
                pattern = re.compile(r'<td align="center".*?>(.*?)</td>')
                span_pattern = re.compile(r'<span style=".*?">(.*?)</span>')
                data_list = re.findall(pattern, driver.page_source)

                # 处理data 去掉span标签
                def del_data(data):
                    if 'span' in data:
                        return re.findall(span_pattern, data)[0]
                    else:
                        return data

                data_list = [del_data(item) for item in data_list]
                csv_f.writerows([data_list[i:i + 9] for i in range(0, len(data_list), 9)][0:-1])
            except:
                # 到了这一步就需要特别注意，这个可能是进程开多了导致出错
                # 页面是有数据的但是没有获取到
               print(url)
    driver.close()


def main():
    # 加载无头浏览器0/0 headless browse
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    months = get_months()
    all_tasks = []
    # 三进程，进程太多会不稳定
    with ProcessPoolExecutor(3) as Executor:
        for city in get_cities():
            # 执行多进程
            all_tasks.append(Executor.submit(do_it, months, city,  options))

    # 阻塞主进程，等待所有子子进程结束。
    wait(all_tasks, return_when=ALL_COMPLETED)


if __name__ == '__main__':
    main()
