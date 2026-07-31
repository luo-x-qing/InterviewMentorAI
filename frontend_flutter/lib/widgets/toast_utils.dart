import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

/// 统一 SnackBar 快捷方法
class ToastUtils {
  ToastUtils._();

  static void _show(
    BuildContext context,
    String message, {
    required Color backgroundColor,
    IconData? icon,
    Duration duration = const Duration(seconds: 3),
  }) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            if (icon != null) ...[
              Icon(icon, color: Colors.white, size: 18),
              const SizedBox(width: 10),
            ],
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: backgroundColor,
        duration: duration,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }

  static void showSuccess(BuildContext context, String message) {
    _show(context, message,
        backgroundColor: AppTheme.success, icon: Icons.check_circle);
  }

  static void showError(BuildContext context, String message) {
    _show(context, message,
        backgroundColor: AppTheme.error, icon: Icons.error_outline);
  }

  static void showInfo(BuildContext context, String message) {
    _show(context, message,
        backgroundColor: AppTheme.brand500, icon: Icons.info_outline);
  }
}
