import json
import yaml
import re
import time
import random
import urllib.parse
from playwright.sync_api import sync_playwright

with open("data.json", "r") as f:
   json_data = f.read()

def clean_company_name(name):
    """(株)や(有)などの法人格を取り除く関数"""
    cleaned = re.sub(r'\(株\)|\(有\)|\(名\)|\(合\)|\(財\)|\(社\)', '', name)
    return cleaned.strip()

def fetch_search_results(page, query):
    """
    【使い回しているpageオブジェクト】を受け取り、URL遷移して検索結果を返す関数
    """
    print(f"検索中: {query}")

    # 検索クエリをURLエンコードしてGoogle検索のURLを生成
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"

    # 同じタブ（page）のまま、新しい検索結果URLへ遷移
    page.goto(search_url, wait_until="domcontentloaded")
    page.wait_for_timeout(90000)

    # h3タグを含む親のaタグ（検索結果リンク）を取得
    links = page.locator("a:has(h3)")
    count = links.count()

    results = []
    # 上位10件を取得
    for i in range(min(count, 10)):
        loc = links.nth(i)
        title = loc.locator("h3").inner_text()
        href = loc.get_attribute("href")

        if href and href.startswith("http"):
            results.append({
                "title": title,
                "url": href
            })

    return results

def main():
    data = json.loads(json_data)
    final_results = []

    with sync_playwright() as p:
        # ==========================================
        # 1. Playwrightの初期化（ここで1度だけ立ち上げる）
        # ==========================================
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # この「page」オブジェクトを最後まで使い回す
        page = context.new_page()

        # ==========================================
        # 2. データの数だけURL遷移を繰り返す
        # ==========================================
        for item in data:
            # 検索ターゲット名の決定
            if item.get("supermarket_names") and len(item["supermarket_names"]) > 0:
                target_name = item["supermarket_names"][0]
            else:
                target_name = clean_company_name(item["company_name"])

            # 検索クエリの作成
            query = f'{target_name} テーマソング OR イメージソング OR 曲 OR BGM'

            try:
                # 使い回している「page」を渡してURL遷移を実行
                search_results = fetch_search_results(page, query)

                final_results.append({
                    "target_name": target_name,
                    "search_query": query,
                    "results": search_results
                })
            except Exception as e:
                print(f"[{target_name}] の検索中にエラーが発生しました: {e}")

            # ループの最後に待機時間を入れる（Googleの連続アクセス制限ブロック回避）
            sleep_time = random.uniform(2.0, 5.0)
            time.sleep(sleep_time)

        # ==========================================
        # 3. すべてのURL遷移が終わったらブラウザを閉じる
        # ==========================================
        browser.close()

    # 結果をYAMLファイルに保存
    output_filename = "supermarket_songs.yaml"
    with open(output_filename, "w", encoding="utf-8") as f:
        yaml.dump(final_results, f, allow_unicode=True, sort_keys=False)

    print(f"\n完了しました！ 結果は '{output_filename}' に保存されています。")

if __name__ == "__main__":
    main()
