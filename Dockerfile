FROM node:22-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

ENV NODE_ENV=production
ENV PYTHON_BIN=python3
ENV MCP_SERVER_DIR=/app

EXPOSE 10000

CMD ["node", "server.js"]
