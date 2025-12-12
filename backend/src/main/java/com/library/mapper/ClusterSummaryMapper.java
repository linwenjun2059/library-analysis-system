package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.ClusterSummary;
import org.apache.ibatis.annotations.Mapper;

/**
 * 聚类统计摘要Mapper
 */
@Mapper
public interface ClusterSummaryMapper extends BaseMapper<ClusterSummary> {
}
