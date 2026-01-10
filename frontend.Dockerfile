FROM node:18-slim

WORKDIR /workspace

# npm依存関係をインストール
COPY package*.json ./
RUN npm install

# ソースコードをコピー
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
