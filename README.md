# 英作文トレーニングアプリ

Streamlitを使用した英作文トレーニングアプリケーションです。

## セットアップ

### 1. 仮想環境の作成とアクティベート

```bash
# 仮想環境を作成
python -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate     # Windows
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. アプリケーションの実行

```bash
streamlit run app.py
```

## 使用方法

1. アプリケーションを起動すると、ブラウザで自動的に開きます
2. 例文番号を選択してトレーニングしたい例文を選びます
3. 空欄に適切な英単語を入力します
4. 「チェック」ボタンで正解を確認します
5. 必要に応じて「ヒント」や「正解をすべて表示」ボタンを使用します
6. 読み上げボタンで音声を聞くことができます

## ファイル構成

- `app.py` - メインアプリケーションファイル
- `data.yaml` - 教材データ（YAML形式）
- `requirements.txt` - 依存関係リスト
- `README.md` - このファイル

## データの管理

教材データは `data.yaml` ファイルで管理されています。新しい例文を追加する場合は、以下の形式で `data.yaml` に追加してください：

```yaml
lessons:
  - ja: "日本語の例文"
    en: "English example sentence"
    gaps: ["example", "sentence"]
```

## 仮想環境の終了

```bash
deactivate
```