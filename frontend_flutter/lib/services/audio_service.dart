import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';

class AudioService {
  static final AudioRecorder _recorder = AudioRecorder();

  /// 获取本地存储路径
  static Future<String> getAudioSavePath() async {
    Directory appDir = await getApplicationDocumentsDirectory();
    String fileName = "${DateTime.now().millisecondsSinceEpoch}.wav";
    return path.join(appDir.path, fileName);
  }

  /// 请求麦克风权限
  static Future<bool> requestMicPermission() async {
    PermissionStatus status = await Permission.microphone.request();
    return status.isGranted;
  }

  /// 开始录音
  static Future<void> startRecord() async {
    bool hasPerm = await requestMicPermission();
    if (!hasPerm) {
      throw Exception("未授予麦克风权限");
    }
    String savePath = await getAudioSavePath();
    await _recorder.start(const RecordConfig(
      encoder: AudioEncoder.wav,
      sampleRate: 16000,
    ), path: savePath);
  }

  /// 停止录音，返回音频文件路径
  static Future<String?> stopRecord() async {
    String? filePath = await _recorder.stop();
    return filePath;
  }

  /// 销毁资源
  static void dispose() {
    _recorder.dispose();
  }
}
