/**
 * 文件操作工具类（FileUtil）
 * 
 * 功能说明：
 * - 提供通用文件操作方法
 * - 使用UUID生成文件名，避免原文件名冲突
 * - 自动创建目录结构
 * - 供AudioController和asrService调用
 */
package com.ecommerce.backend_springai.util;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

public class FileUtil {

    /**
     * 生成唯一文件名
     * 保留原文件后缀，使用UUID作为文件名
     * 
     * @param originalFilename 原始文件名，如"interview.wav"
     * @return UUID文件名，如"a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav"
     */
    public static String generateFileName(String originalFilename) {
        String suffix = "";
        if (originalFilename.contains(".")) {
            suffix = originalFilename.substring(originalFilename.lastIndexOf("."));
        }
        return UUID.randomUUID() + suffix;
    }

    /**
     * 创建目录（如不存在）
     * 
     * @param dirPath 目录路径
     * @throws Exception 创建目录失败时抛出异常
     */
    public static void makeDir(String dirPath) throws Exception {
        Path path = Paths.get(dirPath);
        if (!Files.exists(path)) {
            Files.createDirectories(path);
        }
    }
}
