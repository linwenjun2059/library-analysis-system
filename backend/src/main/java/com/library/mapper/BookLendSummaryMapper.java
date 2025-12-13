package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.BookLendSummary;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 图书借阅汇总Mapper
 */
@Mapper
public interface BookLendSummaryMapper extends BaseMapper<BookLendSummary> {

    /**
     * 获取图书排行榜（带书名）
     */
    @Select("SELECT s.*, d.title, d.author, d.subject " +
            "FROM book_lend_summary s " +
            "LEFT JOIN book_dimension d ON s.book_id = d.book_id " +
            "ORDER BY ${orderField} DESC " +
            "LIMIT #{limit}")
    List<BookLendSummary> selectRankingWithTitle(@Param("orderField") String orderField, @Param("limit") Integer limit);
}
