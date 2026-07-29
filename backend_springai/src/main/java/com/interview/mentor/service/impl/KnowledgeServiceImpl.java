package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.KnowledgeDocument;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.KnowledgeDocumentMapper;
import com.interview.mentor.service.KnowledgeService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;

@Service
public class KnowledgeServiceImpl implements KnowledgeService {

    private final KnowledgeDocumentMapper knowledgeMapper;

    public KnowledgeServiceImpl(KnowledgeDocumentMapper knowledgeMapper) {
        this.knowledgeMapper = knowledgeMapper;
    }

    @Override
    public KnowledgeDocument createDocument(KnowledgeDocument document, Long userId) {
        document.setUploadedBy(userId);
        document.setIsPublic(0);
        document.setEmbeddingStatus(0);
        document.setCreatedAt(LocalDateTime.now());
        document.setUpdatedAt(LocalDateTime.now());
        knowledgeMapper.insert(document);
        return document;
    }

    @Override
    public KnowledgeDocument updateDocument(Long id, KnowledgeDocument document, Long userId) {
        KnowledgeDocument existing = knowledgeMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(404, "文档不存在");
        }
        if (!existing.getUploadedBy().equals(userId)) {
            throw new BusinessException(403, "无权修改此文档");
        }
        existing.setTitle(document.getTitle());
        existing.setContent(document.getContent());
        existing.setDocType(document.getDocType());
        existing.setJobRole(document.getJobRole());
        existing.setTags(document.getTags());
        existing.setUpdatedAt(LocalDateTime.now());
        existing.setEmbeddingStatus(0);
        knowledgeMapper.updateById(existing);
        return existing;
    }

    @Override
    public void deleteDocument(Long id, Long userId) {
        KnowledgeDocument existing = knowledgeMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(404, "文档不存在");
        }
        if (!existing.getUploadedBy().equals(userId)) {
            throw new BusinessException(403, "无权删除此文档");
        }
        knowledgeMapper.deleteById(id);
    }

    @Override
    public KnowledgeDocument getDocument(Long id, Long userId) {
        KnowledgeDocument document = knowledgeMapper.selectById(id);
        if (document == null) {
            throw new BusinessException(404, "文档不存在");
        }
        if (!document.getUploadedBy().equals(userId) && document.getIsPublic() != 1) {
            throw new BusinessException(403, "无权查看此文档");
        }
        return document;
    }

    @Override
    public IPage<KnowledgeDocument> listDocuments(
            Page<KnowledgeDocument> page,
            Long userId,
            String docType,
            String jobRole) {

        LambdaQueryWrapper<KnowledgeDocument> wrapper = new LambdaQueryWrapper<KnowledgeDocument>()
                .and(w -> w
                        .eq(KnowledgeDocument::getIsPublic, 1)
                        .or()
                        .eq(KnowledgeDocument::getUploadedBy, userId))
                .orderByDesc(KnowledgeDocument::getCreatedAt);

        if (StringUtils.hasText(docType)) {
            wrapper.eq(KnowledgeDocument::getDocType, docType);
        }
        if (StringUtils.hasText(jobRole)) {
            wrapper.eq(KnowledgeDocument::getJobRole, jobRole);
        }

        return knowledgeMapper.selectPage(page, wrapper);
    }

    @Override
    public IPage<KnowledgeDocument> searchDocuments(
            Page<KnowledgeDocument> page,
            Long userId,
            String keyword) {

        LambdaQueryWrapper<KnowledgeDocument> wrapper = new LambdaQueryWrapper<KnowledgeDocument>()
                .and(w -> w
                        .eq(KnowledgeDocument::getIsPublic, 1)
                        .or()
                        .eq(KnowledgeDocument::getUploadedBy, userId))
                .and(w -> w
                        .like(KnowledgeDocument::getTitle, keyword)
                        .or()
                        .like(KnowledgeDocument::getContent, keyword))
                .orderByDesc(KnowledgeDocument::getCreatedAt);

        return knowledgeMapper.selectPage(page, wrapper);
    }
}
