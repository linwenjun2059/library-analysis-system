package com.library.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.entity.BookDimension;
import com.library.entity.BookLendSummary;
import com.library.entity.HotBooks;

import java.util.List;
import java.util.Map;

/**
 * 图书服务接口
 */
public interface BookService {

    /**
     * 获取热门图书
     */
    List<HotBooks> getHotBooks(Integer limit);

    /**
     * 搜索图书
     */
    Page<BookDimension> searchBooks(String keyword, Integer current, Integer size);

    /**
     * 获取图书详情
     */
    BookDimension getBookDetail(String bookId);

    /**
     * 获取图书借阅汇总
     */
    BookLendSummary getBookLendSummary(String bookId);

    /**
     * 获取图书排行榜(多维度)
     * @param dimension 排序维度：totalLendCount, uniqueUserCount, lendFrequency, avgBorrowDays, overdueRate
     * @param limit 返回数量
     */
    List<BookLendSummary> getBookRanking(String dimension, Integer limit);

    /**
     * 获取图书健康度分析
     */
    Map<String, Object> getBookHealthAnalysis(String bookId);
}
