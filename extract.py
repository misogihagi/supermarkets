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

        soup = BeautifulSoup(response.text, 'html.parser')

        # スクリプトやスタイルシートなどを除去
        for element in soup(["script", "style", "noscript", "header", "footer"]):
            element.decompose()

        text = soup.get_text(separator=' ', strip=True)
        # トークン節約のため、テキストを長すぎる場合は1500文字程度にカット
#        return text[:1500]
        return text
    except Exception as e:
        print(f"  [エラー] {url} の取得に失敗しました: {e}")
        return ""

def analyze_with_ollama(target_name: str, url: str, text_content: str):
    """Ollamaを使用してテキストの中からテーマソング情報を分析・抽出する"""
    prompt = f"""
以下のWebページテキストから、「{target_name}」のテーマソング（イメージソング、BGM、曲）の名前を探してください。

【対象URL】: {url}
【ページテキスト】:
{text_content}

【指示】:
1. テーマソング・イメージソングなどの曲名が見つかった場合は、その「曲名」と「曲の音源が格納されたURL」を出力してください。
2. 見つからなかった場合は「該当なし」と回答してください。
3. 余計な解説は不要です。以下のフォーマットのみで回答してください。

曲名: <見つかった曲名、または該当なし>
曲の音源が格納されたURL: 
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": "あなたは与えられたテキストから正確に情報を抽出するアシスタントです。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response['message']['content']

def main():
    # YAMLのパース
    items = yaml.safe_load(yaml_data)

    for item in items:
        target_name = item.get("target_name", "")
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

            # 2. Ollamaによる解析
            analysis_result = analyze_with_ollama(target_name, url, page_text)

            print("--- Ollamaの抽出結果 ---")
            print(analysis_result)

if __name__ == "__main__":
    main()
