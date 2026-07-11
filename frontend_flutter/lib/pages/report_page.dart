import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class ReportPage extends StatelessWidget {
  const ReportPage({super.key});

  @override
  Widget build(BuildContext context) {
    final Object? args = ModalRoute.of(context)?.settings.arguments;
    Map<String, dynamic>? data = args as Map<String, dynamic>?;
    String reportContent = data?["report"] ?? "暂无分析内容";

    return Scaffold(
      appBar: AppBar(title: const Text("面试复盘报告")),
      body: Markdown(data: reportContent),
    );
  }
}
