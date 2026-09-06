# ---- Stage 1: Flutter Web 构建 ----
FROM debian:bookworm-slim AS builder

# 生产构建注入 API 基址（与 lib/utils/constants.dart 的 API_BASE_URL 对应）：
#   docker build --build-arg API_BASE_URL=http://your-host
# 未传时回落 localhost:8000（本地开发模式）
ARG API_BASE_URL=http://localhost:8000

ENV FLUTTER_VERSION=3.29.2
ENV FLUTTER_URL=https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${FLUTTER_VERSION}-stable.tar.xz

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils git ca-certificates unzip \
    && rm -rf /var/lib/apt/lists/*

RUN echo "正在下载 Flutter SDK（约 1GB）..." \
    && curl -fsSL --retry 5 "$FLUTTER_URL" -o /tmp/flutter.tar.xz \
    && tar -xf /tmp/flutter.tar.xz -C /opt \
    && rm /tmp/flutter.tar.xz

ENV PATH="/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:$PATH"

RUN flutter config --no-analytics && dart --disable-analytics

WORKDIR /app
COPY pubspec.* /app/
RUN flutter pub get

COPY . /app/

# 构建 Flutter Web
RUN flutter build web --release --dart-define=API_BASE_URL=${API_BASE_URL}

# ---- Stage 2: nginx 伺服 ----
FROM nginx:alpine
COPY --from=builder /app/build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
