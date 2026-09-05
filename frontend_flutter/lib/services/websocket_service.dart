import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'package:frontend_flutter/services/token_storage.dart';
import 'package:frontend_flutter/utils/constants.dart';

/// 面试分析状态枚举
enum AnalysisProgress {
  idle,        // 空闲
  uploading,   // 上传中
  processing,  // AI 分析中
  completed,   // 分析完成
  failed,      // 分析失败
}

/// 分析进度回调
typedef ProgressCallback = void Function(AnalysisProgress status, String? message);

/// 原生 WebSocket 服务 —— 订阅 AI 分析实时进度
///
/// 连接 Python 单后端（架构 AGENT-ARCHITECTURE.md §9.4）：
///   `ws://host/ws?token=<access>&subscribe=interview.{id}`
/// 推送消息体：`{"type": "interview.{id}.progress", "payload": {...}}`
///   type 后缀 `.progress` / `.complete` / `.error` → AnalysisProgress 状态机
class WebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _sub;

  AnalysisProgress _status = AnalysisProgress.idle;
  AnalysisProgress get status => _status;

  String? _lastMessage;
  String? get lastMessage => _lastMessage;

  ProgressCallback? onProgressChanged;

  bool _disposed = false;

  /// 连接到 WebSocket 并订阅指定面试的分析进度
  Future<void> connect(int interviewId) async {
    if (_disposed) return;

    await _close();

    final accessToken = TokenStorage.accessToken ?? '';
    final url = '${Constants.wsUrl}?token=$accessToken&subscribe=interview.$interviewId';
    if (kDebugMode) print('[WS] 连接: interview=$interviewId');

    _channel = WebSocketChannel.connect(Uri.parse(url));
    _sub = _channel!.stream.listen(
      (data) => _onMessage(data),
      onError: (err) {
        if (kDebugMode) print('[WS] 错误: $err');
      },
      onDone: () {
        if (kDebugMode) print('[WS] 连接关闭');
        _updateStatus(AnalysisProgress.idle, null);
      },
    );

    _updateStatus(AnalysisProgress.uploading, '正在上传音频...');
  }

  void _onMessage(dynamic data) {
    if (kDebugMode) print('[WS] 收到: $data');
    try {
      final map = jsonDecode(data as String) as Map<String, dynamic>;
      final type = map['type'] as String? ?? '';
      final payload = map['payload'] as Map<String, dynamic>? ?? const {};
      final message = payload['message'] as String?;

      if (type.endsWith('.progress')) {
        _updateStatus(AnalysisProgress.processing, message);
      } else if (type.endsWith('.complete')) {
        _updateStatus(AnalysisProgress.completed, message ?? '分析完成');
      } else if (type.endsWith('.error')) {
        _updateStatus(AnalysisProgress.failed, message ?? '分析失败');
      }
    } catch (e) {
      if (kDebugMode) print('[WS] 解析失败: $e');
    }
  }

  void _updateStatus(AnalysisProgress status, String? message) {
    _status = status;
    _lastMessage = message;
    onProgressChanged?.call(status, message);
  }

  Future<void> _close() async {
    await _sub?.cancel();
    _sub = null;
    await _channel?.sink.close();
    _channel = null;
  }

  /// 断开连接并清理资源
  void disconnect() {
    _updateStatus(AnalysisProgress.idle, null);
    _close();
    _status = AnalysisProgress.idle;
  }

  /// 释放所有资源（页面销毁时调用）
  void dispose() {
    _disposed = true;
    disconnect();
  }
}