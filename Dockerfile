FROM node:22-bookworm

# The YKVS assistant uses Node.js for the web server and Python for the MCP school-data server.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node dependencies first for better Docker layer caching.
COPY package*.json ./
RUN npm install --omit=dev

# Install the Python MCP dependency.
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy the project.
COPY . .

ENV NODE_ENV=production
ENV PYTHON_BIN=python3

EXPOSE 10000

CMD ["node", "backend-node/server.js"]
