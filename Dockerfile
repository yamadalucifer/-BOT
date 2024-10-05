# Pythonのベースイメージを使用
FROM python:3.9-slim

# 必要な依存関係をインストール
RUN apt-get update && apt-get install -y ffmpeg

# 作業ディレクトリを設定
WORKDIR /app

# 必要なPythonパッケージをインストール
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコンテナにコピー
COPY . /app

# ボットを実行するスタートコマンド
CMD ["python", "bot.py"]

