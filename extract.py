import yaml
import requests
from bs4 import BeautifulSoup
import ollama

# 1. サンプルYAMLデータの定義（ファイルから読み込む場合は open('data.yaml') を利用）

output_filename = "supermarket_songs.yaml"
with open(output_filename, "r", encoding="utf-8") as f:
    yaml_data = f.read()

# 使用するOllamaモデル名（ローカルにダウンロードされているモデルを指定）
OLLAMA_MODEL = "qwen3.5:9b"  # 例: 'qwen2.5', 'gemma2', 'mistral' など


def fetch_page_text(url: str) -> str:
    """URLからHTMLを取得し、本文テキストのみを抽出する（文字化け・アクセスブロック対策込み）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # エンコーディング自動判定の修正
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # スクリプトやスタイルシートなどを除去
        for element in soup(["script", "style", "noscript", "header", "footer"]):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # トークン節約のため、テキストを長すぎる場合は1500文字程度にカット
        #        return text[:1500]
        return text
    except Exception as e:
        print(f"  [エラー] {url} の取得に失敗しました: {e}")
        return ""


def fetch_html(url: str) -> str:
    """URLからHTMLをそのまま取得する（URL探索用。トークン節約のため先頭のみ保持）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text[:30000]
    except Exception as e:
        print(f"  [エラー] {url} のHTML取得に失敗しました: {e}")
        return ""


def find_song_name(
    target_name: str, url: str, text_content: str, ai_overview: str = ""
):
    """Ollamaに曲名の有無だけを判定させる。見つかれば曲名、なければNoneを返す"""
    prompt = f"""
以下は「{target_name}」に関するWebページのテキストと、検索時のAI概要です。
この中に{target_name}のテーマソング・イメージソング・BGM・店内で流れる曲などの「曲名」が記載されていますか？
※AI概要はあくまで参考情報であり、ページテキストに記載がなくてもAI概要内に明確な曲名があれば採用してください。

【対象URL】: {url}
【AI概要（参考情報）】:
{ai_overview if ai_overview else "（なし）"}

【ページテキスト】:
{text_content}

【指示】:
- 曲名が見つかった場合: 「曲名: <曲名>」とだけ1行で出力してください。
- 見つからない場合: 「該当なし」とだけ出力してください。
- 余計な解説・改行は不要です。
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": "あなたは与えられたテキストから正確に情報を抽出するアシスタントです。",
            },
            {"role": "user", "content": prompt},
        ],
    )
    content = response["message"]["content"].strip()
    if "該当なし" in content:
        return None
    if "曲名:" in content:
        return content.split("曲名:", 1)[1].strip().splitlines()[0].strip()
    return content


def find_song_url(target_name: str, song_name: str, html_content: str):
    """OllamaにHTMLを食わせ、曲の音源・動画が格納されたURLを探させる"""
    prompt = f"""
以下は「{target_name}」のWebページのHTMLです。
{target_name}のテーマソング「{song_name}」の音源・動画が格納されたURL（オーディオファイル、YouTube、配信サイト、画像化された歌詞ページなど）を探してください。

【HTML】:
{html_content}

【指示】:
- 該当するURLが見つかった場合: 「URL: <url>」とだけ1行で出力してください。
- 見つからない場合: 「該当なし」とだけ出力してください。
- 余計な解説・改行は不要です。
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": "あなたは与えられたHTMLから正確にURLを抽出するアシスタントです。",
            },
            {"role": "user", "content": prompt},
        ],
    )
    content = response["message"]["content"].strip()
    if "URL:" in content:
        return content.split("URL:", 1)[1].strip().splitlines()[0].strip()
    return content


def main():
    # YAMLのパース
    items = yaml.safe_load(yaml_data)

    for item in items:
        target_name = item.get("target_name", "")
        ai_overview = item.get("ai_overview", "") or ""
        results = item.get("results", [])

        print(f"=== 対象: {target_name} ===")

        for result in results:
            title = result.get("title")
            url = result.get("url")

            print(f"\nアクセス中: {title} ({url})")

            # 1. ページテキストの取得
            page_text = fetch_page_text(url)

            if not page_text:
                print("  -> テキストを取得できなかったためスキップします。")
                continue

            # 2. 曲名の有無を判定（AI概要も参考にさせる）
            song_name = find_song_name(target_name, url, page_text, ai_overview)

            if not song_name:
                print("  -> 曲名が見つかりませんでした。")
                continue

            print(f"  -> 曲名ヒット: {song_name}")

            # 3. ヒットした場合のみHTMLを取得してURLを探索
            html = fetch_html(url)

            if not html:
                print("  -> HTMLを取得できなかったためスキップします。")
                continue

            url_result = find_song_url(target_name, song_name, html)

            print("--- URL抽出結果 ---")
            print(url_result)


if __name__ == "__main__":
    main()
