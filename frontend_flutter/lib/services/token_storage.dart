import 'package:shared_preferences/shared_preferences.dart';

/// JWT Token 持久化存储（SharedPreferences + 内存缓存）
///
/// 双 Token 机制：
/// - accessToken: 2 小时有效，每次请求通过 Dio 拦截器自动携带
/// - refreshToken: 7 天有效，accessToken 过期时自动刷新
class TokenStorage {
  static const _keyAccess = 'jwt_access_token';
  static const _keyRefresh = 'jwt_refresh_token';

  static String? _accessToken;
  static String? _refreshToken;
  static bool _initialized = false;

  /// 初始化：从磁盘恢复缓存的 Token
  static Future<void> init() async {
    if (_initialized) return;
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString(_keyAccess);
    _refreshToken = prefs.getString(_keyRefresh);
    _initialized = true;
  }

  /// 获取 Access Token（优先内存）
  static String? get accessToken => _accessToken;

  /// 获取 Refresh Token（优先内存）
  static String? get refreshToken => _refreshToken;

  /// 是否已登录
  static bool get isLoggedIn => _accessToken != null && _accessToken!.isNotEmpty;

  /// 保存双 Token（内存 + 磁盘）
  static Future<void> save({
    required String accessToken,
    required String refreshToken,
  }) async {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccess, accessToken);
    await prefs.setString(_keyRefresh, refreshToken);
  }

  /// 只更新 Access Token（刷新后调用）
  static Future<void> updateAccessToken(String accessToken) async {
    _accessToken = accessToken;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccess, accessToken);
  }

  /// 清除所有 Token（登出）
  static Future<void> clear() async {
    _accessToken = null;
    _refreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyAccess);
    await prefs.remove(_keyRefresh);
  }
}
