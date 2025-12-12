package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.UserProfile;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户画像Mapper
 */
@Mapper
public interface UserProfileMapper extends BaseMapper<UserProfile> {
}
