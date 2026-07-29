package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.KnowledgeDocument;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.security.SecurityUtils;
import com.interview.mentor.service.KnowledgeService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/knowledge")
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    public KnowledgeController(KnowledgeService knowledgeService) {
        this.knowledgeService = knowledgeService;
    }

    @PostMapping
    public Result<KnowledgeDocument> createDocument(@RequestBody KnowledgeDocument document) {
        Long userId = SecurityUtils.currentUserId();
        KnowledgeDocument created = knowledgeService.createDocument(document, userId);
        return Result.success(created);
    }

    @PutMapping("/{id}")
    public Result<KnowledgeDocument> updateDocument(
            @PathVariable Long id,
            @RequestBody KnowledgeDocument document) {
        Long userId = SecurityUtils.currentUserId();
        KnowledgeDocument updated = knowledgeService.updateDocument(id, document, userId);
        return Result.success(updated);
    }

    @DeleteMapping("/{id}")
    public Result<Void> deleteDocument(@PathVariable Long id) {
        Long userId = SecurityUtils.currentUserId();
        knowledgeService.deleteDocument(id, userId);
        return Result.success();
    }

    @GetMapping("/{id}")
    public Result<KnowledgeDocument> getDocument(@PathVariable Long id) {
        Long userId = SecurityUtils.currentUserId();
        KnowledgeDocument document = knowledgeService.getDocument(id, userId);
        return Result.success(document);
    }

    @GetMapping("/list")
    public Result<IPage<KnowledgeDocument>> listDocuments(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String docType,
            @RequestParam(required = false) String jobRole) {
        Long userId = SecurityUtils.currentUserId();
        IPage<KnowledgeDocument> result = knowledgeService.listDocuments(
                new Page<>(page, size), userId, docType, jobRole);
        return Result.success(result);
    }

    @GetMapping("/search")
    public Result<IPage<KnowledgeDocument>> searchDocuments(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam String keyword) {
        Long userId = SecurityUtils.currentUserId();
        IPage<KnowledgeDocument> result = knowledgeService.searchDocuments(
                new Page<>(page, size), userId, keyword);
        return Result.success(result);
    }
}
