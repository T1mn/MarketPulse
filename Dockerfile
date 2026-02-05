# MarketPulse Dockerfile - pnpm + bun runtime
FROM node:20-slim

# 配置 apt 使用阿里云镜像
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    libpango-1.0-0 libcairo2 fonts-liberation fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 安装 pnpm 和 bun
RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g pnpm bun

WORKDIR /app

# 复制 package 文件（移除 bun packageManager 声明，让 pnpm 可以工作）
COPY package.json pnpm-workspace.yaml turbo.json tsconfig.json ./
RUN sed -i '/"packageManager"/d' package.json
COPY packages/shared/package.json ./packages/shared/
COPY packages/core/package.json ./packages/core/
COPY packages/server/package.json ./packages/server/
COPY packages/web/package.json ./packages/web/
COPY packages/sdk/package.json ./packages/sdk/
COPY packages/cli/package.json ./packages/cli/
COPY packages/tui/package.json ./packages/tui/
COPY packages/desktop/package.json ./packages/desktop/

# 用 pnpm 安装依赖（hoisted 模式，完全平铺无 symlink）
RUN pnpm install --node-linker=hoisted --shamefully-hoist --registry=https://registry.npmmirror.com

# 复制源代码
COPY packages/ ./packages/

# 构建 Web 前端
RUN cd packages/web && pnpm exec vite build

# 创建数据目录
RUN mkdir -p /app/packages/core/data

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

CMD ["bun", "run", "packages/server/src/index.ts"]
