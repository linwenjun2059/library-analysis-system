package com.library.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.common.Result;
import com.library.entity.BookAssociationRule;
import com.library.entity.ClusterSummary;
import com.library.entity.UserCluster;
import com.library.mapper.BookAssociationRuleMapper;
import com.library.mapper.ClusterSummaryMapper;
import com.library.mapper.UserClusterMapper;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 高级数据挖掘分析控制器
 * 
 * 提供关联规则分析和用户聚类分群的API接口
 */
@Slf4j
@Api(tags = "高级数据挖掘分析")
@RestController
@RequestMapping("/analysis/advanced")
public class AdvancedAnalysisController {

    @Resource
    private BookAssociationRuleMapper bookAssociationRuleMapper;

    @Resource
    private UserClusterMapper userClusterMapper;

    @Resource
    private ClusterSummaryMapper clusterSummaryMapper;

    // ==================== 关联规则分析 ====================

    /**
     * 获取图书关联规则列表(分页)
     */
    @ApiOperation("获取图书关联规则")
    @GetMapping("/association/rules")
    public Result<Page<BookAssociationRule>> getAssociationRules(
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "20") Integer size,
            @RequestParam(required = false) String subject,
            @RequestParam(required = false) String associationType,
            @RequestParam(defaultValue = "confidence") String sortBy) {
        log.info("获取图书关联规则：current={}, size={}, subject={}, associationType={}, sortBy={}",
                current, size, subject, associationType, sortBy);

        Page<BookAssociationRule> page = new Page<>(current, size);
        LambdaQueryWrapper<BookAssociationRule> wrapper = new LambdaQueryWrapper<>();

        // 按主题筛选
        if (StringUtils.hasText(subject)) {
            wrapper.and(w -> w
                    .like(BookAssociationRule::getAntecedentSubject, subject)
                    .or()
                    .like(BookAssociationRule::getConsequentSubject, subject));
        }

        // 按关联类型筛选
        if (StringUtils.hasText(associationType)) {
            wrapper.eq(BookAssociationRule::getAssociationType, associationType);
        }

        // 按总数排序
        if ("lift".equals(sortBy)) {
            wrapper.orderByDesc(BookAssociationRule::getLift);
        } else if ("support".equals(sortBy)) {
            wrapper.orderByDesc(BookAssociationRule::getSupport);
        } else {
            wrapper.orderByDesc(BookAssociationRule::getConfidence);
        }

        Page<BookAssociationRule> result = bookAssociationRuleMapper.selectPage(page, wrapper);
        return Result.success(result);
    }

    /**
     * 获取指定图书的关联推荐
     */
    @ApiOperation("获取图书关联推荐")
    @GetMapping("/association/book/{bookTitle}")
    public Result<List<BookAssociationRule>> getBookAssociations(
            @PathVariable String bookTitle,
            @RequestParam(defaultValue = "10") Integer limit) {
        log.info("获取图书关联推荐：bookTitle={}, limit={}", bookTitle, limit);

        LambdaQueryWrapper<BookAssociationRule> wrapper = new LambdaQueryWrapper<>();
        wrapper.like(BookAssociationRule::getAntecedentTitle, bookTitle)
                .orderByDesc(BookAssociationRule::getConfidence)
                .last("LIMIT " + limit);

        List<BookAssociationRule> rules = bookAssociationRuleMapper.selectList(wrapper);
        return Result.success(rules);
    }

    /**
     * 获取关联规则统计概览
     */
    @ApiOperation("获取关联规则统计")
    @GetMapping("/association/stats")
    public Result<Map<String, Object>> getAssociationStats() {
        log.info("获取关联规则统计");

        Map<String, Object> stats = new HashMap<>();

        // 总规则数
        Long totalRules = bookAssociationRuleMapper.selectCount(null);
        stats.put("totalRules", totalRules);

        // 同主题关联数
        LambdaQueryWrapper<BookAssociationRule> sameSubjectWrapper = new LambdaQueryWrapper<>();
        sameSubjectWrapper.eq(BookAssociationRule::getAssociationType, "同主题关联");
        Long sameSubjectCount = bookAssociationRuleMapper.selectCount(sameSubjectWrapper);
        stats.put("sameSubjectRules", sameSubjectCount);

        // 跨主题关联数
        stats.put("crossSubjectRules", totalRules - sameSubjectCount);

        // 平均置信度
        List<BookAssociationRule> allRules = bookAssociationRuleMapper.selectList(null);
        if (!allRules.isEmpty()) {
            double avgConfidence = allRules.stream()
                    .mapToDouble(BookAssociationRule::getConfidence)
                    .average()
                    .orElse(0.0);
            stats.put("avgConfidence", Math.round(avgConfidence * 10000) / 100.0);

            double avgLift = allRules.stream()
                    .mapToDouble(BookAssociationRule::getLift)
                    .average()
                    .orElse(0.0);
            stats.put("avgLift", Math.round(avgLift * 100) / 100.0);
        }

        return Result.success(stats);
    }

    // ==================== 用户聚类分群 ====================

    /**
     * 获取聚类统计摘要
     */
    @ApiOperation("获取聚类统计摘要")
    @GetMapping("/cluster/summary")
    public Result<List<ClusterSummary>> getClusterSummary() {
        log.info("获取聚类统计摘要");

        LambdaQueryWrapper<ClusterSummary> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByAsc(ClusterSummary::getCluster);

        List<ClusterSummary> summaries = clusterSummaryMapper.selectList(wrapper);
        return Result.success(summaries);
    }

    /**
     * 获取指定聚类的用户列表(分页)
     */
    @ApiOperation("获取聚类用户列表")
    @GetMapping("/cluster/{clusterId}/users")
    public Result<Page<UserCluster>> getClusterUsers(
            @PathVariable Integer clusterId,
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "20") Integer size,
            @RequestParam(required = false) String dept) {
        log.info("获取聚类用户列表：clusterId={}, current={}, size={}, dept={}",
                clusterId, current, size, dept);

        Page<UserCluster> page = new Page<>(current, size);
        LambdaQueryWrapper<UserCluster> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCluster::getCluster, clusterId);

        if (StringUtils.hasText(dept)) {
            wrapper.like(UserCluster::getDept, dept);
        }

        wrapper.orderByDesc(UserCluster::getBorrowCount);

        Page<UserCluster> result = userClusterMapper.selectPage(page, wrapper);
        return Result.success(result);
    }

    /**
     * 获取用户所属聚类信息
     */
    @ApiOperation("获取用户聚类信息")
    @GetMapping("/cluster/user/{userid}")
    public Result<UserCluster> getUserCluster(@PathVariable String userid) {
        log.info("获取用户聚类信息：userid={}", userid);

        LambdaQueryWrapper<UserCluster> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCluster::getUserid, userid);

        UserCluster userCluster = userClusterMapper.selectOne(wrapper);
        return Result.success(userCluster);
    }

    /**
     * 获取院系聚类分布
     */
    @ApiOperation("获取院系聚类分布")
    @GetMapping("/cluster/dept-distribution")
    public Result<List<Map<String, Object>>> getDeptClusterDistribution(
            @RequestParam(required = false) String dept) {
        log.info("获取院系聚类分布：dept={}", dept);

        // 这里简化处理，实际可以用自定义SQL
        LambdaQueryWrapper<UserCluster> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(dept)) {
            wrapper.eq(UserCluster::getDept, dept);
        }

        List<UserCluster> users = userClusterMapper.selectList(wrapper);

        // 按院系和聚类分组统计
        Map<String, Map<String, Long>> deptClusterCount = new HashMap<>();
        for (UserCluster user : users) {
            String deptName = user.getDept() != null ? user.getDept() : "未知";
            String clusterName = user.getClusterName();

            deptClusterCount
                    .computeIfAbsent(deptName, k -> new HashMap<>())
                    .merge(clusterName, 1L, Long::sum);
        }

        // 转换为前端友好的格式
        List<Map<String, Object>> result = new java.util.ArrayList<>();
        for (Map.Entry<String, Map<String, Long>> entry : deptClusterCount.entrySet()) {
            Map<String, Object> item = new HashMap<>();
            item.put("dept", entry.getKey());
            item.put("clusters", entry.getValue());
            item.put("total", entry.getValue().values().stream().mapToLong(Long::longValue).sum());
            result.add(item);
        }

        // 按总数排序
        result.sort((a, b) -> Long.compare((Long) b.get("total"), (Long) a.get("total")));

        return Result.success(result);
    }

    /**
     * 获取聚类整体统计
     */
    @ApiOperation("获取聚类整体统计")
    @GetMapping("/cluster/stats")
    public Result<Map<String, Object>> getClusterStats() {
        log.info("获取聚类整体统计");

        Map<String, Object> stats = new HashMap<>();

        // 总用户数
        Long totalUsers = userClusterMapper.selectCount(null);
        stats.put("totalUsers", totalUsers);

        // 聚类数
        List<ClusterSummary> summaries = clusterSummaryMapper.selectList(null);
        stats.put("clusterCount", summaries.size());

        // 各聚类用户数
        List<Map<String, Object>> clusterDistribution = new java.util.ArrayList<>();
        for (ClusterSummary summary : summaries) {
            Map<String, Object> item = new HashMap<>();
            item.put("name", summary.getClusterName());
            item.put("count", summary.getUserCount());
            item.put("percentage", totalUsers > 0 
                    ? Math.round(summary.getUserCount() * 10000.0 / totalUsers) / 100.0 
                    : 0);
            item.put("characteristics", summary.getClusterCharacteristics());
            clusterDistribution.add(item);
        }
        stats.put("distribution", clusterDistribution);

        return Result.success(stats);
    }
}
