package com.interview.mentor.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.KnowledgeDocument;

public interface KnowledgeService {

    /**
     * 创建知识库文档
     */
    KnowledgeDocument createDocument(KnowledgeDocument document, Long tenantId, Long userId);

    /**
     * 更新知识库文档
     */
    KnowledgeDocument updateDocument(Long id, KnowledgeDocument document, Long tenantId);

    /**
     * 删除知识库文档（仅租户私有文档可删除）
     */
    void deleteDocument(Long id, Long tenantId);

    /**
     * 查询文档详情（平台公共 + 租户私有）
     */
    KnowledgeDocument getDocument(Long id, Long tenantId);

    /**
     * 分页查询文档列表
     * @param docType 文档类型筛选（可选）
     * @param jobRole 岗位筛选（可选）
     */
    IPage<KnowledgeDocument> listDocuments(
            Page<KnowledgeDocument> page,
            Long tenantId,
            String docType,
            String jobRole);

    /**
     * 搜索文档内容（关键词模糊搜索）
     */
    IPage<KnowledgeDocument> searchDocuments(
            Page<KnowledgeDocument> page,
            Long tenantId,
            String keyword);
}
