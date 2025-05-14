# 1) Builder stage on Debian to compile native modules
FROM node:18-slim AS builder

WORKDIR /app

# Install build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy package files & install
COPY package.json package-lock.json ./
RUN npm ci

# Copy your source
COPY . .

# Rebuild any native modules
RUN npm rebuild

# 2) Slim runtime stage
FROM node:18-slim

WORKDIR /app

# Copy only what's needed from builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json  ./package.json
COPY --from=builder /app/index.js      ./index.js
COPY --from=builder /app/routes        ./routes
COPY --from=builder /app/services      ./services
COPY --from=builder /app/model         ./model

# (Optional) Install nodemon globally for dev/debug
RUN npm install -g nodemon

# Use non-root user
RUN groupadd -r app && useradd --no-log-init -r -g app app
USER app

EXPOSE 3000

# Production start; override to `nodemon index.js` for local dev
CMD [ "node", "index.js" ]
