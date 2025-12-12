package com.library.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.common.Result;
import com.library.entity.BookHeatPrediction;
import com.library.entity.LendTrendPrediction;
import com.library.entity.OverdueRiskPrediction;
import com.library.mapper.BookHeatPredictionMapper;
import com.library.mapper.LendTrendPredictionMapper;
import com.library.mapper.OverdueRiskPredictionMapper;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 预测分析控制器
 * 
 * 提供逾期风险预测、借阅趋势预测、图书热度预测等API接口
 */
@Slf4j
@Api(tags = "预测分析")
@RestController
@RequestMapping("/analysis/prediction")
public class PredictionController {

    @Resource
    private OverdueRiskPredictionMapper overdueRiskPredictionMapper;

    @Resource
    private LendTrendPredictionMapper lendTrendPredictionMapper;

    @Resource
    private BookHeatPredictionMapper bookHeatPredictionMapper;

    // ==================== 逾期风险预测 ====================

    /**
     * 获取逾期风险预测列表(分页)
     */
    @ApiOperation("获取逾期风险预测列表")
    @GetMapping("/overdue/list")
    public Result<Page<OverdueRiskPrediction>> getOverdueRiskList(
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "20") Integer size,
            @RequestParam(required = false) String riskLevel,
            @RequestParam(required = false) String dept) {
        log.info("获取逾期风险预测列表:current={}, size={}, riskLevel={}, dept={}", 
                current, size, riskLevel, dept);

        Page<OverdueRiskPrediction> page = new Page<>(current, size);
        LambdaQueryWrapper<OverdueRiskPrediction> wrapper = new LambdaQueryWrapper<>();

        if (StringUtils.hasText(riskLevel)) {
            wrapper.eq(OverdueRiskPrediction::getRiskLevel, riskLevel);
        }
        if (StringUtils.hasText(dept)) {
            wrapper.like(OverdueRiskPrediction::getDept, dept);
        }

        wrapper.orderByDesc(OverdueRiskPrediction::getOverdueProbability);

        Page<OverdueRiskPrediction> result = overdueRiskPredictionMapper.selectPage(page, wrapper);
        return Result.success(result);
    }

    /**
     * 获取逾期风险统计概览
     */
    @ApiOperation("获取逾期风险统计")
    @GetMapping("/overdue/stats")
    public Result<Map<String, Object>> getOverdueRiskStats() {
        log.info("获取逾期风险统计");

        Map<String, Object> stats = new HashMap<>();

        // 总用户数
        Long totalUsers = overdueRiskPredictionMapper.selectCount(null);
        stats.put("totalUsers", totalUsers);

        // 各风险等级统计
        List<OverdueRiskPrediction> all = overdueRiskPredictionMapper.selectList(null);
        Map<String, Long> riskDistribution = all.stream()
                .collect(Collectors.groupingBy(
                        p -> p.getRiskLevel() != null ? p.getRiskLevel() : "未知",
                        Collectors.counting()
                ));
        stats.put("riskDistribution", riskDistribution);

        // 中高风险用户数(高风险+中风险)
        long mediumHighRiskCount = all.stream()
                .filter(p -> "高风险".equals(p.getRiskLevel()) || "中风险".equals(p.getRiskLevel()))
                .count();
        stats.put("mediumHighRiskCount", mediumHighRiskCount);
        stats.put("mediumHighRiskRate", totalUsers > 0 ? Math.round(mediumHighRiskCount * 10000.0 / totalUsers) / 100.0 : 0);

        // 平均逾期概率
        double avgProbability = all.stream()
                .mapToDouble(p -> p.getOverdueProbability() != null ? p.getOverdueProbability() : 0)
                .average()
                .orElse(0);
        stats.put("avgOverdueProbability", Math.round(avgProbability * 10000) / 100.0);

        return Result.success(stats);
    }

    /**
     * 获取指定用户的逾期风险
     */
    @ApiOperation("获取用户逾期风险")
    @GetMapping("/overdue/user/{userid}")
    public Result<OverdueRiskPrediction> getUserOverdueRisk(@PathVariable String userid) {
        log.info("获取用户逾期风险:userid={}", userid);

        LambdaQueryWrapper<OverdueRiskPrediction> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(OverdueRiskPrediction::getUserid, userid);

        OverdueRiskPrediction prediction = overdueRiskPredictionMapper.selectOne(wrapper);
        return Result.success(prediction);
    }

    // ==================== 借阅趋势预测 ====================

    /**
     * 获取借阅趋势预测数据
     */
    @ApiOperation("获取借阅趋势预测")
    @GetMapping("/trend/list")
    public Result<List<LendTrendPrediction>> getLendTrendList(
            @RequestParam(required = false) String dataType) {
        log.info("获取借阅趋势预测:dataType={}", dataType);

        LambdaQueryWrapper<LendTrendPrediction> wrapper = new LambdaQueryWrapper<>();

        if (StringUtils.hasText(dataType)) {
            wrapper.eq(LendTrendPrediction::getDataType, dataType);
        }

        wrapper.orderByAsc(LendTrendPrediction::getLendMonth);

        List<LendTrendPrediction> result = lendTrendPredictionMapper.selectList(wrapper);
        return Result.success(result);
    }

    /**
     * 获取借阅趋势统计
     */
    @ApiOperation("获取借阅趋势统计")
    @GetMapping("/trend/stats")
    public Result<Map<String, Object>> getLendTrendStats() {
        log.info("获取借阅趋势统计");

        Map<String, Object> stats = new HashMap<>();

        List<LendTrendPrediction> all = lendTrendPredictionMapper.selectList(null);

        // 历史数据
        List<LendTrendPrediction> historical = all.stream()
                .filter(p -> "历史".equals(p.getDataType()))
                .collect(Collectors.toList());

        // 预测数据
        List<LendTrendPrediction> predicted = all.stream()
                .filter(p -> "预测".equals(p.getDataType()))
                .collect(Collectors.toList());

        stats.put("historicalMonths", historical.size());
        stats.put("predictedMonths", predicted.size());

        // 历史平均借阅量
        double avgHistorical = historical.stream()
                .mapToLong(p -> p.getLendCount() != null ? p.getLendCount() : 0)
                .average()
                .orElse(0);
        stats.put("avgHistoricalLend", Math.round(avgHistorical));

        // 预测平均借阅量
        double avgPredicted = predicted.stream()
                .mapToLong(p -> p.getPredictedCount() != null ? p.getPredictedCount() : 0)
                .average()
                .orElse(0);
        stats.put("avgPredictedLend", Math.round(avgPredicted));

        // 趋势判断
        if (avgPredicted > avgHistorical * 1.1) {
            stats.put("overallTrend", "上升");
        } else if (avgPredicted < avgHistorical * 0.9) {
            stats.put("overallTrend", "下降");
        } else {
            stats.put("overallTrend", "平稳");
        }

        return Result.success(stats);
    }

    // ==================== 图书热度预测 ====================

    /**
     * 获取图书热度预测列表(分页)
     */
    @ApiOperation("获取图书热度预测列表")
    @GetMapping("/heat/list")
    public Result<Page<BookHeatPrediction>> getBookHeatList(
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "20") Integer size,
            @RequestParam(required = false) String heatLevel,
            @RequestParam(required = false) String trend,
            @RequestParam(required = false) String subject) {
        log.info("获取图书热度预测列表:current={}, size={}, heatLevel={}, trend={}, subject={}",
                current, size, heatLevel, trend, subject);

        Page<BookHeatPrediction> page = new Page<>(current, size);
        LambdaQueryWrapper<BookHeatPrediction> wrapper = new LambdaQueryWrapper<>();

        if (StringUtils.hasText(heatLevel)) {
            wrapper.eq(BookHeatPrediction::getHeatLevel, heatLevel);
        }
        if (StringUtils.hasText(trend)) {
            wrapper.eq(BookHeatPrediction::getTrend, trend);
        }
        if (StringUtils.hasText(subject)) {
            wrapper.like(BookHeatPrediction::getSubject, subject);
        }

        wrapper.orderByDesc(BookHeatPrediction::getHeatScore);

        Page<BookHeatPrediction> result = bookHeatPredictionMapper.selectPage(page, wrapper);
        return Result.success(result);
    }

    /**
     * 获取图书热度统计
     */
    @ApiOperation("获取图书热度统计")
    @GetMapping("/heat/stats")
    public Result<Map<String, Object>> getBookHeatStats() {
        log.info("获取图书热度统计");

        Map<String, Object> stats = new HashMap<>();

        List<BookHeatPrediction> all = bookHeatPredictionMapper.selectList(null);
        stats.put("totalBooks", all.size());

        // 热度等级分布
        Map<String, Long> heatDistribution = all.stream()
                .collect(Collectors.groupingBy(
                        p -> p.getHeatLevel() != null ? p.getHeatLevel() : "未知",
                        Collectors.counting()
                ));
        stats.put("heatDistribution", heatDistribution);

        // 趋势分布
        Map<String, Long> trendDistribution = all.stream()
                .collect(Collectors.groupingBy(
                        p -> p.getTrend() != null ? p.getTrend() : "未知",
                        Collectors.counting()
                ));
        stats.put("trendDistribution", trendDistribution);

        // 爆款图书数
        long hotCount = all.stream()
                .filter(p -> "爆款".equals(p.getHeatLevel()) || "热门".equals(p.getHeatLevel()))
                .count();
        stats.put("hotBooksCount", hotCount);

        // 需要采购的图书数
        long needPurchase = all.stream()
                .filter(p -> p.getRecommendation() != null && p.getRecommendation().contains("增加馆藏"))
                .count();
        stats.put("needPurchaseCount", needPurchase);

        return Result.success(stats);
    }

    /**
     * 获取热门图书TOP N
     */
    @ApiOperation("获取热门图书TOP")
    @GetMapping("/heat/top")
    public Result<List<BookHeatPrediction>> getTopHotBooks(
            @RequestParam(defaultValue = "20") Integer limit) {
        log.info("获取热门图书TOP:limit={}", limit);

        LambdaQueryWrapper<BookHeatPrediction> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(BookHeatPrediction::getHeatScore)
                .last("LIMIT " + limit);

        List<BookHeatPrediction> result = bookHeatPredictionMapper.selectList(wrapper);
        return Result.success(result);
    }

    /**
     * 获取采购建议列表
     */
    @ApiOperation("获取采购建议")
    @GetMapping("/heat/purchase-suggestions")
    public Result<List<BookHeatPrediction>> getPurchaseSuggestions() {
        log.info("获取采购建议");

        LambdaQueryWrapper<BookHeatPrediction> wrapper = new LambdaQueryWrapper<>();
        wrapper.like(BookHeatPrediction::getRecommendation, "增加馆藏")
                .orderByDesc(BookHeatPrediction::getHeatScore);

        List<BookHeatPrediction> result = bookHeatPredictionMapper.selectList(wrapper);
        return Result.success(result);
    }
}
