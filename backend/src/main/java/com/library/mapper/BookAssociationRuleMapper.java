package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.library.entity.BookAssociationRule;
import org.apache.ibatis.annotations.Mapper;

/**
 * 图书关联规则Mapper
 */
@Mapper
public interface BookAssociationRuleMapper extends BaseMapper<BookAssociationRule> {
}
