import json
import re
import time
import random
from playwright.sync_api import sync_playwright

DATA_FILE = "data.json"
BASE_URL = "https://www.houjin-bangou.nta.go.jp/"

HEADERS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def clean_company_name(name):
    """㈱㈲や(株)(有)などの法人格表記と末尾の()を除いて検索用の商号を返す"""
    cleaned = re.sub(r"[㈱㈲]", "", name)
    cleaned = re.sub(r"[（(](株|有|名|合|財|社)[）)]", "", cleaned)
    cleaned = re.sub(r"[（(][^）)]*[）)]$", "", cleaned)
    return cleaned.strip()


def search_location(page, company_name, prefecture):
    """法人番号公表サイトで検索し、所在地を返す（見つからなければNone）"""
    query = clean_company_name(company_name)

    # ホーム画面に戻って検索（トークンを毎回取得）
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.fill("#corp_name", query)
    page.select_option("#addr_pref", label=prefecture)
    page.click("#search_condition")
    page.wait_for_url("**/kensaku-kekka.html*", timeout=30000)
    page.wait_for_timeout(1000)

    rows = page.locator("table tr:has(td)")
    count = rows.count()
    if count == 0:
        print(f"  結果なし: {query} ({prefecture})")
        return None

    # 先頭結果を基本としつつ、商号名と都道府県が一致する行を探す
    for i in range(count):
        tds = rows.nth(i).locator("td")
        if tds.count() < 2:
            continue
        name_cell = tds.nth(0).inner_text()
        address = tds.nth(1).inner_text().strip()
        normalized = re.sub(r"\s+", "", name_cell)
        if not normalized:
            continue
        if query in normalized or normalized in query:
            if address.startswith(prefecture):
                return address
            print(f"  都道府県不一致: {query} → {address}")

    # 名前が一致しなければ先頭の結果を採用
    tds = rows.nth(0).locator("td")
    address = tds.nth(1).inner_text().strip()
    if address.startswith(prefecture):
        return address
    print(f"  都道府県不一致（先頭結果）: {address}")
    return None


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=HEADERS_UA)
        page = context.new_page()

        done = 0
        for item in data:
            company_name = item.get("company_name", "")
            prefecture = item.get("prefecture", "")
            if "location" in item:
                print(f"[スキップ] {company_name}")
                continue
            if not company_name or not prefecture:
                print(f"[スキップ] 情報不足: {company_name}")
                continue

            print(f"=== {company_name} ({prefecture}) ===")
            try:
                address = search_location(page, company_name, prefecture)
                item["location"] = address
                if address:
                    print(f"  所在地: {address}")
            except Exception as e:
                print(f"  エラー: {e}")
                item["location"] = None

            done += 1
            # 連続アクセスを避けるため待機
            time.sleep(random.uniform(1.5, 3.0))

        browser.close()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n完了: {done} 件を処理しました。")


if __name__ == "__main__":
    main()
