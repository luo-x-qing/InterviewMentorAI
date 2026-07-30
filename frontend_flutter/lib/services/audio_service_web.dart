import 'dart:async';
import 'dart:html' as html;
import 'dart:typed_data';

class AudioService {
  static html.MediaRecorder? _recorder;
  static List<html.Blob>? _chunks;
  static html.MediaStream? _stream;

  /// 上一次权限请求失败的详细原因
  static String? lastError;

  /// 请求麦克风权限（浏览器原生弹窗：允许 / 应用使用时允许 / 拒绝）
  static Future<bool> requestMicPermission() async {
    lastError = null;
    final devices = html.window.navigator.mediaDevices;
    if (devices == null) {
      lastError = '浏览器不支持麦克风访问（页面不在安全上下文中）';
      return false;
    }

    if (_stream != null) return true;

    try {
      _stream = await devices.getUserMedia({'audio': true});
      return true;
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('NotFoundError')) {
        lastError = '未检测到麦克风设备，请检查麦克风连接和系统设置';
      } else if (msg.contains('NotAllowedError')) {
        lastError = '麦克风权限被拒绝，请在浏览器设置中允许麦克风访问';
      } else if (msg.contains('NotReadableError')) {
        lastError = '麦克风被其他应用占用，请关闭其他使用麦克风的程序';
      } else {
        lastError = '请求麦克风失败: $e';
      }
      return false;
    }
  }

  static Future<void> startRecord() async {
    _chunks = [];
    if (_stream == null) {
      final devices = html.window.navigator.mediaDevices;
      if (devices == null) throw Exception('浏览器不支持麦克风访问');
      _stream = await devices.getUserMedia({'audio': true});
    }
    _recorder = html.MediaRecorder(_stream!);
    _recorder!.addEventListener('dataavailable', (Object event) {
      final e = event as html.BlobEvent;
      final data = e.data;
      if (data != null && data.size > 0) _chunks!.add(data);
    });
    _recorder!.start();
  }

  static Future<Uint8List?> stopRecord() async {
    final completer = Completer<Uint8List?>();
    _recorder!.addEventListener('stop', (Object event) async {
      final blob = html.Blob(_chunks!, 'audio/webm');
      final reader = html.FileReader();
      reader.addEventListener('load', (Object e) {
        completer.complete(reader.result as Uint8List?);
      });
      reader.readAsArrayBuffer(blob);
      _chunks = null;
      _recorder = null;
    });
    _recorder!.stop();
    _stream?.getTracks().forEach((t) => t.stop());
    _stream = null;
    return completer.future;
  }

  static void dispose() {
    _stream?.getTracks().forEach((t) => t.stop());
    _recorder = null;
    _chunks = null;
    _stream = null;
  }
}
