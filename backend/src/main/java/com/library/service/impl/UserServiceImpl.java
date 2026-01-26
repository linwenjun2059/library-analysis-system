package com.library.service.impl;

import cn.hutool.core.date.DateUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.common.ResultCode;
import com.library.entity.*;
import com.library.exception.BusinessException;
import com.library.mapper.*;
import com.library.service.UserService;
import com.library.vo.UserProfileVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

/**
 * 用户服务实现类
 */
@Slf4j
@Service
public class UserServiceImpl implements UserService {

    @Resource
    private UserProfileMapper userProfileMapper;

    @Resource
    private UserLendSummaryMapper userLendSummaryMapper;

    @Resource
    private RecentLendRecordsMapper recentLendRecordsMapper;

    @Resource
    private BookRecommendationsMapper bookRecommendationsMapper;

    @Resource
    private UserDimensionMapper userDimensionMapper;

    @Override
    public UserProfileVO getUserProfile(String userid) {
        UserProfile userProfile = userProfileMapper.selectById(userid);
        if (userProfile == null) {
            throw new BusinessException(ResultCode.DATA_NOT_FOUND);
        }

        UserProfileVO vo = new UserProfileVO();
        BeanUtils.copyProperties(userProfile, vo);

        // 解析JSON字段
        if (StrUtil.isNotBlank(userProfile.getFavoriteSubjects())) {
            vo.setFavoriteSubjects(JSONUtil.parse(userProfile.getFavoriteSubjects()));
        }
        if (StrUtil.isNotBlank(userProfile.getFavoriteLocations())) {
            vo.setFavoriteLocations(JSONUtil.parse(userProfile.getFavoriteLocations()));
        }
        if (StrUtil.isNotBlank(userProfile.getUserTags())) {
            vo.setUserTags(JSONUtil.parse(userProfile.getUserTags()));
        }

        return vo;
    }

    @Override
    public UserLendSummary getUserLendSummary(String userid) {
        UserLendSummary summary = userLendSummaryMapper.selectById(userid);
        if (summary == null) {
            throw new BusinessException(ResultCode.DATA_NOT_FOUND);
        }
        return summary;
    }

    @Override
    public Page<RecentLendRecords> getUserLendRecords(String userid, Integer current, Integer size) {
        Page<RecentLendRecords> page = new Page<>(current, size);
        // 使用关联查询，获取图书信息
        return recentLendRecordsMapper.selectUserRecordsWithBookInfo(page, userid);
    }

    @Override
    public Page<RecentLendRecords> getAllLendRecords(String keyword, String startDate, String endDate, String returnStatus, String overdueStatus, Integer current, Integer size) {
        Page<RecentLendRecords> page = new Page<>(current, size);
        // 使用关联查询，获取图书信息，并支持按书名搜索
        return recentLendRecordsMapper.selectAllRecordsWithBookInfo(page, keyword, startDate, endDate, returnStatus, overdueStatus);
    }

    @Override
    public List<BookRecommendations> getUserRecommendations(String userid, Integer limit) {
        LambdaQueryWrapper<BookRecommendations> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(BookRecommendations::getUserid, userid)
                .orderByAsc(BookRecommendations::getRankNo)
                .last("LIMIT " + limit);
        return bookRecommendationsMapper.selectList(wrapper);
    }

    @Override
    public UserDimension getUserDimension(String userid) {
        return userDimensionMapper.selectById(userid);
    }
}
