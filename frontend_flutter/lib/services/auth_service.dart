import 'package:dio/dio.dart';
import 'package:frontend_flutter/services/token_storage.dart';
import 'package:frontend_flutter/utils/constants.dart';

class AuthService {
  static final Dio _dio = Dio(BaseOptions(
    baseUrl: Constants.baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 15),
    headers: {'Content-Type': 'application/json'},
  ));

  static Future<Map<String, dynamic>> login({
    required String phone,
    required String password,
  }) async {
    final resp = await _dio.post(Constants.loginApi, data: {
      'phone': phone,
      'password': password,
    });
    final data = _extractData(resp);
    await TokenStorage.save(
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
    );
    return <String, dynamic>{
      'id': data['user_id'],
      'phone': phone,
      'nickname': '',
    };
  }

  static Future<Map<String, dynamic>> register({
    required String phone,
    required String password,
    String? nickname,
  }) async {
    final body = <String, dynamic>{
      'phone': phone,
      'password': password,
    };
    if (nickname != null && nickname.isNotEmpty) body['nickname'] = nickname;

    final resp = await _dio.post(Constants.registerApi, data: body);
    final data = _extractData(resp);
    await TokenStorage.save(
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
    );
    return <String, dynamic>{
      'id': data['user_id'],
      'phone': phone,
      'nickname': nickname ?? '',
    };
  }

  static Future<String?> tryRefresh() async {
    final refresh = TokenStorage.refreshToken;
    if (refresh == null || refresh.isEmpty) return null;
    try {
      final resp = await _dio.post(Constants.refreshTokenApi, data: {
        'refresh_token': refresh,
      });
      final data = _extractData(resp);
      final newAccess = data['access_token'] as String;
      await TokenStorage.updateAccessToken(newAccess);
      return newAccess;
    } catch (_) {
      await TokenStorage.clear();
      return null;
    }
  }

  static Future<void> logout() async {
    await TokenStorage.clear();
  }

  static Map<String, dynamic> _extractData(Response resp) {
    // 后端 Python 单后端直接返回 payload（200=成功）
    return resp.data as Map<String, dynamic>;
  }
}
