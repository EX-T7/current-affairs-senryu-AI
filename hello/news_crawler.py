""" 各ニュースサイトから記事をクローリングする."""
import re
import sys
import time
import logging
import requests
from urllib.parse import urljoin
from concurrent import futures
from bs4 import BeautifulSoup


# デバッグメッセージを有効にする場合はコメントアウトする
# logging.disable(logging.CRITICAL)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


def yahoo_news_crawling():
    """Yahooニュース から記事をクローリングする."""
    article = []
    # 記事一覧を取得する
    for i in range(1, 30):
        response = requests.get('https://news.yahoo.co.jp/topics/top-picks?page={}'.format(i))
        if response.status_code == 404:
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        article_url = list(map(lambda x: x.get('href'),
                               [x for x in soup.select('.newsFeed_item > a')]))
        
        # 個別の記事へ
        try:
            for a in article_url:
                response = requests.get(a)
                if response.status_code == 404:
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')

                # 個別の記事の詳細へ
                a = soup.select('.sc-dcOKER.hqjjOv')[0].get('href')
                response = requests.get(a)
                if response.status_code == 404:
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.select('.sc-ipZHIp.lczCjB')    # たまに書式が違う記事あり
                if title == []:
                    title = soup.select('.articleBody > div > h1')[0].text
                    title = ' '.join(title.split())
                    body = list(map(lambda x: x.text,
                                [x for x in soup.select('#byline_detail_article > div > p')]))
                    body = ''.join(body).replace('\n', '')

                else:
                    title = title[0].text
                    title = ' '.join(title.split())
                    body = soup.select('.sc-gqPbQI.hvfJU.yjSlinkDirectlink')[0].text
                    body = ''.join(body.split())
                    body = re.sub(r"\n<aside.*\n", '', s)
                    body = re.sub(r'\(?(<p|<a|<span).*(</p>|</a>|</span>)\)?', '', body)

                article.append([title, body])
                logging.debug("title: %s\nbody: %s\n", title, body)

                time.sleep(3.0)     # Webサイトへ過剰に負荷をかけないため

        except KeyboardInterrupt:
            sys.exit(1)
        except:
            pass

    return article


def sankei_news_crawling():
    """産経ニュースから記事をクローリングする."""
    article = []
    genres = ['https://www.sankei.com/affairs/affairs.html',
              'https://www.sankei.com/politics/politics.html',
              'https://www.sankei.com/world/world.html',
              'https://www.sankei.com/economy/economy.html',
              'https://www.sankei.com/sports/sports.html',
              'https://www.sankei.com/entertainments/entertainments.html',
              'https://www.sankei.com/life/life.html']
    # ジャンルごとの記事一覧を取得する
    for genre in genres:
        response = requests.get(genre)
        soup = BeautifulSoup(response.text, 'html.parser')
        article_url = list(map(lambda x: urljoin(genre, x.get('href')),
                               [x for x in soup.select('.entry.inline.is-arrow > h3 > a')]))

        # 個別の記事へ
        try:
            for a in article_url:
                response = requests.get(a)
                if response.status_code == 404:
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.select('#__r_article_title__')[0].text
                title = ' '.join(title.split())
                body = soup.select('.post_content > p')
                body = ''.join([re.sub(r'(<p>|</p>|　|)', '', str(a)) for a in body])
                body = re.sub(r'\(?(<p|<a|<span).*(</p>|</a>|</span>)\)?', '', body)

                article.append([title, body])
                logging.debug("title: %s\nbody: %s\n", title, body)

                time.sleep(3.0)
                
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            pass

    return article


def asahi_news_crawling():
    """朝日新聞デジタルから記事をクローリングする."""
    article = []
    genres = ["https://www.asahi.com/national/list/",
              "http://www.asahi.com/business/list/",
              "https://www.asahi.com/politics/list/",
              "http://www.asahi.com/international/list/",
              "http://www.asahi.com/tech_science/list/",
              "http://www.asahi.com/culture/list/",
              "http://www.asahi.com/life/list/",
              "http://www.asahi.com/edu/list/"]

    # ジャンルごとの記事一覧を取得する
    for genre in genres:
        response = requests.get(genre)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        article_url = list(map(lambda x: urljoin(genre, x.get('href')),
                           [x for x in soup.select('.List > li > a')]))

        # 個別の記事へ
        try:
            for a in article_url:
                response = requests.get(a)
                response.encoding = response.apparent_encoding
                if response.status_code == 404:
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.select('.Title > h1')[0].text
                title = ''.join(title.split())
                body = soup.select('.ArticleText > p')
                if soup.select(".Title > .TagUnderTitle > p > span[class^=TagMember]") != []:
                    body = body[:-2]
                else:
                    body = body[:-1]
                body = ''.join([re.sub(r'(<p>|</p>|　|)', '', str(a)) for a in body])
                body = re.sub(r'\(?(<p|<a|<span).*(</p>|</a>|</span>)\)?', '', body)

                article.append([title, body])
                logging.debug("title: %s\nbody: %s\n", title, body)

                time.sleep(3.0)

        except KeyboardInterrupt:
            sys.exit(1)
        except:
            pass

    return article


def main():
    with futures.ThreadPoolExecutor(max_workers=3) as executor:
        # yahooニュースから記事をクローリングする
        yahoo_article = executor.submit(yahoo_news_crawling)
        # 産経ニュースから記事をクローリングする
        sankei_article = executor.submit(sankei_news_crawling)
        # 朝日新聞デジタルから記事をクローリングする
        asahi_article = executor.submit(asahi_news_crawling)

    print(yahoo_article.result(), end="\n")
    print(sankei_article.result(), end="\n")
    print(asahi_article.result(), end="\n")

    return([yahoo_article.result(), sankei_article.result(), asahi_article.result()])


if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    diff_time = end_time - start_time
    print("クローリング完了。")
    print("実行時間： {} 秒".format(diff_time))

