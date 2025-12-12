package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.DeptLendSummary;
import org.apache.ibatis.annotations.Mapper;

/**
 * 院系借阅汇总Mapper
 */
@Mapper
public interface DeptLendSummaryMapper extends BaseMapper<DeptLendSummary> {
}
