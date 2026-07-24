class Constants {
  /// 后端 API 基础地址
  static const String baseUrl = "http://172.28.161.26:8080";

  /// WebSocket STOMP 地址（raw WebSocket，非 SockJS）
  static const String wsUrl = "ws://172.28.161.26:8080/ws";

  /// Auth
  static const String loginApi = "$baseUrl/auth/login";
  static const String registerApi = "$baseUrl/auth/register";
  static const String refreshTokenApi = "$baseUrl/auth/refresh";

  /// 面试
  static const String interviewCreateApi = "$baseUrl/interview";
  static const String interviewListApi = "$baseUrl/interview/list";
  static const String interviewMyListApi = "$baseUrl/interview/my";
  static const String interviewDetailApi = "$baseUrl/interview";   // + /{id}

  /// 音频上传（待接入新 interview API）
  static const String uploadAudioApi = "$baseUrl/audio/upload";

  /// 会话（邀请码）
  static const String sessionCreateApi = "$baseUrl/session/create";
  static const String sessionCheckApi = "$baseUrl/session/code";   // + /{code}/valid
  static const String sessionDetailApi = "$baseUrl/session/code";  // + /{code}

  /// 报告 & 评估
  static const String reportEvaluationsApi = "$baseUrl/report/interview";  // + /{id}/evaluations
  static const String reportDetailApi = "$baseUrl/report/interview";       // + /{id}/report
  static const String reportCorrectEvalApi = "$baseUrl/report/evaluation"; // + /{id}/correct
  static const String reportListApi = "$baseUrl/report/list";
  static const String reportCorrectReportApi = "$baseUrl/report/interview"; // + /{id}/report (PUT)

  /// 历史记录
  static const String recordListApi = "$baseUrl/record/list";
  static const String recordDetailApi = "$baseUrl/record/detail";

  /// 用户
  static const String userProfileApi = "$baseUrl/user/profile";
  static const String userPasswordApi = "$baseUrl/user/password";
}
