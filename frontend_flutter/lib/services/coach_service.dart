import 'package:dio/dio.dart';

import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/utils/constants.dart';

/// 教练陪练数据模型（对齐后端 entities：Coach*Out）
class CoachQuestion {
  final String questionNo;
  final String title;
  final String question;
  final String evaluationPoints;
  final String difficulty;

  const CoachQuestion({
    required this.questionNo,
    required this.title,
    required this.question,
    this.evaluationPoints = '',
    this.difficulty = 'MEDIUM',
  });

  factory CoachQuestion.fromJson(Map<String, dynamic> json) => CoachQuestion(
        questionNo: json['question_no'] as String? ?? '',
        title: json['title'] as String? ?? '',
        question: json['question'] as String? ?? '',
        evaluationPoints: json['evaluation_points'] as String? ?? '',
        difficulty: json['difficulty'] as String? ?? 'MEDIUM',
      );
}

class CoachFeedback {
  final bool isCorrect;
  final int score;
  final String feedback;
  final String correctAnswer;

  const CoachFeedback({
    required this.isCorrect,
    required this.score,
    required this.feedback,
    this.correctAnswer = '',
  });

  factory CoachFeedback.fromJson(Map<String, dynamic> json) => CoachFeedback(
        isCorrect: json['is_correct'] as bool? ?? false,
        score: json['score'] as int? ?? 0,
        feedback: json['feedback'] as String? ?? '',
        correctAnswer: json['correct_answer'] as String? ?? '',
      );
}

class CoachSessionReportData {
  final String sessionId;
  final int totalQuestions;
  final int correctAnswers;
  final double accuracy;
  final List<String> weaknesses;
  final String suggestions;

  const CoachSessionReportData({
    required this.sessionId,
    required this.totalQuestions,
    required this.correctAnswers,
    required this.accuracy,
    this.weaknesses = const [],
    this.suggestions = '',
  });

  factory CoachSessionReportData.fromJson(Map<String, dynamic> json) =>
      CoachSessionReportData(
        sessionId: json['session_id'] as String? ?? '',
        totalQuestions: json['total_questions'] as int? ?? 0,
        correctAnswers: json['correct_answers'] as int? ?? 0,
        accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0,
        weaknesses: (json['weaknesses'] as List<dynamic>? ?? [])
            .whereType<String>()
            .toList(),
        suggestions: json['suggestions'] as String? ?? '',
      );
}

/// Coach 陪练服务 —— 会话生命周期 + 画像 + 推荐
class CoachService {
  static final Dio _dio = ApiService.dio;

  /// 开启一个新的陪练会话
  static Future<Map<String, dynamic>> startSession({
    String mode = 'TEXT',
    String difficulty = 'MEDIUM',
  }) async {
    final resp = await _dio.post(Constants.coachSessionApi, data: {
      'mode': mode,
      'difficulty': difficulty,
    });
    return resp.data as Map<String, dynamic>;
  }

  /// 获取当前会话的下一道题
  static Future<CoachQuestion> nextQuestion(String sessionId) async {
    final resp = await _dio.get('${Constants.coachQuestionApi}/$sessionId/question');
    return CoachQuestion.fromJson(resp.data as Map<String, dynamic>);
  }

  /// 提交作答，返回即时反馈（后端同步推送 WS coach.{id}.feedback）
  static Future<CoachFeedback> submitAnswer(String sessionId, String answer) async {
    final resp = await _dio.post(
      '${Constants.coachAnswerApi}/$sessionId/answer',
      data: {'answer': answer},
    );
    return CoachFeedback.fromJson(resp.data as Map<String, dynamic>);
  }

  /// 结束会话，生成结课报告
  static Future<CoachSessionReportData> endSession(String sessionId) async {
    final resp = await _dio.post('${Constants.coachEndApi}/$sessionId/end');
    return CoachSessionReportData.fromJson(resp.data as Map<String, dynamic>);
  }

  /// 按画像弱项推荐针对性练习（无需开启会话）
  static Future<List<CoachQuestion>> recommend({int limit = 3}) async {
    final resp = await _dio.get(Constants.coachRecommendApi, queryParameters: {'limit': limit});
    final list = resp.data as List<dynamic>;
    return list
        .map((e) => CoachQuestion.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// 获取我的薄弱点画像
  static Future<Map<String, dynamic>> getProfile() async {
    final resp = await _dio.get(Constants.coachProfileApi);
    return resp.data as Map<String, dynamic>;
  }
}