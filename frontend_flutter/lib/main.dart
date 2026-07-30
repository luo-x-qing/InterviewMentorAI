import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/pages/main_shell.dart';
import 'package:frontend_flutter/pages/login_page.dart';
import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/services/token_storage.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await TokenStorage.init();
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  static final GlobalKey<NavigatorState> navigatorKey =
      GlobalKey<NavigatorState>();

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  @override
  void initState() {
    super.initState();
    ApiService.onAuthExpired = () {
      MyApp.navigatorKey.currentState?.pushNamedAndRemoveUntil(
        '/login',
        (route) => false,
      );
    };
  }

  String? _authGuard(String routeName) {
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
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      initialRoute: TokenStorage.isLoggedIn ? '/' : '/login',
      onGenerateRoute: (settings) {
        final redirect = _authGuard(settings.name ?? '/');
        if (redirect != null) {
          return MaterialPageRoute(
            builder: (_) => const LoginPage(),
            settings: const RouteSettings(name: '/login'),
          );
        }

        Widget page;
        switch (settings.name) {
          case '/':
            page = const MainShell();
          case '/login':
            page = const LoginPage();
          default:
            page = const MainShell();
        }

        return MaterialPageRoute(
          builder: (_) => page,
          settings: settings,
        );
      },
    );
  }
}
