package com.library.controller;

import com.library.common.Result;
import com.library.entity.*;
import com.library.service.StatisticsService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import javax.annotation.Resource;
import java.util.List;
import java.util.Map;

/**
 * 统计分析控制器
 */
@Slf4j
@Api(tags = "统计分析")
@RestController
@RequestMapping("/statistics")
public class StatisticsController {

    @Resource
    private StatisticsService statisticsService;

    /**
     * 获取用户排名
     */
    @ApiOperation("获取用户排名")
    @GetMapping("/user-ranking/{userid}")
    public Result<UserRanking> getUserRanking(@PathVariable String userid) {
        log.info("获取用户排名：userid={}", userid);
        UserRanking ranking = statisticsService.getUserRanking(userid);
        return Result.success(ranking);
    }

    /**
     * 获取院系借阅汇总
     */
    @ApiOperation("获取院系借阅汇总")
    @GetMapping("/dept-summary")
    public Result<List<DeptLendSummary>> getDeptLendSummary() {
        log.info("获取院系借阅汇总");
        List<DeptLendSummary> list = statisticsService.getDeptLendSummary();
        return Result.success(list);
    }

    /**
     * 获取院系借阅偏好
     */
    @ApiOperation("获取院系借阅偏好")
    @GetMapping("/dept-preference/{dept}")
    public Result<DeptPreference> getDeptPreference(@PathVariable String dept) {
        log.info("获取院系借阅偏好：dept={}", dept);
        DeptPreference preference = statisticsService.getDeptPreference(dept);
        return Result.success(preference);
    }

    /**
     * 获取主题借阅汇总
     */
    @ApiOperation("获取主题借阅汇总")
    @GetMapping("/subject-summary")
    public Result<List<SubjectLendSummary>> getSubjectLendSummary() {
        log.info("获取主题借阅汇总");
        List<SubjectLendSummary> list = statisticsService.getSubjectLendSummary();
        return Result.success(list);
    }

    /**
     * 获取每日统计数据
     */
    @ApiOperation("获取每日统计数据")
    @GetMapping("/daily-stats")
    public Result<List<DailyStats>> getDailyStats(
            @RequestParam(defaultValue = "30") Integer days) {
        log.info("获取每日统计数据：days={}", days);
        List<DailyStats> list = statisticsService.getDailyStats(days);
        return Result.success(list);
    }

    /**
     * 获取活跃用户列表
     */
    @ApiOperation("获取活跃用户列表")
    @GetMapping("/active-users")
    public Result<List<ActiveUsers>> getActiveUsers(
            @RequestParam(defaultValue = "100") Integer limit) {
        log.info("获取活跃用户列表：limit={}", limit);
        List<ActiveUsers> list = statisticsService.getActiveUsers(limit);
        return Result.success(list);
    }

    /**
     * 获取借阅趋势
     */
    @ApiOperation("获取借阅趋势")
    @GetMapping("/lend-trend")
    public Result<List<LendTrend>> getLendTrend(
            @RequestParam(defaultValue = "30") Integer days) {
        log.info("获取借阅趋势：days={}", days);
        List<LendTrend> list = statisticsService.getLendTrend(days);
        return Result.success(list);
    }

    /**
     * 获取时间分布统计
     */
    @ApiOperation("获取时间分布统计")
    @GetMapping("/time-distribution")
    public Result<List<TimeDistribution>> getTimeDistribution(
            @RequestParam(required = false) String timeType) {
        log.info("获取时间分布统计：timeType={}", timeType);
        List<TimeDistribution> list = statisticsService.getTimeDistribution(timeType);
        return Result.success(list);
    }

    /**
     * 获取逾期分析
     */
    @ApiOperation("获取逾期分析")
    @GetMapping("/overdue-analysis")
    public Result<List<OverdueAnalysis>> getOverdueAnalysis(
            @RequestParam(required = false) String analysisType) {
        log.info("获取逾期分析：analysisType={}", analysisType);
        List<OverdueAnalysis> list = statisticsService.getOverdueAnalysis(analysisType);
        return Result.success(list);
    }

    /**
     * 获取用户画像数据(全部)
     */
    @ApiOperation("获取用户画像数据")
    @GetMapping("/user-profile")
    public Result<List<UserProfile>> getUserProfile() {
        log.info("获取用户画像数据");
        List<UserProfile> list = statisticsService.getUserProfile();
        return Result.success(list);
    }

    /**
     * 获取指定用户画像数据
     */
    @ApiOperation("获取指定用户画像数据")
    @GetMapping("/user-profile/{userid}")
    public Result<UserProfile> getUserProfileByUserid(@PathVariable String userid) {
        log.info("获取用户画像数据：userid={}", userid);
        UserProfile profile = statisticsService.getUserProfileByUserid(userid);
        return Result.success(profile);
    }

    /**
     * 获取运营看板数据
     */
    @ApiOperation("获取运营看板数据")
    @GetMapping("/operation-dashboard")
    public Result<List<OperationDashboard>> getOperationDashboard() {
        log.info("获取运营看板数据");
        List<OperationDashboard> list = statisticsService.getOperationDashboard();
        return Result.success(list);
    }

    /**
     * 获取馆藏利用分析
     */
    @ApiOperation("获取馆藏利用分析")
    @GetMapping("/collection-utilization")
    public Result<List<CollectionUtilizationAnalysis>> getCollectionUtilization(
            @RequestParam(required = false) String dimensionType) {
        log.info("获取馆藏利用分析：dimensionType={}", dimensionType);
        List<CollectionUtilizationAnalysis> list = statisticsService.getCollectionUtilization(dimensionType);
        return Result.success(list);
    }

    /**
     * 获取专业阅读特征
     */
    @ApiOperation("获取专业阅读特征")
    @GetMapping("/major-reading-profile")
    public Result<List<MajorReadingProfile>> getMajorReadingProfile() {
        log.info("获取专业阅读特征");
        List<MajorReadingProfile> list = statisticsService.getMajorReadingProfile();
        return Result.success(list);
    }

    /**
     * 获取推荐统计
     */
    @ApiOperation("获取推荐统计")
    @GetMapping("/recommendation-stats")
    public Result<List<RecommendationStats>> getRecommendationStats() {
        log.info("获取推荐统计");
        List<RecommendationStats> list = statisticsService.getRecommendationStats();
        return Result.success(list);
    }

    /**
     * 获取图书推荐基础数据(全部)
     */
    @ApiOperation("获取图书推荐基础数据")
    @GetMapping("/book-recommend-base")
    public Result<List<BookRecommendBase>> getBookRecommendBase() {
        log.info("获取图书推荐基础数据");
        List<BookRecommendBase> list = statisticsService.getBookRecommendBase();
        return Result.success(list);
    }

    /**
     * 获取院系推荐图书
     */
    @ApiOperation("获取院系推荐图书")
    @GetMapping("/dept-recommend-books")
    public Result<List<BookRecommendBase>> getDeptRecommendBooks(
            @RequestParam String dept,
            @RequestParam(defaultValue = "20") Integer limit) {
        log.info("获取院系推荐图书：dept={}, limit={}", dept, limit);
        List<BookRecommendBase> list = statisticsService.getDeptRecommendBooks(dept, limit);
        return Result.success(list);
    }

    /**
     * 获取借阅日历数据
     */
    @ApiOperation("获取借阅日历数据")
    @GetMapping("/borrow-calendar/{userid}")
    public Result<Map<String, Integer>> getBorrowCalendar(
            @PathVariable String userid,
            @RequestParam(required = false) String yearMonth) {
        log.info("获取借阅日历数据：userid={}, yearMonth={}", userid, yearMonth);
        Map<String, Integer> calendar = statisticsService.getBorrowCalendar(userid, yearMonth);
        return Result.success(calendar);
    }

    /**
     * 获取出版社分析
     */
    @ApiOperation("获取出版社分析")
    @GetMapping("/publisher-analysis")
    public Result<List<Map<String, Object>>> getPublisherAnalysis() {
        log.info("获取出版社分析");
        List<Map<String, Object>> list = statisticsService.getPublisherAnalysis();
        return Result.success(list);
    }

    /**
     * 获取出版年份分析
     */
    @ApiOperation("获取出版年份分析")
    @GetMapping("/publish-year-analysis")
    public Result<List<Map<String, Object>>> getPublishYearAnalysis() {
        log.info("获取出版年份分析");
        List<Map<String, Object>> list = statisticsService.getPublishYearAnalysis();
        return Result.success(list);
    }

    /**
     * 获取馆藏位置分析
     */
    @ApiOperation("获取馆藏位置分析")
    @GetMapping("/location-analysis")
    public Result<List<Map<String, Object>>> getLocationAnalysis() {
        log.info("获取馆藏位置分析");
        List<Map<String, Object>> list = statisticsService.getLocationAnalysis();
        return Result.success(list);
    }

    /**
     * 获取借阅时间分布
     */
    @ApiOperation("获取借阅时间分布")
    @GetMapping("/lend-time-distribution")
    public Result<List<Map<String, Object>>> getLendTimeDistribution() {
        log.info("获取借阅时间分布");
        List<Map<String, Object>> list = statisticsService.getLendTimeDistribution();
        return Result.success(list);
    }

    /**
     * 获取续借行为分析
     */
    @ApiOperation("获取续借行为分析")
    @GetMapping("/renew-analysis")
    public Result<Map<String, Object>> getRenewAnalysis() {
        log.info("获取续借行为分析");
        Map<String, Object> analysis = statisticsService.getRenewAnalysis();
        return Result.success(analysis);
    }
}
