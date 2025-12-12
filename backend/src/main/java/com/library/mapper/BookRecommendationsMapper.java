package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.BookRecommendations;
import org.apache.ibatis.annotations.Mapper;

/**
 * 图书推荐Mapper
 */
@Mapper
public interface BookRecommendationsMapper extends BaseMapper<BookRecommendations> {
}
