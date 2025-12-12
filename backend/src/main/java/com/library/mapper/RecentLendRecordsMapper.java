package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.RecentLendRecords;
import org.apache.ibatis.annotations.Mapper;

/**
 * 近期借阅记录Mapper
 */
@Mapper
public interface RecentLendRecordsMapper extends BaseMapper<RecentLendRecords> {
}
