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
    required String username,
    required String password,
  }) async {
    final body = <String, dynamic>{
      'username': username,
      'password': password,
    };
    final resp = await _dio.post(Constants.loginApi, data: body);
    final data = _extractData(resp);
    await TokenStorage.save(
      accessToken: data['accessToken'] as String,
      refreshToken: data['refreshToken'] as String,
    );
    return data['userInfo'] as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> register({
    required String username,
    required String password,
    String? nickname,
    String? email,
    String? phone,
  }) async {
    final body = <String, dynamic>{
      'username': username,
      'password': password,
    };
    if (nickname != null && nickname.isNotEmpty) body['nickname'] = nickname;
    if (email != null && email.isNotEmpty) body['email'] = email;
    if (phone != null && phone.isNotEmpty) body['phone'] = phone;

    final resp = await _dio.post(Constants.registerApi, data: body);
    final data = _extractData(resp);
    await TokenStorage.save(
      accessToken: data['accessToken'] as String,
      refreshToken: data['refreshToken'] as String,
    );
    return data['userInfo'] as Map<String, dynamic>;
  }

  static Future<String?> tryRefresh() async {
    final refresh = TokenStorage.refreshToken;
    if (refresh == null || refresh.isEmpty) return null;
    try {
      final resp = await _dio.post(Constants.refreshTokenApi, data: {
        'refreshToken': refresh,
      });
      final data = _extractData(resp);
      final newAccess = data['accessToken'] as String;
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
    final body = resp.data as Map<String, dynamic>;
    if (body['code'] != 200) {
      throw DioException(
        requestOptions: resp.requestOptions,
        message: body['message'] as String? ?? '请求失败',
      );
    }
    return body['data'] as Map<String, dynamic>;
  }
}
