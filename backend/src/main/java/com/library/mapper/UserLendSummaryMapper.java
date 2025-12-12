package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.UserLendSummary;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户借阅汇总Mapper
 */
@Mapper
public interface UserLendSummaryMapper extends BaseMapper<UserLendSummary> {
}
