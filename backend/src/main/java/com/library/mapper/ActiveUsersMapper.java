package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.ActiveUsers;
import org.apache.ibatis.annotations.Mapper;

/**
 * 活跃用户Mapper
 */
@Mapper
public interface ActiveUsersMapper extends BaseMapper<ActiveUsers> {
}
