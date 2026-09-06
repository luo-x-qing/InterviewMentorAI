class Constants {
  /// 后端 API 基础地址（Python Agent 单后端）——单源配置。
  /// 本地开发默认 http://localhost:8000；
  /// 生产构建注入实际基址（nginx 已反代全部 API 与 WS，同源传站点基址即可）：
  ///   flutter build web --release --dart-define=API_BASE_URL=http://<域名或服务器IP>
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// WebSocket 基址：由 [baseUrl] 派生（http→ws、https→wss），保持同源。
  static String get wsUrl {
    final secure = baseUrl.startsWith('https://');
    final withoutScheme = baseUrl.substring(secure ? 8 : 7);
    return '${secure ? 'wss' : 'ws'}://$withoutScheme/ws';
  }

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
