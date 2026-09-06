class Constants {
  /// 后端 API 基础地址（Python Agent 单后端）
  /// Docker 中 nginx 反向代理同源访问，留空表示同源
  /// 本地开发时可改为 http://localhost:8000
  static const String baseUrl = "http://localhost:8000";
  static const String wsUrl = "ws://localhost:8000/ws";

  /// Auth
  static const String loginApi = "$baseUrl/auth/login";
  static const String registerApi = "$baseUrl/auth/register";
  static const String refreshTokenApi = "$baseUrl/auth/refresh";

  /// 面试
  static const String interviewCreateApi = "$baseUrl/interview";
  static const String interviewListApi = "$baseUrl/interview/list";
  static const String interviewMyListApi = "$baseUrl/interview/my";
  static const String interviewDetailApi = "$baseUrl/interview";   // + /{id}
  static const String interviewAnalyzeApi = "$baseUrl/interview";  // + /{id}/analyze

  /// 音频上传（后端 §9.4：存盘 + 建面试记录，返回 interview_id）
  static const String uploadAudioApi = "$baseUrl/audio/upload";

  /// 报告 & 评估
  static const String reportEvaluationsApi = "$baseUrl/report/interview";  // + /{id}/evaluations
  static const String reportDetailApi = "$baseUrl/report/interview";       // + /{id}/report
  static const String reportListApi = "$baseUrl/report/list";

  /// Coach 陪练
  static const String coachSessionApi = "$baseUrl/coach/session";          // POST 开会话
  static const String coachQuestionApi = "$baseUrl/coach/session";         // + /{id}/question
  static const String coachAnswerApi = "$baseUrl/coach/session";           // + /{id}/answer
  static const String coachEndApi = "$baseUrl/coach/session";              // + /{id}/end
  static const String coachRecommendApi = "$baseUrl/coach/recommend";      // GET ?limit=
  static const String coachProfileApi = "$baseUrl/coach/profile";          // GET 画像

  /// 用户
  static const String userProfileApi = "$baseUrl/user/profile";
  static const String userPasswordApi = "$baseUrl/user/password";
}
