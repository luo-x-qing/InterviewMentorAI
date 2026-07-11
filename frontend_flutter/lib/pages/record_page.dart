import 'package:flutter/material.dart';
import 'package:frontend_flutter/services/audio_service.dart';
import 'package:frontend_flutter/services/api_service.dart';

class RecordPage extends StatefulWidget {
  const RecordPage({super.key});

  @override
  State<RecordPage> createState() => _RecordPageState();
}

class _RecordPageState extends State<RecordPage> {
  bool isRecording = false;
  bool isAnalyzing = false;

  Future<void> _toggleRecord() async {
    if (!isRecording) {
      await AudioService.startRecord();
      setState(() => isRecording = true);
    } else {
      setState(() {
        isRecording = false;
        isAnalyzing = true;
      });
      String? audioPath = await AudioService.stopRecord();
      if (audioPath != null) {
        var result = await ApiService.uploadAudioFile(audioPath);
        setState(() => isAnalyzing = false);
        if (mounted) {
          Navigator.pushNamed(context, "/report", arguments: result["data"]);
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("面试录音")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (isAnalyzing)
              const Column(
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 20),
                  Text("AI正在分析面试内容，请稍候..."),
                ],
              ),
            const SizedBox(height: 40),
            ElevatedButton(
              onPressed: isAnalyzing ? null : _toggleRecord,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 50, vertical: 16),
                backgroundColor: isRecording ? Colors.red : Colors.blue,
              ),
              child: Text(isRecording ? "停止录音" : "开始录音"),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    AudioService.dispose();
    super.dispose();
  }
}
