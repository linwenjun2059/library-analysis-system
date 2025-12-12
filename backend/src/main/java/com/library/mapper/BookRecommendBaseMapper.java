package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.BookRecommendBase;
import org.apache.ibatis.annotations.Mapper;

/**
 * 图书推荐基础Mapper
 */
@Mapper
public interface BookRecommendBaseMapper extends BaseMapper<BookRecommendBase> {
}
