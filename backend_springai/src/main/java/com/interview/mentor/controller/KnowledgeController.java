package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.KnowledgeDocument;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.service.KnowledgeService;
import com.interview.mentor.tenant.TenantContext;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/knowledge")
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    public KnowledgeController(KnowledgeService knowledgeService) {
        this.knowledgeService = knowledgeService;
    }

    /**
     * 创建知识库文档
     */
    @PostMapping
    public Result<KnowledgeDocument> createDocument(
            @RequestBody KnowledgeDocument document) {
        Long tenantId = TenantContext.getTenantId();
        // TODO: 从 Authentication 获取 userId
        Long userId = null;
        KnowledgeDocument created = knowledgeService.createDocument(document, tenantId, userId);
        return Result.success(created);
    }

    /**
     * 更新知识库文档
     */
    @PutMapping("/{id}")
    public Result<KnowledgeDocument> updateDocument(
            @PathVariable Long id,
            @RequestBody KnowledgeDocument document) {
        Long tenantId = TenantContext.getTenantId();
        KnowledgeDocument updated = knowledgeService.updateDocument(id, document, tenantId);
        return Result.success(updated);
    }

    /**
     * 删除知识库文档
     */
    @DeleteMapping("/{id}")
    public Result<Void> deleteDocument(@PathVariable Long id) {
        Long tenantId = TenantContext.getTenantId();
        knowledgeService.deleteDocument(id, tenantId);
        return Result.success();
    }

    /**
     * 查询文档详情
     */
    @GetMapping("/{id}")
    public Result<KnowledgeDocument> getDocument(@PathVariable Long id) {
        Long tenantId = TenantContext.getTenantId();
        KnowledgeDocument document = knowledgeService.getDocument(id, tenantId);
        return Result.success(document);
    }

    /**
     * 分页查询文档列表
     */
    @GetMapping("/list")
    public Result<IPage<KnowledgeDocument>> listDocuments(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String docType,
            @RequestParam(required = false) String jobRole) {
        Long tenantId = TenantContext.getTenantId();
        IPage<KnowledgeDocument> result = knowledgeService.listDocuments(
                new Page<>(page, size), tenantId, docType, jobRole);
        return Result.success(result);
    }

    /**
     * 搜索文档
     */
    @GetMapping("/search")
    public Result<IPage<KnowledgeDocument>> searchDocuments(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam String keyword) {
        Long tenantId = TenantContext.getTenantId();
        IPage<KnowledgeDocument> result = knowledgeService.searchDocuments(
                new Page<>(page, size), tenantId, keyword);
        return Result.success(result);
    }
}
