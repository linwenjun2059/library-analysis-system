package com.library.service;

import com.library.entity.*;

import java.util.List;
import java.util.Map;

/**
 * 统计分析服务接口
 */
public interface StatisticsService {

    /**
     * 获取用户排名信息
     */
    UserRanking getUserRanking(String userid);

    /**
     * 获取院系借阅汇总
     */
    List<DeptLendSummary> getDeptLendSummary();

    /**
     * 获取院系偏好
     */
    DeptPreference getDeptPreference(String dept);

    /**
     * 获取主题借阅汇总
     */
    List<SubjectLendSummary> getSubjectLendSummary();

    /**
     * 获取每日统计数据
     */
    List<DailyStats> getDailyStats(Integer days);

    /**
     * 获取活跃用户列表
     */
    List<ActiveUsers> getActiveUsers(Integer limit);

    /**
     * 获取借阅趋势数据
     */
    List<LendTrend> getLendTrend(Integer days);

    /**
     * 获取时间分布统计
     */
    List<TimeDistribution> getTimeDistribution(String timeType);

    /**
     * 获取逾期分析数据
     */
    List<OverdueAnalysis> getOverdueAnalysis(String analysisType);

    /**
     * 获取运营看板数据
     */
    List<OperationDashboard> getOperationDashboard();

    /**
     * 获取馆藏利用分析
     */
    List<CollectionUtilizationAnalysis> getCollectionUtilization(String dimensionType);

    /**
     * 获取专业阅读特征
     */
    List<MajorReadingProfile> getMajorReadingProfile();

    /**
     * 获取推荐统计数据
     */
    List<RecommendationStats> getRecommendationStats();

    /**
     * 获取图书推荐基础数据
     */
    List<BookRecommendBase> getBookRecommendBase();

    /**
     * 获取院系推荐图书
     */
    List<BookRecommendBase> getDeptRecommendBooks(String dept, Integer limit);

    /**
     * 获取借阅日历数据(按月份)
     */
    Map<String, Integer> getBorrowCalendar(String userid, String yearMonth);

    /**
     * 获取用户画像数据
     */
    List<UserProfile> getUserProfile();

    /**
     * 获取指定用户的画像数据
     */
    UserProfile getUserProfileByUserid(String userid);

    /**
     * 获取出版社分析数据
     */
    List<Map<String, Object>> getPublisherAnalysis();

    /**
     * 获取出版年份分析数据
     */
    List<Map<String, Object>> getPublishYearAnalysis();

    /**
     * 获取借阅时间分布(按小时)
     */
    List<Map<String, Object>> getLendTimeDistribution();

    /**
     * 获取续借行为分析
     */
    Map<String, Object> getRenewAnalysis();
}
