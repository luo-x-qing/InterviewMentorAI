import 'package:flutter/material.dart';
import 'package:frontend_flutter/pages/home_page.dart';
import 'package:frontend_flutter/pages/community_page.dart';
import 'package:frontend_flutter/pages/question_bank_page.dart';
import 'package:frontend_flutter/pages/notifications_page.dart';
import 'package:frontend_flutter/pages/profile_page.dart';
import 'package:frontend_flutter/theme.dart';

const _tabs = [
  _TabItem(Icons.home_outlined, Icons.home, '主页'),
  _TabItem(Icons.group_outlined, Icons.group, '社区'),
  _TabItem(Icons.library_books_outlined, Icons.library_books, '题库'),
  _TabItem(Icons.notifications_outlined, Icons.notifications, '通知'),
  _TabItem(Icons.person_outline, Icons.person, '我'),
];

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _pages),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        border: Border(top: BorderSide(color: AppTheme.borderLight)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 12, offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            children: List.generate(_tabs.length, (i) {
              final active = _currentIndex == i;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _currentIndex = i),
                  behavior: HitTestBehavior.opaque,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          active ? _tabs[i].activeIcon : _tabs[i].icon,
                          size: 24,
                          color: active ? AppTheme.brand500 : AppTheme.textMuted,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          _tabs[i].label,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: active ? FontWeight.w600 : FontWeight.w400,
                            color: active ? AppTheme.brand500 : AppTheme.textMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }

  static const _pages = [
    HomePage(),
    CommunityPage(),
    QuestionBankPage(),
    NotificationsPage(),
    ProfilePage(),
  ];
}

class _TabItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  const _TabItem(this.icon, this.activeIcon, this.label);
}
