package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.UserRanking;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户排名Mapper
 */
@Mapper
public interface UserRankingMapper extends BaseMapper<UserRanking> {
}
