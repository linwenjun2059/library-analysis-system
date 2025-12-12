package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.RecommendationStats;
import org.apache.ibatis.annotations.Mapper;

/**
 * 推荐效果统计Mapper
 */
@Mapper
public interface RecommendationStatsMapper extends BaseMapper<RecommendationStats> {
}
