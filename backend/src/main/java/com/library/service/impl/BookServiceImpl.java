package com.library.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.common.ResultCode;
import com.library.entity.BookDimension;
import com.library.entity.BookLendSummary;
import com.library.entity.HotBooks;
import com.library.exception.BusinessException;
import com.library.mapper.BookDimensionMapper;
import com.library.mapper.BookLendSummaryMapper;
import com.library.mapper.HotBooksMapper;
import com.library.service.BookService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 图书服务实现类
 */
@Slf4j
@Service
public class BookServiceImpl implements BookService {

    @Resource
    private HotBooksMapper hotBooksMapper;

    @Resource
    private BookDimensionMapper bookDimensionMapper;

    @Resource
    private BookLendSummaryMapper bookLendSummaryMapper;

    @Override
    public List<HotBooks> getHotBooks(Integer limit) {
        LambdaQueryWrapper<HotBooks> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByAsc(HotBooks::getRankNo)
                .last("LIMIT " + limit);
        return hotBooksMapper.selectList(wrapper);
    }

    @Override
    public Page<BookDimension> searchBooks(String keyword, Integer current, Integer size) {
        Page<BookDimension> page = new Page<>(current, size);
        LambdaQueryWrapper<BookDimension> wrapper = new LambdaQueryWrapper<>();
        
        if (StrUtil.isNotBlank(keyword)) {
            wrapper.and(w -> w.like(BookDimension::getTitle, keyword)
                    .or()
                    .like(BookDimension::getAuthor, keyword)
                    .or()
                    .like(BookDimension::getSubject, keyword));
        }
        
        return bookDimensionMapper.selectPage(page, wrapper);
    }

    @Override
    public BookDimension getBookDetail(String bookId) {
        BookDimension book = bookDimensionMapper.selectById(bookId);
        if (book == null) {
            throw new BusinessException(ResultCode.DATA_NOT_FOUND);
        }
        return book;
    }

    @Override
    public BookLendSummary getBookLendSummary(String bookId) {
        return bookLendSummaryMapper.selectById(bookId);
    }

    @Override
    public List<BookLendSummary> getBookRanking(String dimension, Integer limit) {
        LambdaQueryWrapper<BookLendSummary> wrapper = new LambdaQueryWrapper<>();
        
        // 根据维度排序
        if (StrUtil.isNotBlank(dimension)) {
            switch (dimension) {
                case "totalLendCount":
                    wrapper.orderByDesc(BookLendSummary::getTotalLendCount);
                    break;
                case "uniqueUserCount":
                    wrapper.orderByDesc(BookLendSummary::getUniqueUserCount);
                    break;
                case "lendFrequency":
                    wrapper.orderByDesc(BookLendSummary::getLendFrequency);
                    break;
                case "avgBorrowDays":
                    wrapper.orderByDesc(BookLendSummary::getAvgBorrowDays);
                    break;
                case "overdueRate":
                    wrapper.orderByDesc(BookLendSummary::getOverdueRate);
                    break;
                default:
                    wrapper.orderByDesc(BookLendSummary::getTotalLendCount);
            }
        } else {
            wrapper.orderByDesc(BookLendSummary::getTotalLendCount);
        }
        
        wrapper.last("LIMIT " + limit);
        return bookLendSummaryMapper.selectList(wrapper);
    }

    @Override
    public Map<String, Object> getBookHealthAnalysis(String bookId) {
        BookLendSummary summary = bookLendSummaryMapper.selectById(bookId);
        if (summary == null) {
            throw new BusinessException(ResultCode.DATA_NOT_FOUND);
        }
        
        Map<String, Object> result = new HashMap<>();
        result.put("summary", summary);
        
        // 计算健康度得分(0-100)
        double healthScore = 0;
        
        // 借阅次数得分(40分)
        if (summary.getTotalLendCount() != null) {
            if (summary.getTotalLendCount() >= 100) {
                healthScore += 40;
            } else if (summary.getTotalLendCount() >= 50) {
                healthScore += 30;
            } else if (summary.getTotalLendCount() >= 20) {
                healthScore += 20;
            } else if (summary.getTotalLendCount() >= 10) {
                healthScore += 10;
            }
        }
        
        // 借阅用户数得分(30分)
        if (summary.getUniqueUserCount() != null) {
            if (summary.getUniqueUserCount() >= 50) {
                healthScore += 30;
            } else if (summary.getUniqueUserCount() >= 20) {
                healthScore += 20;
            } else if (summary.getUniqueUserCount() >= 10) {
                healthScore += 10;
            } else if (summary.getUniqueUserCount() >= 5) {
                healthScore += 5;
            }
        }
        
        // 借阅频率得分(20分)
        if (summary.getLendFrequency() != null) {
            if (summary.getLendFrequency() >= 3.0) {
                healthScore += 20;
            } else if (summary.getLendFrequency() >= 2.0) {
                healthScore += 15;
            } else if (summary.getLendFrequency() >= 1.5) {
                healthScore += 10;
            } else if (summary.getLendFrequency() >= 1.0) {
                healthScore += 5;
            }
        }
        
        // 逾期率扣分(10分)
        if (summary.getOverdueRate() != null) {
            if (summary.getOverdueRate() <= 0.05) {
                healthScore += 10;
            } else if (summary.getOverdueRate() <= 0.1) {
                healthScore += 5;
            } else if (summary.getOverdueRate() > 0.3) {
                healthScore -= 10;
            }
        }
        
        healthScore = Math.max(0, Math.min(100, healthScore));
        result.put("healthScore", healthScore);
        
        // 健康度等级
        String healthLevel;
        if (healthScore >= 80) {
            healthLevel = "优秀";
        } else if (healthScore >= 60) {
            healthLevel = "良好";
        } else if (healthScore >= 40) {
            healthLevel = "一般";
        } else {
            healthLevel = "较差";
        }
        result.put("healthLevel", healthLevel);
        
        return result;
    }
}
