package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.HotBooks;
import org.apache.ibatis.annotations.Mapper;

/**
 * 热门图书Mapper
 */
@Mapper
public interface HotBooksMapper extends BaseMapper<HotBooks> {
}
