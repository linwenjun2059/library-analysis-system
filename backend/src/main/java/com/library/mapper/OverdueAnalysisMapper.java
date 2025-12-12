package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.OverdueAnalysis;
import org.apache.ibatis.annotations.Mapper;

/**
 * 逾期分析Mapper
 */
@Mapper
public interface OverdueAnalysisMapper extends BaseMapper<OverdueAnalysis> {
}
