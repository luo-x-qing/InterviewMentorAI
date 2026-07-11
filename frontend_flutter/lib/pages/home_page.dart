import 'package:flutter/material.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("InterviewMentorAI")),
      body: const Center(child: Text("历史面试记录")),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.pushNamed(context, "/record");
        },
        child: const Icon(Icons.mic),
      ),
    );
  }
}
