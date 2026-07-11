class Constants {
  /// 本机地址，真机局域网调试
  static const String baseUrl = "http://172.28.161.26:8080";

  /// 接口地址
  static const String uploadAudioApi = "$baseUrl/audio/upload";
  static const String recordListApi = "$baseUrl/record/list";
  static const String recordDetailApi = "$baseUrl/record/detail";
}
