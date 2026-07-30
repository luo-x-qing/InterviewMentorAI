class Constants {
  /// 后端 API 基础地址
  /// Docker 中 nginx 反向代理同源访问，留空表示同源
  /// 本地开发时可改为 http://localhost:8080
  static const String baseUrl = "http://localhost:8081";
  static const String wsUrl = "ws://localhost:8081/ws";

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

  /// 报告 & 评估
  static const String reportEvaluationsApi = "$baseUrl/report/interview";  // + /{id}/evaluations
  static const String reportDetailApi = "$baseUrl/report/interview";       // + /{id}/report
  static const String reportListApi = "$baseUrl/report/list";

  /// 用户
  static const String userProfileApi = "$baseUrl/user/profile";
  static const String userPasswordApi = "$baseUrl/user/password";
}
