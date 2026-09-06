import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:frontend_flutter/services/auth_service.dart';
import 'package:frontend_flutter/services/token_storage.dart';
import 'package:frontend_flutter/utils/constants.dart';

/// 统一 API 服务 —— 带 JWT 认证拦截器的 Dio 单例
///
/// 拦截器职责：
/// 1. 请求前自动注入 Authorization: Bearer `accessToken`
/// 2. 收到 401 时自动用 refreshToken 刷新，重试原请求（最多 1 次）
/// 3. 刷新失败时清除本地 Token，通知 UI 层跳转登录
class ApiService {
  static final Dio _dio = _createDio();

  /// 供 Coach 等服务复用带 JWT 拦截器的 Dio 实例
  static Dio get dio => _dio;

  /// 供外部监听认证失效（刷新也失败 → 跳转登录页）
  static void Function()? onAuthExpired;

  static Dio _createDio() {
    final dio = Dio(BaseOptions(
      baseUrl: Constants.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
    ));

    // ── 请求拦截器：注入 Bearer Token ──
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = TokenStorage.accessToken;
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        // 不是 401 或不是服务端请求 → 直接抛出
        if (error.response?.statusCode != 401 ||
            error.requestOptions.headers.containsKey('X-Retry')) {
          return handler.next(error);
        }

        // ── 401 自动刷新逻辑 ──
        if (kDebugMode) print('[ApiService] 收到 401，尝试刷新 Token...');
        final newToken = await AuthService.tryRefresh();

        if (newToken != null) {
          // 刷新成功：更新请求头并重试
          final retryOpts = error.requestOptions;
          retryOpts.headers['Authorization'] = 'Bearer $newToken';
          retryOpts.headers['X-Retry'] = '1'; // 标记已重试，防止死循环
          try {
            final retryResp = await _dio.fetch(retryOpts);
            return handler.resolve(retryResp);
          } catch (e) {
            return handler.next(e is DioException ? e : DioException(
              requestOptions: retryOpts, error: e));
          }
        }

        // 刷新失败 → 清除 Token → 通知登录
        if (kDebugMode) print('[ApiService] Token 刷新失败，跳转登录');
        await TokenStorage.clear();
        onAuthExpired?.call();
        handler.next(error);
      },
    ));

    return dio;
  }

  /// 上传音频字节数据，后端建面试记录，返回 interview_id
  static Future<Map<String, dynamic>> uploadAudioBytes(Uint8List bytes) async {
    try {
      FormData formData = FormData.fromMap({
        "audioFile": MultipartFile.fromBytes(bytes, filename: 'recording.wav'),
      });
      Response resp = await _dio.post(Constants.uploadAudioApi, data: formData);
      return resp.data as Map<String, dynamic>;
    } catch (e) {
      if (kDebugMode) print("上传音频异常：$e");
      rethrow;
    }
  }

  /// 触发指定面试的复盘分析（全链路编排；进度经 WS 推送）
  static Future<Map<String, dynamic>> analyzeInterview(int interviewId) async {
    Response resp = await _dio.post('${Constants.interviewAnalyzeApi}/$interviewId/analyze');
    return resp.data as Map<String, dynamic>;
  }

  /// 获取面试报告正文（Markdown）
  static Future<String> getReportContent(int interviewId) async {
    Response resp = await _dio.get('${Constants.reportDetailApi}/$interviewId/report');
    return (resp.data as Map<String, dynamic>)['content'] as String? ?? '';
  }

  /// 获取面试记录详情
  static Future<Map<String, dynamic>> getInterviewDetail(int interviewId) async {
    Response resp = await _dio.get('${Constants.interviewDetailApi}/$interviewId');
    return resp.data as Map<String, dynamic>;
  }

  /// 获取历史面试记录列表
  static Future<Map<String, dynamic>> getRecordList() async {
    Response resp = await _dio.get(Constants.interviewListApi);
    return resp.data;
  }

  /// 获取报告列表（后端返回裸 list[ReportOut{interview_id, content, created_at}]）
  static Future<List<Map<String, dynamic>>> getReportList({int page = 1, int size = 20}) async {
    Response resp = await _dio.get(Constants.reportListApi, queryParameters: {
      'page': page, 'size': size,
    });
    final data = resp.data;
    if (data is List) {
      return data.cast<Map<String, dynamic>>();
    }
    if (data is Map && data['data'] is List) {
      return (data['data'] as List).cast<Map<String, dynamic>>();
    }
    return [];
  }

  /// 获取面试评测明细（含逐题得分）
  static Future<List<Map<String, dynamic>>> getEvaluations(int interviewId) async {
    Response resp = await _dio.get('${Constants.reportEvaluationsApi}/$interviewId/evaluations');
    final data = resp.data;
    if (data is List) {
      return data.cast<Map<String, dynamic>>();
    }
    return [];
  }

  /// 获取我的面试记录列表（裸 list[InterviewOut]）
  static Future<List<Map<String, dynamic>>> getInterviewList() async {
    Response resp = await _dio.get(Constants.interviewMyListApi);
    final data = resp.data;
    if (data is List) {
      return data.cast<Map<String, dynamic>>();
    }
    return [];
  }

  /// 获取用户个人信息
  static Future<Map<String, dynamic>> getUserProfile() async {
    Response resp = await _dio.get(Constants.userProfileApi);
    return resp.data;
  }

  /// 修改密码
  static Future<Map<String, dynamic>> updatePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    Response resp = await _dio.put(Constants.userPasswordApi, data: {
      'oldPassword': oldPassword,
      'newPassword': newPassword,
    });
    return resp.data;
  }
}
