package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.BookDimension;
import org.apache.ibatis.annotations.Mapper;

/**
 * 图书维度Mapper
 */
@Mapper
public interface BookDimensionMapper extends BaseMapper<BookDimension> {
}
