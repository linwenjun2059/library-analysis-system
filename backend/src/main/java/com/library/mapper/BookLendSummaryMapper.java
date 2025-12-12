package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.BookLendSummary;
import org.apache.ibatis.annotations.Mapper;

/**
 * 图书借阅汇总Mapper
 */
@Mapper
public interface BookLendSummaryMapper extends BaseMapper<BookLendSummary> {
}
