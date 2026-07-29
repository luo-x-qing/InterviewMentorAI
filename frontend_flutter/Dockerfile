FROM debian:bookworm-slim

ENV FLUTTER_VERSION=3.29.2
ENV FLUTTER_URL=https://storage.flutter-io.cn/flutter_infra_release/releases/stable/linux/flutter_linux_${FLUTTER_VERSION}-stable.tar.xz
ENV PUB_HOSTED_URL=https://pub.flutter-io.cn
ENV FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils git ca-certificates unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "$FLUTTER_URL" -o /tmp/flutter.tar.xz \
    && tar -xf /tmp/flutter.tar.xz -C /opt \
    && rm /tmp/flutter.tar.xz

ENV PATH="/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:$PATH"

RUN flutter config --no-analytics \
    && dart --disable-analytics \
    && flutter precache --no-android --no-ios --no-web --no-linux --no-windows --no-fuchsia --no-macos

WORKDIR /app

COPY pubspec.* /app/
RUN flutter pub get

COPY . /app/

ENTRYPOINT ["flutter"]
CMD ["--help"]
