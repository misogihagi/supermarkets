import html
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
    "海外",
]


class SuperMarket:
    prefecture: Prefecture
    company_name: str
    company_url: str
    belong_to: str  # 加盟企業もしくはグループ企業
    supermarket_names: list[str]
    songs: list[str]


ALL_PREFECTURES = [
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

PREFECTURE_MAP = {p[:-1]: p for p in ALL_PREFECTURES}
PREFECTURE_MAP["北海道"] = "北海道"

# 住所が県名ではなく都市名始まりの場合の逆引きマップ（県庁所在地・政令指定都市）
CITY_PREFECTURE_MAP = {
    "札幌市": "北海道",
    "青森市": "青森県",
    "盛岡市": "岩手県",
    "仙台市": "宮城県",
    "秋田市": "秋田県",
    "山形市": "山形県",
    "福島市": "福島県",
    "水戸市": "茨城県",
    "宇都宮市": "栃木県",
    "前橋市": "群馬県",
    "さいたま市": "埼玉県",
    "千葉市": "千葉県",
    "横浜市": "神奈川県",
    "川崎市": "神奈川県",
    "相模原市": "神奈川県",
    "新潟市": "新潟県",
    "富山市": "富山県",
    "金沢市": "石川県",
    "福井市": "福井県",
    "甲府市": "山梨県",
    "長野市": "長野県",
    "岐阜市": "岐阜県",
    "静岡市": "静岡県",
    "浜松市": "静岡県",
    "名古屋市": "愛知県",
    "津市": "三重県",
    "大津市": "滋賀県",
    "京都市": "京都府",
    "大阪市": "大阪府",
    "堺市": "大阪府",
    "神戸市": "兵庫県",
    "奈良市": "奈良県",
    "和歌山市": "和歌山県",
    "鳥取市": "鳥取県",
    "松江市": "島根県",
    "岡山市": "岡山県",
    "広島市": "広島県",
    "山口市": "山口県",
    "徳島市": "徳島県",
    "高松市": "香川県",
    "松山市": "愛媛県",
    "高知市": "高知県",
    "北九州市": "福岡県",
    "福岡市": "福岡県",
    "佐賀市": "佐賀県",
    "長崎市": "長崎県",
    "熊本市": "熊本県",
    "大分市": "大分県",
    "宮崎市": "宮崎県",
    "鹿児島市": "鹿児島県",
    "那覇市": "沖縄県",
}


def prefecture_from_address(address):
    """県名を含む住所から都道府県を返す（最初に現れる県名を優先、都市名始まりは逆引き）"""
    matches = [
        (address.find(pref), pref) for pref in ALL_PREFECTURES if pref in address
    ]
    if matches:
        return min(matches)[1]
    city_matches = [
        (address.find(city), pref)
        for city, pref in CITY_PREFECTURE_MAP.items()
        if city in address
    ]
    if city_matches:
        return min(city_matches)[1]
    return None


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

AJS_MEMBER_PDF = (
    "https://www.ajs.gr.jp/main/wp-content/imgs/2021/04/listKAIIN_20260401.pdf"
)


def ajs():
    rows = []
    # 協会概要ページから最新の会員一覧PDFを探す
    url = AJS_MEMBER_PDF
    try:
        response = requests.get("https://www.ajs.gr.jp/contents/")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        link = soup.find("a", href=re.compile(r"listKAIIN.*\.pdf"))
        if link is not None:
            url = link["href"]
    except requests.exceptions.RequestException:
        pass

    response = requests.get(url)
    response.raise_for_status()

    with open("kaiin.pdf", "wb") as f:
        f.write(response.content)

    doc = pymupdf.open("kaiin.pdf")
    for page in doc:
        lines = []
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                text = "".join(span["text"] for span in line["spans"]).strip()
                if text:
                    lines.append({"bbox": line["bbox"], "text": text})

        # リンク矩形の座標から対応する商号行を特定して社名・都道府県を取得
        for link in page.get_links():
            uri = link.get("uri")
            if uri is None:
                continue
            from_rect = link["from"]
            matched = None
            for entry in lines:
                x0, y0, x1, y1 = entry["bbox"]
                if (
                    y0 - 1 <= from_rect.y0 <= y1 + 1
                    and x0 - 1 <= from_rect.x0 <= x1 + 1
                ):
                    matched = entry["text"]
                    break
            if matched is None:
                continue
            m = re.match(r"^(?P<name>.+?)[（(](?P<pref>[^）)]+)[）)]$", matched)
            if m is None:
                continue
            prefecture = PREFECTURE_MAP.get(m.group("pref"), "海外")
            row = {
                "prefecture": prefecture,
                "company_url": uri,
                "company_name": m.group("name"),
                "supermarket_names": [],
            }
            rows.append(row)

    doc.close()
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
            # title属性に〒から始まる本社住所が入っている
            title = html.unescape(e.get("title") or "")
            m = re.search(r"〒[\d\-]+\s*(.+)", title)
            prefecture = None
            if m is not None:
                address = re.sub(r"^[\s\u3000]+", "", m.group(1))
                for pref in ALL_PREFECTURES:
                    if address.startswith(pref):
                        prefecture = pref
                        break
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
        # h4.sub-ttlのspanに都道府県名、直後のcorp-blockに企業リストが入っている
        for h4 in soup.select("main h4.sub-ttl"):
            prefecture = PREFECTURE_MAP.get(
                h4.select_one("span").get_text(strip=True), "海外"
            )
            corp_block = h4.find_next_sibling("div", class_="corp-block")
            if corp_block is None:
                continue
            elements = corp_block.select("ul > li > p > a")
            for e in elements:
                company_name = e.get_text()
                href = e.get("href")
                supermarket_names = []
                row = {
                    "prefecture": prefecture,
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
        # alt属性は「商号 本社住所」の形式
        alt = e.find("img").get("alt")
        company_name = alt.split(" ")[0]
        href = e.get("href")
        supermarket_names = []
        row = {
            "prefecture": prefecture_from_address(alt),
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
    table = soup.select_one("#main > div.indent > table")
    if table is None:
        return rows

    # 各行の先頭セルに都道府県名（rowspan継続行にはなし）が入っている
    prefecture = None
    for tr in table.select("tr"):
        tds = tr.select("td")
        if not tds:
            continue
        first = tds[0].get_text().strip()
        if first in PREFECTURE_MAP:
            prefecture = PREFECTURE_MAP[first]
            company_cells = tds[1:]
        else:
            company_cells = tds
        for cell in company_cells:
            company_name = cell.get_text().strip()
            if not company_name:
                continue
            href = cell.find("a").get("href") if cell.find("a") is not None else ""
            supermarket_names = []
            row = {
                "prefecture": prefecture,
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
    json.dump(rows, f, indent=2, ensure_ascii=False)
