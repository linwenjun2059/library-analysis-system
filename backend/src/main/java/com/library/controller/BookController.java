package com.library.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.common.Result;
import com.library.entity.BookDimension;
import com.library.entity.BookLendSummary;
import com.library.entity.HotBooks;
import com.library.service.BookService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import javax.annotation.Resource;
import java.util.List;
import java.util.Map;

/**
 * 图书控制器
 */
@Slf4j
@Api(tags = "图书管理")
@RestController
@RequestMapping("/book")
public class BookController {

    @Resource
    private BookService bookService;

    /**
     * 获取热门图书
     */
    @ApiOperation("获取热门图书")
    @GetMapping("/hot")
    public Result<List<HotBooks>> getHotBooks(@RequestParam(defaultValue = "100") Integer limit) {
        log.info("获取热门图书：limit={}", limit);
        List<HotBooks> hotBooks = bookService.getHotBooks(limit);
        return Result.success(hotBooks);
    }

    /**
     * 搜索图书
     */
    @ApiOperation("搜索图书")
    @GetMapping("/search")
    public Result<Page<BookDimension>> searchBooks(
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "10") Integer size) {
        log.info("搜索图书：keyword={}, current={}, size={}", keyword, current, size);
        Page<BookDimension> page = bookService.searchBooks(keyword, current, size);
        return Result.success(page);
    }

    /**
     * 获取图书详情
     */
    @ApiOperation("获取图书详情")
    @GetMapping("/detail/{bookId}")
    public Result<BookDimension> getBookDetail(@PathVariable String bookId) {
        log.info("获取图书详情：bookId={}", bookId);
        BookDimension book = bookService.getBookDetail(bookId);
        return Result.success(book);
    }

    /**
     * 获取图书借阅统计
     */
    @ApiOperation("获取图书借阅统计")
    @GetMapping("/summary/{bookId}")
    public Result<BookLendSummary> getBookLendSummary(@PathVariable String bookId) {
        log.info("获取图书借阅统计：bookId={}", bookId);
        BookLendSummary summary = bookService.getBookLendSummary(bookId);
        return Result.success(summary);
    }

    /**
     * 获取图书排行榜（多维度）
     */
    @ApiOperation("获取图书排行榜")
    @GetMapping("/ranking")
    public Result<List<BookLendSummary>> getBookRanking(
            @RequestParam(required = false, defaultValue = "totalLendCount") String dimension,
            @RequestParam(defaultValue = "20") Integer limit) {
        log.info("获取图书排行榜：dimension={}, limit={}", dimension, limit);
        List<BookLendSummary> list = bookService.getBookRanking(dimension, limit);
        return Result.success(list);
    }

    /**
     * 获取图书健康度分析
     */
    @ApiOperation("获取图书健康度分析")
    @GetMapping("/health-analysis/{bookId}")
    public Result<Map<String, Object>> getBookHealthAnalysis(@PathVariable String bookId) {
        log.info("获取图书健康度分析：bookId={}", bookId);
        Map<String, Object> analysis = bookService.getBookHealthAnalysis(bookId);
        return Result.success(analysis);
    }
}
