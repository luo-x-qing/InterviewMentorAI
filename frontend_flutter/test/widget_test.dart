import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:frontend_flutter/main.dart';

void main() {
  // 所有测试前 mock SharedPreferences（TokenStorage 依赖）
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('未登录时自动跳转登录页', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();

    // 未登录状态下应展示登录页面的标题
    expect(find.text('InterviewMentorAI'), findsOneWidget);
    expect(find.text('登录'), findsWidgets); // Tab 标签
    expect(find.text('注册'), findsOneWidget);
  });

  testWidgets('登录页切换登录/注册模式', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();

    // 默认在登录 Tab，不应出现昵称字段
    expect(find.text('昵称（选填）'), findsNothing);

    // 点击"注册" Tab
    await tester.tap(find.text('注册'));
    await tester.pumpAndSettle();

    // 注册模式下应展示额外字段（新后端契约：手机号必填，昵称选填，无邮箱）
    expect(find.text('昵称（选填）'), findsOneWidget);
    expect(find.text('手机号'), findsWidgets);

    // 切换回登录
    await tester.tap(find.text('登录'));
    await tester.pumpAndSettle();
    expect(find.text('昵称（选填）'), findsNothing);
  });

  testWidgets('空手机号密码时显示错误提示', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();

    // 不输入任何内容直接点登录
    await tester.tap(find.text('登 录'));
    await tester.pumpAndSettle();

    // 应显示错误提示
    expect(find.text('手机号和密码不能为空'), findsOneWidget);
  });
}
