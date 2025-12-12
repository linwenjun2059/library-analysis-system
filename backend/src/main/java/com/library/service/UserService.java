package com.library.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.entity.*;
import com.library.vo.UserProfileVO;

import java.util.List;

/**
 * 用户服务接口
 */
public interface UserService {

    /**
     * 获取用户画像
     */
    UserProfileVO getUserProfile(String userid);

    /**
     * 获取用户借阅汇总
     */
    UserLendSummary getUserLendSummary(String userid);

    /**
     * 获取用户借阅记录(分页)
     */
    Page<RecentLendRecords> getUserLendRecords(String userid, Integer current, Integer size);

    /**
     * 管理员查询所有借阅记录(支持搜索、日期范围、归还状态和逾期状态)
     */
    Page<RecentLendRecords> getAllLendRecords(String keyword, String startDate, String endDate, String returnStatus, String overdueStatus, Integer current, Integer size);

    /**
     * 获取用户推荐图书
     */
    List<BookRecommendations> getUserRecommendations(String userid, Integer limit);

    /**
     * 获取用户维度信息
     */
    UserDimension getUserDimension(String userid);
}
