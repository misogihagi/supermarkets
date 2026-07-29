import json
import os
import re
from typing import Literal

import pymupdf
import requests
from bs4 import BeautifulSoup

region = {
    # 地方名と都道府県名が一致するとエラーになるのでコメントアウト
    # "北海道": ["北海道"],
    "東北": [
        "青森県",
        "岩手県",
        "宮城県",
        "秋田県",
        "山形県",
        "福島県",
    ],
    "関東": [
        "茨城県",
        "栃木県",
        "群馬県",
        "埼玉県",
        "千葉県",
        "東京都",
        "神奈川県",
        "山梨県",
        "長野県",
    ],
    "北陸": [
        "新潟県",
        "富山県",
        "石川県",
        "福井県",
    ],
    "中部": [
        "岐阜県",
        "静岡県",
        "愛知県",
        "三重県",
    ],
    "東海": [
        "岐阜県",
        "静岡県",
        "愛知県",
        "三重県",
    ],
    "近畿": [
        "滋賀県",
        "京都府",
        "大阪府",
        "兵庫県",
        "奈良県",
        "和歌山県",
    ],
    "中国": [
        "鳥取県",
        "島根県",
        "岡山県",
        "広島県",
        "山口県",
    ],
    "四国": [
        "徳島県",
        "香川県",
        "愛媛県",
        "高知県",
    ],
    "九州": ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県"],
    "沖縄": ["沖縄県"],
    "海外": [],
}
Prefecture = Literal[
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
]


class SuperMarket:
    prefecture: Prefecture
    company_name: str
    company_url: str
    belong_to: str  # 加盟企業もしくはグループ企業
    supermarket_names: list[str]
    songs: list[str]


# 一般社団法人全国スーパーマーケット協会 (NSAJ) 正会員


def nsaj():
    rows = []
    url = "https://www.super.or.jp/?page_id=71"
    css_selector = ".memberlist"
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
        soup = BeautifulSoup(response.text, "html.parser")
        prefecture_elements = soup.select(css_selector)
        for prefecture_element in prefecture_elements:
            prefecture = prefecture_element.find("h3").get_text(strip=True)
            li_elements = prefecture_element.select("li")
            for li in li_elements:
                li_text = li.get_text(strip=True)
                a = li.find("a")
                if a is None:
                    # if no link, li text is company name
                    href = None
                    company_name = re.sub("\*.?", "", li_text)
                    supermarket_names = (
                        li_text[li_text.rfind("(") + 1 : li_text.rfind(")")].split("、")
                        if li_text.count("(") > 1
                        else []
                    )
                else:
                    href = a.get("href")
                    if a.get_text() == "(協)ハニー":
                        row = {
                            "prefecture": prefecture,
                            "href": href,
                            "company_name": "(協)ハニー",
                            "supermarket_names": [],
                        }
                    # extract bracket
                    company_name = re.sub("\*.?", "", a.get_text())
                    # supermarket name requires 2 charas
                    supermarket_names = (
                        li_text[len(a.get_text()) + 1 : li_text.rfind(")")].split("、")
                        if len(li_text) > len(company_name) + 2
                        else []
                    )
                # name is in bracket. separate ,
                row = {
                    "prefecture": prefecture,
                    "company_url": href,
                    "company_name": company_name,
                    "supermarket_names": supermarket_names,
                }
                rows.append(row)
    except requests.exceptions.RequestException as e:
        print(f"エラーが発生しました: {e}")
    return rows


# 一般社団法人日本スーパーマーケット協会 (JSA) 通常会員


def jsa():
    rows = []
    url = "http://www.jsa-net.gr.jp/kaiin/ithiran.html"
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
        soup = BeautifulSoup(response.content.decode("utf-8", "ignore"), "html.parser")
        prefecture_elements = soup.select(".main > h4")
        for prefecture_element in prefecture_elements:
            prefecture = prefecture_element.find("img").get("alt")
            company = prefecture_element.find_next_sibling().find("a")
            company_name = company.get_text()
            href = company.get("href")
            supermarket_names = []
            row = {
                "prefecture": prefecture,
                "company_url": href,
                "company_name": company_name,
                "supermarket_names": supermarket_names,
            }
            rows.append(row)
    except requests.exceptions.RequestException as e:
        print(f"エラーが発生しました: {e}")
    return rows


# オール日本スーパーマーケット協会 (AJS) 会員


def ajs():
    rows = []
    url = "https://www.ajs.gr.jp/main/wp-content/imgs/2025/10/listKAIIN_20251001.pdf"
    response = requests.get(url)

    with open("kaiin.pdf", "wb") as f:
        f.write(response.content)

    doc = pymupdf.open("kaiin.pdf")
    for page in doc:
        texts = list(
            filter(
                lambda s: not any(k in s for k in region.keys()),
                page.get_text().split("\n")[5:-1],
            )
        )
        links = [l["uri"] for l in page.get_links()]
        for i in range(len(texts)):
            row = {
                "company_url": links[i],
                "company_name": texts[i],
                "supermarket_names": [],
            }
            rows.append(row)

    os.remove("kaiin.pdf")
    return rows


# 日本チェーンストア協会 (JCSA) 通常会員


def jcsa():
    rows = []
    url = "https://www.jcsa.gr.jp/member/normal_temp"
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
        soup = BeautifulSoup(response.text, "html.parser")
        elements = soup.select("#main > div.sec-1 > div > ul > li > a")
        for e in elements:
            company_name = e.get_text()
            href = e.get("href")
            supermarket_names = []
            row = {
                "company_url": href,
                "company_name": company_name,
                "supermarket_names": supermarket_names,
            }
            rows.append(row)
    except requests.exceptions.RequestException as e:
        print(f"エラーが発生しました: {e}")
    return rows


# シジシージャパン (CGC) 加盟企業


def cgc():
    rows = []
    response = requests.get("https://www.cgcjapan.co.jp/cgcgroups/group/")
    response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
    soup = BeautifulSoup(response.text, "html.parser")
    urls = soup.select(
        "body > main > section > div.inner > div.map-block > div > ul > li > a"
    )

    for url in urls:
        response = requests.get("https://www.cgcjapan.co.jp" + url.get("href"))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        elements = soup.select(
            "body > main > section > div.inner > div.corp-block > ul > li > p > a"
        )
        for e in elements:
            company_name = e.get_text()
            href = e.get("href")
            supermarket_names = []
            row = {
                "company_url": href,
                "company_name": company_name,
                "supermarket_names": supermarket_names,
            }
            rows.append(row)
    return rows


# 日本流通産業加盟企業


def nichiryu():
    rows = []
    response = requests.get("https://www.nichiryu.co.jp/group/")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    elements = soup.select(
        "body > main > div > div > div > div > div > div > div.groupSec__inner__list > ul > li > a"
    )

    for e in elements:
        company_name = e.find("img").get("alt").split(" ")[0]
        href = e.get("href")
        supermarket_names = []
        row = {
            "company_url": href,
            "company_name": company_name,
            "supermarket_names": supermarket_names,
        }
        rows.append(row)
    return rows


# 協同組合セルコチェーン (セルコ) 会員企業


def selco():
    rows = []
    response = requests.get("https://www.nihonselco.com/member/")
    response.encoding = response.apparent_encoding
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    elements = soup.select("#main > div.indent > table > tr > td")

    for e in elements:
        if e.get_text().strip() != "" and any(
            k in e.get_text().strip() for k in sum(region.values(), [])
        ):
            company_name = e.get_text().strip()
            href = e.find("a").get("href") if e.find("a") is not None else ""
            supermarket_names = []
            row = {
                "company_url": href,
                "company_name": company_name,
                "supermarket_names": supermarket_names,
            }
            rows.append(row)
    return rows


rows = []
rows.extend(nsaj())
rows.extend(jsa())
rows.extend(ajs())
rows.extend(jcsa())
rows.extend(cgc())
rows.extend(nichiryu())
rows.extend(selco())
with open("data.json", "w") as f:
    json.dump(rows, f, indent=2)
