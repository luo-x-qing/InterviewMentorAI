import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:stomp_dart_client/stomp_dart_client.dart';
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

/// STOMP WebSocket 服务 —— 订阅 AI 分析实时进度
///
/// 连接到 Java 后端的 STOMP Broker：
/// - /topic/interview/{id}/progress  — AI 分析进度推送
/// - /topic/interview/{id}/complete  — 分析完成推送
/// - /topic/interview/{id}/error     — 分析失败推送
class WebSocketService {
  StompClient? _client;
  Timer? _reconnectTimer;
  StreamSubscription? _progressSub;
  StreamSubscription? _completeSub;
  StreamSubscription? _errorSub;

  AnalysisProgress _status = AnalysisProgress.idle;
  AnalysisProgress get status => _status;

  String? _lastMessage;
  String? get lastMessage => _lastMessage;

  ProgressCallback? onProgressChanged;

  bool _disposed = false;

  /// 连接到 WebSocket 并订阅指定面试的分析进度
  Future<void> connect(int interviewId) async {
    if (_disposed) return;

    _client?.deactivate();
    _client = StompClient(
      config: StompConfig(
        url: Constants.wsUrl,
        onConnect: (frame) {
          if (kDebugMode) print('[WS] STOMP 连接成功');

          // 订阅进度
          _progressSub = _client!.subscribe(
            destination: '/topic/interview/$interviewId/progress',
            callback: (frame) {
              final body = _parseBody(frame.body);
              _updateStatus(AnalysisProgress.processing, body);
            },
          );

          // 订阅完成
          _completeSub = _client!.subscribe(
            destination: '/topic/interview/$interviewId/complete',
            callback: (frame) {
              final body = _parseBody(frame.body);
              _updateStatus(AnalysisProgress.completed, body);
            },
          );

          // 订阅错误
          _errorSub = _client!.subscribe(
            destination: '/topic/interview/$interviewId/error',
            callback: (frame) {
              final body = _parseBody(frame.body);
              _updateStatus(AnalysisProgress.failed, body);
            },
          );
        },
        onWebSocketError: (error) {
          if (kDebugMode) print('[WS] WebSocket 错误: $error');
        },
        onStompError: (frame) {
          if (kDebugMode) print('[WS] STOMP 错误: ${frame.body}');
        },
        onDisconnect: (frame) {
          if (kDebugMode) print('[WS] 连接断开');
        },
        // 心跳间隔 10s
        heartbeatOutgoing: const Duration(seconds: 10),
        heartbeatIncoming: const Duration(seconds: 10),
      ),
    );

    _client!.activate();
    _updateStatus(AnalysisProgress.uploading, '正在上传音频...');
  }

  void _updateStatus(AnalysisProgress status, String? message) {
    _status = status;
    _lastMessage = message;
    onProgressChanged?.call(status, message);
  }

  String? _parseBody(String? body) {
    if (body == null) return null;
    try {
      final map = jsonDecode(body) as Map<String, dynamic>;
      return map['message'] as String? ?? body;
    } catch (_) {
      return body;
    }
  }

  /// 断开连接并清理资源
  void disconnect() {
    _progressSub?.cancel();
    _completeSub?.cancel();
    _errorSub?.cancel();
    _client?.deactivate();
    _client = null;
    _status = AnalysisProgress.idle;
  }

  /// 释放所有资源（页面销毁时调用）
  void dispose() {
    _disposed = true;
    disconnect();
  }
}
