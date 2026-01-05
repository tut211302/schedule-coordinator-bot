FROM mysql:8.0

# 日本語フォントと必要な設定
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 初期化スクリプトをコピー（存在する場合）
COPY db/init/*.sql /docker-entrypoint-initdb.d/ 2>/dev/null || true

EXPOSE 3306
