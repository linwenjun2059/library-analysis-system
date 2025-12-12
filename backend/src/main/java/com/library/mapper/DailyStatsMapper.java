package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.DailyStats;
import org.apache.ibatis.annotations.Mapper;

/**
 * 每日统计Mapper
 */
@Mapper
public interface DailyStatsMapper extends BaseMapper<DailyStats> {
}
