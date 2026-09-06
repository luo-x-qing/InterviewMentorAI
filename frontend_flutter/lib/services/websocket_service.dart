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

/// Coach 即时点评回调（WS coach.{sessionId}.feedback → payload）
typedef CoachFeedbackCallback = void Function(Map<String, dynamic> payload);

/// 原生 WebSocket 服务 —— 订阅 AI 分析实时进度 + Coach 即时点评
///
/// 连接 Python 单后端（架构 AGENT-ARCHITECTURE.md §9.4）：
///   `ws://host/ws?token=<access>&subscribe=interview.{id},coach.{sessionId}`
/// 推送消息体：`{"type": "<topic>.<suffix>", "payload": {...}}`
///   interview.* → AnalysisProgress 状态机；coach.*.feedback → CoachFeedbackCallback
class WebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _sub;

  AnalysisProgress _status = AnalysisProgress.idle;
  AnalysisProgress get status => _status;

  String? _lastMessage;
  String? get lastMessage => _lastMessage;

  int _lastPercent = 0;
  int get lastPercent => _lastPercent;

  /// 本次连接订阅的 Coach 会话反馈回调（迭代模式：新连接覆盖旧回调）
  CoachFeedbackCallback? onCoachFeedback;

  ProgressCallback? onProgressChanged;

  bool _disposed = false;

  /// 连接到 WebSocket 并订阅指定面试的分析进度与 Coach 会话反馈
  Future<void> connect({
    int? interviewId,
    String? coachSessionId,
  }) async {
    if (_disposed) return;

    await _close();

    final topics = <String>[
      if (interviewId != null) 'interview.$interviewId',
      if (coachSessionId != null) 'coach.$coachSessionId',
    ];
    if (topics.isEmpty) return;

    final accessToken = TokenStorage.accessToken ?? '';
    final url = '${Constants.wsUrl}?token=$accessToken&subscribe=${topics.join(',')}';
    if (kDebugMode) print('[WS] 连接: ${topics.join(", ")}');

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

    if (interviewId != null) {
      _updateStatus(AnalysisProgress.uploading, '正在上传音频...');
    }
  }

  /// 兼容旧调用：仅订阅面试分析进度
  @Deprecated('使用 connect(interviewId:) 替代')
  Future<void> connectInterview(int interviewId) =>
      connect(interviewId: interviewId);

  void _onMessage(dynamic data) {
    if (kDebugMode) print('[WS] 收到: $data');
    try {
      final map = jsonDecode(data as String) as Map<String, dynamic>;
      final type = map['type'] as String? ?? '';
      final payload = map['payload'] as Map<String, dynamic>? ?? const {};

      // Coach 即时点评：coach.{sessionId}.feedback
      if (type.contains('.feedback')) {
        onCoachFeedback?.call(payload);
        return;
      }

      final message = payload['message'] as String?;
      if (type.endsWith('.progress')) {
        final percent = payload['percent'] as int? ?? _lastPercent;
        _lastPercent = percent;
        _updateStatus(AnalysisProgress.processing, message);
      } else if (type.endsWith('.complete')) {
        _lastPercent = 100;
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
    _lastPercent = 0;
  }

  /// 释放所有资源（页面销毁时调用）
  void dispose() {
    _disposed = true;
    disconnect();
  }
}