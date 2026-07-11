/**
 * 文件操作工具类（FileUtil）
 * 
 * 功能说明：
 * - 提供通用文件操作静态方法
 * - 生成UUID随机文件名（保留原后缀），避免上传文件名冲突
 * - 自动创建不存在的目录结构
 * - 被AudioController和AsrService调用，处理音频文件存储
 */
package com.ecommerce.backend_springai.util;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

public class FileUtil {

    /**
     * 生成随机文件名，保留原文件后缀
     * 
     * @param originalFilename 原始文件名，如 "interview.wav"
     * @return UUID随机文件名，如 "a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav"
     */
    public static String generateFileName(String originalFilename) {
        String suffix = "";
        if (originalFilename.contains(".")) {
            suffix = originalFilename.substring(originalFilename.lastIndexOf("."));
        }
        return UUID.randomUUID() + suffix;
    }

    /**
     * 创建目录，若不存在则递归新建
     * 
     * @param dirPath 目标目录绝对路径
     * @throws Exception 目录创建失败时抛出异常
     */
    public static void makeDir(String dirPath) throws Exception {
        Path path = Paths.get(dirPath);
        if (!Files.exists(path)) {
            Files.createDirectories(path);
        }
    }
}
