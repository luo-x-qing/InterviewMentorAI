import 'package:shared_preferences/shared_preferences.dart';

/// 题库收藏服务 —— 基于 SharedPreferences 本地持久化
class FavoriteService {
  static const _key = 'favorite_question_ids';

  /// 获取所有收藏的题目 ID 集合
  static Future<Set<String>> getFavorites() async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_key) ?? [];
    return list.toSet();
  }

  /// 切换收藏状态，返回切换后的状态
  static Future<bool> toggle(String questionId) async {
    final favorites = await getFavorites();
    if (favorites.contains(questionId)) {
      favorites.remove(questionId);
    } else {
      favorites.add(questionId);
    }
    await _save(favorites);
    return favorites.contains(questionId);
  }

  /// 检查某题是否已收藏
  static Future<bool> isFavorite(String questionId) async {
    final favorites = await getFavorites();
    return favorites.contains(questionId);
  }

  /// 批量加载收藏状态到题目列表
  static Future<void> syncFavorites(List<dynamic> questions) async {
    final favorites = await getFavorites();
    for (final q in questions) {
      if (q.id != null) {
        (q as dynamic).isFavorite = favorites.contains(q.id as String);
      }
    }
  }

  static Future<void> _save(Set<String> ids) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_key, ids.toList());
  }
}
