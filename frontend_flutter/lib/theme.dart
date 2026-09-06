import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  // ── 单一节制 accent：深墨青 teal（成长/专业，拒绝 AI 紫渐变）──
  static const Color brand50 = Color(0xFFE8F3F1);
  static const Color brand100 = Color(0xFFCDE7E4);
  static const Color brand200 = Color(0xFFA5D4D0);
  static const Color brand400 = Color(0xFF4F9E97);
  static const Color brand500 = Color(0xFF23766F);
  static const Color brand600 = Color(0xFF1B615B);
  static const Color brand700 = Color(0xFF144A46);

  // 兼容旧引用：purple* 并入 accent 同阶，杜绝第二色相
  static const Color purple400 = brand400;
  static const Color purple500 = brand500;
  static const Color purple600 = brand600;

  static const Color gradientStart = brand500;
  static const Color gradientEnd = brand600;

  // ── 暖中性基底（off-white + 墨调，非纯黑）──
  static const Color bgPage = Color(0xFFFAF9F7);
  static const Color bgCard = Color(0xFFFFFFFF);
  static const Color bgHover = Color(0xFFF3F1ED);

  static const Color textPrimary = Color(0xFF1F2933);
  static const Color textSecondary = Color(0xFF55606B);
  static const Color textMuted = Color(0xFF8A939E);

  static const Color borderLight = Color(0xFFE7E4DF);
  static const Color borderMedium = Color(0xFFD3CFC8);

  // 语义色：低饱和哑光
  static const Color success = Color(0xFF3F8C68);
  static const Color successBg = Color(0xFFE3F1EA);
  static const Color warning = Color(0xFFB98A2F);
  static const Color warningBg = Color(0xFFF7EFDD);
  static const Color error = Color(0xFFC0524A);

  static const Color shadowColor = Color(0x0A1F2933);

  // 同色系主渐变（克制，仅胶囊/徽标用；主按钮用实色）
  static const LinearGradient gradientPrimary = LinearGradient(
    colors: [brand500, brand600],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const double radiusSm = 8;
  static const double radiusMd = 12;
  static const double radiusLg = 16;
  static const double radiusXl = 20;
  static const double radiusFull = 9999;

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: bgPage,
      colorScheme: const ColorScheme.light(
        primary: brand500,
        secondary: brand500,
        surface: bgCard,
        onPrimary: Colors.white,
        onSecondary: Colors.white,
        onSurface: textPrimary,
        error: error,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
      ),
      cardTheme: CardThemeData(
        color: bgCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusLg),
          side: const BorderSide(color: borderLight),
        ),
        margin: EdgeInsets.zero,
      ),
      // 主按钮：克制圆角（弃 pill），实色 accent
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: brand500,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusMd),
          ),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: brand500,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusMd),
          ),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bgCard,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: const BorderSide(color: borderLight),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: const BorderSide(color: borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: const BorderSide(color: brand500, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      dividerTheme: const DividerThemeData(
        color: borderLight,
        thickness: 1,
        space: 1,
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          fontSize: 32, fontWeight: FontWeight.w600,
          color: textPrimary, letterSpacing: -0.04,
        ),
        headlineMedium: TextStyle(
          fontSize: 22, fontWeight: FontWeight.w600,
          color: textPrimary, letterSpacing: -0.03,
        ),
        titleMedium: TextStyle(
          fontSize: 16, fontWeight: FontWeight.w600, color: textPrimary,
        ),
        bodyLarge: TextStyle(fontSize: 16, color: textSecondary),
        bodyMedium: TextStyle(fontSize: 14, color: textSecondary),
        bodySmall: TextStyle(fontSize: 12, color: textMuted),
        labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: textPrimary),
      ),
    );
  }

  /// 卡片底：细边框 + 极轻投影（无重阴影）
  static BoxDecoration get cardDecoration => BoxDecoration(
    color: bgCard,
    borderRadius: BorderRadius.circular(radiusLg),
    border: Border.all(color: borderLight),
    boxShadow: const [
      BoxShadow(
        color: Color(0x061F2933),
        blurRadius: 14,
        offset: Offset(0, 3),
      ),
    ],
  );

  /// 主行动按钮：实色 accent，无渐变无霓虹
  static BoxDecoration get gradientButton => BoxDecoration(
    color: brand500,
    borderRadius: BorderRadius.circular(radiusMd),
    boxShadow: const [
      BoxShadow(
        color: Color(0x1A1B615B),
        blurRadius: 8,
        offset: Offset(0, 3),
      ),
    ],
  );

  /// 录音大圆：克制单色 + 微弱阴影（弃外扩光晕）
  static BoxDecoration get glowDecoration => BoxDecoration(
    color: brand500,
    shape: BoxShape.circle,
    boxShadow: const [
      BoxShadow(
        color: Color(0x141B615B),
        blurRadius: 22,
        spreadRadius: 4,
      ),
    ],
  );
}
