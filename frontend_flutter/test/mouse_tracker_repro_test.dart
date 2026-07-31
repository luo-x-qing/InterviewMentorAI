import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:frontend_flutter/pages/report_page.dart';
import 'package:frontend_flutter/theme.dart';

void main() {
  testWidgets('示例报告页悬停不触发 mouse_tracker 断言', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.lightTheme,
      home: ReportPage(data: ReportPage.mockData()),
    ));
    await tester.pumpAndSettle();

    final pointer = TestPointer(1, PointerDeviceKind.mouse);
    const x = 200.0;
    for (double y = 50; y < 700; y += 50) {
      await tester.sendEventToBinding(pointer.hover(Offset(x, y)));
      await tester.pump();
    }
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });

  testWidgets('示例报告页 Markdown 表格可正常渲染', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(500, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.lightTheme,
      home: ReportPage(data: ReportPage.mockData()),
    ));
    await tester.pumpAndSettle();

    expect(find.text('面试复盘报告'), findsWidgets);
    expect(find.text('优势亮点'), findsOneWidget);
    expect(find.text('改进建议'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
