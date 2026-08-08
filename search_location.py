import json
import random
import re
import time
import unicodedata

from playwright.sync_api import sync_playwright

DATA_FILE = "data.json"
BASE_URL = "https://www.houjin-bangou.nta.go.jp/"

HEADERS_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


ENTITY_MAP = {
    "(株)": "株式会社",
    "(有)": "有限会社",
    "(名)": "合名会社",
    "(合)": "合資会社",
    "(財)": "財団法人",
    "(社)": "社団法人",
    "(学)": "学校法人",
}

ENTITY_SUFFIXES = [
    "株式会社",
    "有限会社",
    "合同会社",
    "合資会社",
    "合名会社",
    "社団法人",
    "財団法人",
    "医療法人",
    "相互会社",
    "学校法人",
]


def _base_name(name):
    """全角文字をNFKC正規化し、空白を除去して商号を返す"""
    cleaned = unicodedata.normalize("NFKC", name)
    cleaned = re.sub(r"[\s\u3000]", "", cleaned)
    return cleaned


def normalize_name(name):
    """法人格表記(㈱㈲や(株)(有)、株式会社等)と末尾の括弧書きを除去し、商号を返す（検索用）"""
    cleaned = _base_name(name)
    cleaned = re.sub(r"[（(](株|有|名|合|財|社|学)[）)]", "", cleaned)
    for suffix in ENTITY_SUFFIXES:
        cleaned = cleaned.replace(suffix, "")
    cleaned = re.sub(r"\([^)]*\)$", "", cleaned)
    return cleaned


def normalize_name_with_entity(name):
    """法人格を正式表記に揃えて末尾に置き、空白・全角文字も正規化して商号を返す（比較用）

    株式会社福原と福原株式会社は同一視されるが、
    福原株式会社と福原有限会社は区別される。
    """
    cleaned = _base_name(name)
    for short, full in ENTITY_MAP.items():
        cleaned = cleaned.replace(short, full)
    cleaned = re.sub(r"\([^)]*\)$", "", cleaned)
    for suffix in ENTITY_SUFFIXES:
        if cleaned.startswith(suffix):
            cleaned = cleaned[len(suffix) :] + suffix
    return cleaned


def get_name_text(cell):
    """td要素からフリガナ(div.furigana)を除いた商号テキストを返す"""
    return cell.evaluate(
        "el => { const c = el.cloneNode(true); const f = c.querySelector('.furigana'); if (f) f.remove(); return c.innerText; }"
    )


def search_location(page, company_name, prefecture):
    """法人番号公表サイトで検索し、正規化後の商号と都道府県が完全一致する所在地の一覧を返す"""
    query = normalize_name(company_name)
    query_with_entity = normalize_name_with_entity(company_name)

    # ホーム画面に戻って検索（トークンを毎回取得）
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.fill("#corp_name", query)
    page.select_option("#addr_pref", label=prefecture)
    page.click("#search_condition")
    page.wait_for_url("**/kensaku-kekka.html*", timeout=30000)
    page.wait_for_timeout(1000)

    rows = page.locator("table tr:has(td)")
    matches = []
    for i in range(rows.count()):
        tds = rows.nth(i).locator("td")
        if tds.count() < 2:
            continue
        name_cell = tds.nth(0)
        address = tds.nth(1).inner_text().strip()
        if (
            normalize_name_with_entity(get_name_text(name_cell)) == query_with_entity
            and address.startswith(prefecture)
        ):
            matches.append(address)
    return matches


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=HEADERS_UA)
        page = context.new_page()

        no_result = []
        multiple_matches = []
        errors = []
        done = 0
        for item in data:
            company_name = item.get("company_name", "")
            prefecture = item.get("prefecture", "")
            if item.get("location"):
                print(f"[スキップ] {company_name}")
                continue
            if not company_name or not prefecture:
                print(f"[スキップ] 情報不足: {company_name}")
                continue

            print(f"=== {company_name} ({prefecture}) ===")
            try:
                matches = search_location(page, company_name, prefecture)
                if len(matches) == 1:
                    item["location"] = matches[0]
                    print(f"  所在地: {matches[0]}")
                elif len(matches) == 0:
                    item["location"] = None
                    no_result.append((company_name, prefecture))
                else:
                    item["location"] = None
                    multiple_matches.append((company_name, prefecture, matches))
            except Exception as e:
                print(f"  エラー: {e}")
                item["location"] = None
                errors.append((company_name, prefecture, str(e)))

            done += 1
            # 連続アクセスを避けるため待機
            time.sleep(random.uniform(1.5, 3.0))

        browser.close()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n完了: {done} 件を処理しました。")

    print("\n=== 結果なし（0件） ===")
    for company_name, prefecture in no_result:
        print(f"  {company_name} ({prefecture})")

    print("\n=== 複数件マッチ ===")
    for company_name, prefecture, matches in multiple_matches:
        print(f"  {company_name} ({prefecture})")
        for address in matches:
            print(f"    {address}")

    if errors:
        print("\n=== エラー ===")
        for company_name, prefecture, message in errors:
            print(f"  {company_name} ({prefecture}): {message}")


if __name__ == "__main__":
    main()
