import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  static const Color brand50 = Color(0xFFEEF2FF);
  static const Color brand100 = Color(0xFFE0E7FF);
  static const Color brand200 = Color(0xFFC7D2FE);
  static const Color brand400 = Color(0xFF818CF8);
  static const Color brand500 = Color(0xFF4F46E5);
  static const Color brand600 = Color(0xFF4338CA);
  static const Color brand700 = Color(0xFF3730A3);

  static const Color purple400 = Color(0xFFC084FC);
  static const Color purple500 = Color(0xFF7C3AED);
  static const Color purple600 = Color(0xFF6D28D9);

  static const Color gradientStart = brand500;
  static const Color gradientEnd = purple500;

  static const Color bgPage = Color(0xFFF8FAFC);
  static const Color bgCard = Color(0xFFFFFFFF);
  static const Color bgHover = Color(0xFFF1F5F9);

  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF475569);
  static const Color textMuted = Color(0xFF94A3B8);

  static const Color borderLight = Color(0xFFE2E8F0);
  static const Color borderMedium = Color(0xFFCBD5E1);

  static const Color success = Color(0xFF22C55E);
  static const Color successBg = Color(0xFFDCFCE7);
  static const Color warning = Color(0xFFD97706);
  static const Color warningBg = Color(0xFFFEF3C7);
  static const Color error = Color(0xFFEF4444);

  static const Color shadowColor = Color(0x0D000000);

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
        secondary: purple500,
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
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: brand500,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusFull),
          ),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: brand500,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusFull),
          ),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bgPage,
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

  static BoxDecoration get cardDecoration => BoxDecoration(
    color: bgCard,
    borderRadius: BorderRadius.circular(radiusLg),
    border: Border.all(color: borderLight),
    boxShadow: const [
      BoxShadow(
        color: Color(0x08000000),
        blurRadius: 20,
        offset: Offset(0, 4),
      ),
      BoxShadow(
        color: Color(0x0A000000),
        blurRadius: 6,
        offset: Offset(0, 2),
      ),
    ],
  );

  static BoxDecoration get gradientButton => BoxDecoration(
    gradient: const LinearGradient(
      colors: [gradientStart, gradientEnd],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    borderRadius: BorderRadius.circular(radiusFull),
    boxShadow: const [
      BoxShadow(
        color: Color(0x404F46E5),
        blurRadius: 12,
        offset: Offset(0, 4),
      ),
    ],
  );

  static BoxDecoration get glowDecoration => BoxDecoration(
    gradient: const LinearGradient(
      colors: [gradientStart, gradientEnd],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    shape: BoxShape.circle,
    boxShadow: const [
      BoxShadow(
        color: Color(0x1A4F46E5),
        blurRadius: 32,
        spreadRadius: 8,
      ),
    ],
  );
}
