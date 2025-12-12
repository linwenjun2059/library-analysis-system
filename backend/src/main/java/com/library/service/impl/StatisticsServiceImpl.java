package com.library.service.impl;

import cn.hutool.core.date.DateUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.library.entity.*;
import com.library.mapper.*;
import com.library.service.StatisticsService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 统计分析服务实现类
 *
 * @author Lin Wenjun
 * @since 2025
 */
@Slf4j
@Service
public class StatisticsServiceImpl implements StatisticsService {

    @Resource
    private UserRankingMapper userRankingMapper;

    @Resource
    private DeptLendSummaryMapper deptLendSummaryMapper;

    @Resource
    private DeptPreferenceMapper deptPreferenceMapper;

    @Resource
    private SubjectLendSummaryMapper subjectLendSummaryMapper;

    @Resource
    private DailyStatsMapper dailyStatsMapper;

    @Resource
    private ActiveUsersMapper activeUsersMapper;

    @Resource
    private LendTrendMapper lendTrendMapper;

    @Resource
    private TimeDistributionMapper timeDistributionMapper;

    @Resource
    private OverdueAnalysisMapper overdueAnalysisMapper;

    @Resource
    private OperationDashboardMapper operationDashboardMapper;

    @Resource
    private CollectionUtilizationAnalysisMapper collectionUtilizationAnalysisMapper;

    @Resource
    private MajorReadingProfileMapper majorReadingProfileMapper;

    @Resource
    private RecommendationStatsMapper recommendationStatsMapper;

    @Resource
    private BookRecommendBaseMapper bookRecommendBaseMapper;

    @Resource
    private RecentLendRecordsMapper recentLendRecordsMapper;

    @Resource
    private UserProfileMapper userProfileMapper;

    @Resource
    private BookDimensionMapper bookDimensionMapper;

    @Resource
    private BookLendSummaryMapper bookLendSummaryMapper;

    @Override
    public UserRanking getUserRanking(String userid) {
        return userRankingMapper.selectById(userid);
    }

    @Override
    public List<DeptLendSummary> getDeptLendSummary() {
        LambdaQueryWrapper<DeptLendSummary> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(DeptLendSummary::getTotalLendCount);
        return deptLendSummaryMapper.selectList(wrapper);
    }

    @Override
    public DeptPreference getDeptPreference(String dept) {
        return deptPreferenceMapper.selectById(dept);
    }

    @Override
    public List<SubjectLendSummary> getSubjectLendSummary() {
        LambdaQueryWrapper<SubjectLendSummary> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(SubjectLendSummary::getTotalLendCount);
        return subjectLendSummaryMapper.selectList(wrapper);
    }

    @Override
    public List<DailyStats> getDailyStats(Integer days) {
        LambdaQueryWrapper<DailyStats> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(DailyStats::getStatDate)
                .last("LIMIT " + days);
        List<DailyStats> list = dailyStatsMapper.selectList(wrapper);
        Collections.reverse(list);
        return list;
    }

    @Override
    public List<ActiveUsers> getActiveUsers(Integer limit) {
        LambdaQueryWrapper<ActiveUsers> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByAsc(ActiveUsers::getRankNo)
                .last("LIMIT " + limit);
        return activeUsersMapper.selectList(wrapper);
    }

    @Override
    public List<LendTrend> getLendTrend(Integer days) {
        LambdaQueryWrapper<LendTrend> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(LendTrend::getTrendDate)
                .last("LIMIT " + days);
        List<LendTrend> list = lendTrendMapper.selectList(wrapper);
        Collections.reverse(list);
        return list;
    }

    @Override
    public List<TimeDistribution> getTimeDistribution(String timeType) {
        LambdaQueryWrapper<TimeDistribution> wrapper = new LambdaQueryWrapper<>();
        // 如果指定了时间类型，则按类型过滤，否则查询所有
        if (timeType != null && !timeType.isEmpty()) {
            wrapper.eq(TimeDistribution::getTimeType, timeType);
        }
        wrapper.orderByAsc(TimeDistribution::getTimeType, TimeDistribution::getTimeValue);
        return timeDistributionMapper.selectList(wrapper);
    }

    @Override
    public List<OverdueAnalysis> getOverdueAnalysis(String analysisType) {
        LambdaQueryWrapper<OverdueAnalysis> wrapper = new LambdaQueryWrapper<>();
        if (analysisType != null) {
            wrapper.eq(OverdueAnalysis::getAnalysisType, analysisType);
        }
        wrapper.orderByDesc(OverdueAnalysis::getOverdueRate);
        return overdueAnalysisMapper.selectList(wrapper);
    }

    @Override
    public List<OperationDashboard> getOperationDashboard() {
        return operationDashboardMapper.selectList(null);
    }

    @Override
    public List<CollectionUtilizationAnalysis> getCollectionUtilization(String dimensionType) {
        LambdaQueryWrapper<CollectionUtilizationAnalysis> wrapper = new LambdaQueryWrapper<>();
        if (dimensionType != null) {
            wrapper.eq(CollectionUtilizationAnalysis::getDimensionType, dimensionType);
        }
        wrapper.orderByDesc(CollectionUtilizationAnalysis::getTurnoverRate);
        return collectionUtilizationAnalysisMapper.selectList(wrapper);
    }

    @Override
    public List<MajorReadingProfile> getMajorReadingProfile() {
        LambdaQueryWrapper<MajorReadingProfile> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(MajorReadingProfile::getAvgBorrowPerStudent);
        return majorReadingProfileMapper.selectList(wrapper);
    }

    @Override
    public List<RecommendationStats> getRecommendationStats() {
        return recommendationStatsMapper.selectList(null);
    }

    @Override
    public List<BookRecommendBase> getBookRecommendBase() {
        return bookRecommendBaseMapper.selectList(null);
    }

    @Override
    public List<BookRecommendBase> getDeptRecommendBooks(String dept, Integer limit) {
        LambdaQueryWrapper<BookRecommendBase> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(BookRecommendBase::getScope, dept)
                .eq(BookRecommendBase::getRecommendType, "院系榜")
                .orderByAsc(BookRecommendBase::getRankNo)
                .last("LIMIT " + limit);
        return bookRecommendBaseMapper.selectList(wrapper);
    }

    @Override
    public Map<String, Integer> getBorrowCalendar(String userid, String yearMonth) {
        LambdaQueryWrapper<RecentLendRecords> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(RecentLendRecords::getUserid, userid);
        
        // 支持按月查询
        if (yearMonth != null) {
            if (yearMonth.matches("\\d{4}")) {
                // 支持按年或按月查询
                int year = Integer.parseInt(yearMonth);
                Date startDate = DateUtil.parse(year + "-01-01");
                Date endDate = DateUtil.parse(year + "-12-31");
                wrapper.between(RecentLendRecords::getLendDate, startDate, endDate);
            } else if (yearMonth.matches("\\d{4}-\\d{2}")) {
                // 按月查询
                Date startDate = DateUtil.beginOfMonth(DateUtil.parse(yearMonth + "-01"));
                Date endDate = DateUtil.endOfMonth(startDate);
                wrapper.between(RecentLendRecords::getLendDate, startDate, endDate);
            }
        }
        
        List<RecentLendRecords> records = recentLendRecordsMapper.selectList(wrapper);
        
        // 统计每天的借阅次数
        return records.stream()
                .collect(Collectors.groupingBy(
                        record -> DateUtil.formatDate(record.getLendDate()),
                        Collectors.collectingAndThen(Collectors.counting(), Long::intValue)
                ));
    }

    @Override
    public List<UserProfile> getUserProfile() {
        return userProfileMapper.selectList(null);
    }

    @Override
    public UserProfile getUserProfileByUserid(String userid) {
        return userProfileMapper.selectById(userid);
    }

    @Override
    public List<Map<String, Object>> getPublisherAnalysis() {
        List<BookDimension> books = bookDimensionMapper.selectList(null);
        List<BookLendSummary> summaries = bookLendSummaryMapper.selectList(null);
        
        // 创建图书ID到借阅汇总的映射
        Map<String, BookLendSummary> summaryMap = summaries.stream()
                .collect(Collectors.toMap(BookLendSummary::getBookId, s -> s));
        
        // 按出版社分组统计
        Map<String, Map<String, Object>> publisherMap = new HashMap<>();
        
        for (BookDimension book : books) {
            if (book.getPublisher() == null || book.getPublisher().isEmpty()) {
                continue;
            }
            
            String publisher = book.getPublisher();
            BookLendSummary summary = summaryMap.get(book.getBookId());
            
            publisherMap.computeIfAbsent(publisher, k -> {
                Map<String, Object> stats = new HashMap<>();
                stats.put("publisher", publisher);
                stats.put("bookCount", 0L);
                stats.put("totalLendCount", 0L);
                stats.put("totalUserCount", 0L);
                return stats;
            });
            
            Map<String, Object> stats = publisherMap.get(publisher);
            stats.put("bookCount", ((Long) stats.get("bookCount")) + 1);
            
            if (summary != null) {
                stats.put("totalLendCount", ((Long) stats.get("totalLendCount")) + 
                        (summary.getTotalLendCount() != null ? summary.getTotalLendCount() : 0));
                stats.put("totalUserCount", ((Long) stats.get("totalUserCount")) + 
                        (summary.getUniqueUserCount() != null ? summary.getUniqueUserCount() : 0));
            }
        }
        
        // 计算平均借阅次数并排序
        return publisherMap.values().stream()
                .peek(stats -> {
                    Long bookCount = (Long) stats.get("bookCount");
                    if (bookCount > 0) {
                        Long totalLend = (Long) stats.get("totalLendCount");
                        stats.put("avgLendCount", totalLend.doubleValue() / bookCount);
                    } else {
                        stats.put("avgLendCount", 0.0);
                    }
                })
                .sorted((a, b) -> Long.compare((Long) b.get("totalLendCount"), (Long) a.get("totalLendCount")))
                .limit(20)
                .collect(Collectors.toList());
    }

    @Override
    public List<Map<String, Object>> getPublishYearAnalysis() {
        List<BookDimension> books = bookDimensionMapper.selectList(null);
        List<BookLendSummary> summaries = bookLendSummaryMapper.selectList(null);
        
        Map<String, BookLendSummary> summaryMap = summaries.stream()
                .collect(Collectors.toMap(BookLendSummary::getBookId, s -> s));
        
        Map<Integer, Map<String, Object>> yearMap = new HashMap<>();
        
        for (BookDimension book : books) {
            if (book.getPubYear() == null) {
                continue;
            }
            
            Integer year = book.getPubYear();
            BookLendSummary summary = summaryMap.get(book.getBookId());
            
            yearMap.computeIfAbsent(year, k -> {
                Map<String, Object> stats = new HashMap<>();
                stats.put("year", year);
                stats.put("bookCount", 0L);
                stats.put("totalLendCount", 0L);
                return stats;
            });
            
            Map<String, Object> stats = yearMap.get(year);
            stats.put("bookCount", ((Long) stats.get("bookCount")) + 1);
            
            if (summary != null && summary.getTotalLendCount() != null) {
                stats.put("totalLendCount", ((Long) stats.get("totalLendCount")) + summary.getTotalLendCount());
            }
        }
        
        return yearMap.values().stream()
                .sorted((a, b) -> Integer.compare((Integer) b.get("year"), (Integer) a.get("year")))
                .collect(Collectors.toList());
    }

    @Override
    public List<Map<String, Object>> getLocationAnalysis() {
        List<BookDimension> books = bookDimensionMapper.selectList(null);
        List<BookLendSummary> summaries = bookLendSummaryMapper.selectList(null);
        
        Map<String, BookLendSummary> summaryMap = summaries.stream()
                .collect(Collectors.toMap(BookLendSummary::getBookId, s -> s));
        
        Map<String, Map<String, Object>> locationMap = new HashMap<>();
        
        for (BookDimension book : books) {
            if (book.getLocationName() == null || book.getLocationName().isEmpty()) {
                continue;
            }
            
            String location = book.getLocationName();
            BookLendSummary summary = summaryMap.get(book.getBookId());
            
            locationMap.computeIfAbsent(location, k -> {
                Map<String, Object> stats = new HashMap<>();
                stats.put("location", location);
                stats.put("bookCount", 0L);
                stats.put("totalLendCount", 0L);
                stats.put("borrowedBooks", 0L);
                return stats;
            });
            
            Map<String, Object> stats = locationMap.get(location);
            stats.put("bookCount", ((Long) stats.get("bookCount")) + 1);
            
            if (summary != null) {
                if (summary.getTotalLendCount() != null && summary.getTotalLendCount() > 0) {
                    stats.put("borrowedBooks", ((Long) stats.get("borrowedBooks")) + 1);
                    stats.put("totalLendCount", ((Long) stats.get("totalLendCount")) + summary.getTotalLendCount());
                }
            }
        }
        
        return locationMap.values().stream()
                .peek(stats -> {
                    Long bookCount = (Long) stats.get("bookCount");
                    Long borrowedBooks = (Long) stats.get("borrowedBooks");
                    if (bookCount > 0) {
                        stats.put("circulationRate", borrowedBooks.doubleValue() / bookCount);
                    } else {
                        stats.put("circulationRate", 0.0);
                    }
                })
                .sorted((a, b) -> Long.compare((Long) b.get("totalLendCount"), (Long) a.get("totalLendCount")))
                .collect(Collectors.toList());
    }

    @Override
    public List<Map<String, Object>> getLendTimeDistribution() {
        List<RecentLendRecords> records = recentLendRecordsMapper.selectList(null);
        
        // 按小时统计借阅次数
        Map<Integer, Long> hourCountMap = records.stream()
                .filter(r -> r.getLendTime() != null && !r.getLendTime().isEmpty())
                .collect(Collectors.groupingBy(
                        r -> {
                            try {
                                String time = r.getLendTime();
                                if (time.contains(":")) {
                                    return Integer.parseInt(time.split(":")[0]);
                                }
                            } catch (Exception e) {
                                // 忽略解析错误
                            }
                            return 0;
                        },
                        Collectors.counting()
                ));
        
        List<Map<String, Object>> result = new ArrayList<>();
        for (int hour = 0; hour < 24; hour++) {
            Map<String, Object> hourData = new HashMap<>();
            hourData.put("hour", hour);
            hourData.put("count", hourCountMap.getOrDefault(hour, 0L));
            result.add(hourData);
        }
        
        return result;
    }

    @Override
    public Map<String, Object> getRenewAnalysis() {
        List<RecentLendRecords> records = recentLendRecordsMapper.selectList(null);
        
        long totalRecords = records.size();
        long renewRecords = records.stream()
                .filter(r -> r.getRenewTimes() != null && r.getRenewTimes() > 0)
                .count();
        
        double renewRate = totalRecords > 0 ? (double) renewRecords / totalRecords : 0.0;
        
        // 续借次数分布
        Map<Integer, Long> renewTimesDistribution = records.stream()
                .filter(r -> r.getRenewTimes() != null)
                .collect(Collectors.groupingBy(
                        RecentLendRecords::getRenewTimes,
                        Collectors.counting()
                ));
        
        // 平均续借次数
        double avgRenewTimes = records.stream()
                .filter(r -> r.getRenewTimes() != null)
                .mapToInt(RecentLendRecords::getRenewTimes)
                .average()
                .orElse(0.0);
        
        Map<String, Object> result = new HashMap<>();
        result.put("totalRecords", totalRecords);
        result.put("renewRecords", renewRecords);
        result.put("renewRate", renewRate);
        result.put("avgRenewTimes", avgRenewTimes);
        result.put("renewTimesDistribution", renewTimesDistribution);
        
        return result;
    }
}
