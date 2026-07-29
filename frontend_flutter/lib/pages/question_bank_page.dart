import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

class QuestionBankPage extends StatelessWidget {
  const QuestionBankPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('题库')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.library_books, size: 64,
                color: AppTheme.textMuted.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            const Text('面试题库',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 8),
            const Text('精选技术面试题，按分类练习',
                style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }
}
