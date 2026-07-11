import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:frontend_flutter/utils/constants.dart';

class ApiService {
  static final Dio _dio = Dio(BaseOptions(
    baseUrl: Constants.baseUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
  ));

  /// 上传音频文件，交给后端AI分析
  static Future<Map<String, dynamic>> uploadAudioFile(String filePath) async {
    try {
      FormData formData = FormData.fromMap({
        "audioFile": await MultipartFile.fromFile(filePath),
      });
      Response resp = await _dio.post(Constants.uploadAudioApi, data: formData);
      return resp.data;
    } catch (e) {
      if (kDebugMode) {
        print("上传音频异常：$e");
      }
      rethrow;
    }
  }

  /// 获取历史面试记录列表（预留接口）
  static Future<Map<String, dynamic>> getRecordList() async {
    Response resp = await _dio.get(Constants.recordListApi);
    return resp.data;
  }
}
