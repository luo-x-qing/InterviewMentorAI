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
    public KnowledgeDocument createDocument(KnowledgeDocument document, Long tenantId, Long userId) {
        document.setTenantId(tenantId);
        document.setUploadedBy(userId);
        document.setIsPublic(0); // 默认租户私有
        document.setEmbeddingStatus(0); // 待向量化
        document.setCreatedAt(LocalDateTime.now());
        document.setUpdatedAt(LocalDateTime.now());

        knowledgeMapper.insert(document);

        // TODO: 异步触发向量化任务，调用 Python 后端生成 embedding

        return document;
    }

    @Override
    public KnowledgeDocument updateDocument(Long id, KnowledgeDocument document, Long tenantId) {
        KnowledgeDocument existing = knowledgeMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(404, "文档不存在");
        }

        // 校验权限：只能修改自己租户的文档
        if (!existing.getTenantId().equals(tenantId)) {
            throw new BusinessException(403, "无权修改此文档");
        }

        existing.setTitle(document.getTitle());
        existing.setContent(document.getContent());
        existing.setDocType(document.getDocType());
        existing.setJobRole(document.getJobRole());
        existing.setTags(document.getTags());
        existing.setUpdatedAt(LocalDateTime.now());
        existing.setEmbeddingStatus(0); // 内容变更，需要重新向量化

        knowledgeMapper.updateById(existing);
        return existing;
    }

    @Override
    public void deleteDocument(Long id, Long tenantId) {
        KnowledgeDocument existing = knowledgeMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(404, "文档不存在");
        }

        if (!existing.getTenantId().equals(tenantId)) {
            throw new BusinessException(403, "无权删除此文档");
        }

        // 平台公共文档不允许租户删除
        if (existing.getIsPublic() == 1) {
            throw new BusinessException(403, "平台公共文档不允许删除");
        }

        knowledgeMapper.deleteById(id);
    }

    @Override
    public KnowledgeDocument getDocument(Long id, Long tenantId) {
        KnowledgeDocument document = knowledgeMapper.selectById(id);
        if (document == null) {
            throw new BusinessException(404, "文档不存在");
        }

        // 只能看到：自己租户的文档 或 平台公共文档
        if (!document.getTenantId().equals(tenantId) && document.getIsPublic() != 1) {
            throw new BusinessException(403, "无权查看此文档");
        }

        return document;
    }

    @Override
    public IPage<KnowledgeDocument> listDocuments(
            Page<KnowledgeDocument> page,
            Long tenantId,
            String docType,
            String jobRole) {

        LambdaQueryWrapper<KnowledgeDocument> wrapper = new LambdaQueryWrapper<KnowledgeDocument>()
                // 平台公共文档 或 本租户私有文档
                .and(w -> w
                        .eq(KnowledgeDocument::getIsPublic, 1)
                        .or()
                        .eq(KnowledgeDocument::getTenantId, tenantId))
                .orderByDesc(KnowledgeDocument::getCreatedAt);

        // 可选筛选条件
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
            Long tenantId,
            String keyword) {

        LambdaQueryWrapper<KnowledgeDocument> wrapper = new LambdaQueryWrapper<KnowledgeDocument>()
                .and(w -> w
                        .eq(KnowledgeDocument::getIsPublic, 1)
                        .or()
                        .eq(KnowledgeDocument::getTenantId, tenantId))
                .and(w -> w
                        .like(KnowledgeDocument::getTitle, keyword)
                        .or()
                        .like(KnowledgeDocument::getContent, keyword))
                .orderByDesc(KnowledgeDocument::getCreatedAt);

        return knowledgeMapper.selectPage(page, wrapper);
    }
}
