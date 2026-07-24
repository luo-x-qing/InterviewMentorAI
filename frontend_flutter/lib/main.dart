import 'package:flutter/material.dart';
import 'package:frontend_flutter/pages/home_page.dart';
import 'package:frontend_flutter/pages/hr_correction_page.dart';
import 'package:frontend_flutter/pages/invite_code_page.dart';
import 'package:frontend_flutter/pages/login_page.dart';
import 'package:frontend_flutter/pages/record_page.dart';
import 'package:frontend_flutter/pages/report_page.dart';
import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/services/token_storage.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await TokenStorage.init();
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  /// 全局 navigatorKey 用于在拦截器中触发跳转
  static final GlobalKey<NavigatorState> navigatorKey =
      GlobalKey<NavigatorState>();

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  @override
  void initState() {
    super.initState();
    // Token 刷新失败 → 跳转登录页
    ApiService.onAuthExpired = () {
      MyApp.navigatorKey.currentState?.pushNamedAndRemoveUntil(
        '/login',
        (route) => false,
      );
    };
  }

  /// 认证守卫：未登录则跳转到登录页
  String? _authGuard(String routeName) {
    // 公开路由不需要认证
    const publicRoutes = {'/login'};
    if (publicRoutes.contains(routeName)) return null;
    if (!TokenStorage.isLoggedIn) return '/login';
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: MyApp.navigatorKey,
      title: 'InterviewMentorAI',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      initialRoute: TokenStorage.isLoggedIn ? '/' : '/login',
      onGenerateRoute: (settings) {
        // 认证守卫
        final redirect = _authGuard(settings.name ?? '/');
        if (redirect != null) {
          return MaterialPageRoute(
            builder: (_) => const LoginPage(),
            settings: const RouteSettings(name: '/login'),
          );
        }

        Widget page;
        final name = settings.name;
        if (name == '/') {
          page = const HomePage();
        } else if (name == '/login') {
          page = const LoginPage();
        } else if (name == '/record') {
          page = const RecordPage();
        } else if (name == '/report') {
          page = const ReportPage();
        } else if (name == '/invite') {
          page = const InviteCodePage();
        } else if (name == '/hr-correction') {
          final interviewId = settings.arguments as int? ?? 0;
          page = HrCorrectionPage(interviewId: interviewId);
        } else {
          page = const HomePage();
        }

        return MaterialPageRoute(
          builder: (_) => page,
          settings: settings,
        );
      },
    );
  }
}
