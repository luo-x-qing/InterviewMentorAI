import 'package:shared_preferences/shared_preferences.dart';

class TokenStorage {
  static const _keyAccess = 'jwt_access_token';
  static const _keyRefresh = 'jwt_refresh_token';

  static String? _accessToken;
  static String? _refreshToken;
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) return;
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString(_keyAccess);
    _refreshToken = prefs.getString(_keyRefresh);
    _initialized = true;
  }

  static String? get accessToken => _accessToken;
  static String? get refreshToken => _refreshToken;
  static bool get isLoggedIn => _accessToken != null && _accessToken!.isNotEmpty;

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

  static Future<void> updateAccessToken(String accessToken) async {
    _accessToken = accessToken;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccess, accessToken);
  }

  static Future<void> clear() async {
    _accessToken = null;
    _refreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyAccess);
    await prefs.remove(_keyRefresh);
  }
}
