package com.interview.mentor.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.KnowledgeDocument;

public interface KnowledgeService {

    KnowledgeDocument createDocument(KnowledgeDocument document, Long userId);

    KnowledgeDocument updateDocument(Long id, KnowledgeDocument document, Long userId);

    void deleteDocument(Long id, Long userId);

    KnowledgeDocument getDocument(Long id, Long userId);

    IPage<KnowledgeDocument> listDocuments(
            Page<KnowledgeDocument> page,
            Long userId,
            String docType,
            String jobRole);

    IPage<KnowledgeDocument> searchDocuments(
            Page<KnowledgeDocument> page,
            Long userId,
            String keyword);
}
