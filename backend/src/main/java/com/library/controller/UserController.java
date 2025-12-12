package com.library.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.common.Result;
import com.library.entity.*;
import com.library.service.UserService;
import com.library.vo.UserProfileVO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import javax.annotation.Resource;
import java.util.List;

/**
 * 用户控制器
 */
@Slf4j
@Api(tags = "用户管理")
@RestController
@RequestMapping("/user")
public class UserController {

    @Resource
    private UserService userService;

    /**
     * 获取用户画像
     */
    @ApiOperation("获取用户画像")
    @GetMapping("/profile/{userid}")
    public Result<UserProfileVO> getUserProfile(@PathVariable String userid) {
        log.info("获取用户画像：userid={}", userid);
        UserProfileVO profile = userService.getUserProfile(userid);
        return Result.success(profile);
    }

    /**
     * 获取用户借阅汇总
     */
    @ApiOperation("获取用户借阅汇总")
    @GetMapping("/summary/{userid}")
    public Result<UserLendSummary> getUserLendSummary(@PathVariable String userid) {
        log.info("获取用户借阅汇总：userid={}", userid);
        UserLendSummary summary = userService.getUserLendSummary(userid);
        return Result.success(summary);
    }

    /**
     * 获取用户借阅记录（分页）
     */
    @ApiOperation("获取用户借阅记录")
    @GetMapping("/records/{userid}")
    public Result<Page<RecentLendRecords>> getUserLendRecords(
            @PathVariable String userid,
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "10") Integer size) {
        log.info("获取用户借阅记录：userid={}, current={}, size={}", userid, current, size);
        Page<RecentLendRecords> page = userService.getUserLendRecords(userid, current, size);
        return Result.success(page);
    }

    /**
     * 管理员查询所有借阅记录
     */
    @ApiOperation("查询所有借阅记录")
    @GetMapping("/all-records")
    public Result<Page<RecentLendRecords>> getAllLendRecords(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate,
            @RequestParam(required = false) String returnStatus,
            @RequestParam(required = false) String overdueStatus,
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "10") Integer size) {
        log.info("查询所有借阅记录：keyword={}, startDate={}, endDate={}, returnStatus={}, overdueStatus={}, current={}, size={}",
                keyword, startDate, endDate, returnStatus, overdueStatus, current, size);
        Page<RecentLendRecords> page = userService.getAllLendRecords(keyword, startDate, endDate, returnStatus, overdueStatus, current, size);
        return Result.success(page);
    }

    /**
     * 获取用户推荐图书
     */
    @ApiOperation("获取用户推荐图书")
    @GetMapping("/recommendations/{userid}")
    public Result<List<BookRecommendations>> getUserRecommendations(
            @PathVariable String userid,
            @RequestParam(defaultValue = "20") Integer limit) {
        log.info("获取用户推荐图书：userid={}, limit={}", userid, limit);
        List<BookRecommendations> recommendations = userService.getUserRecommendations(userid, limit);
        return Result.success(recommendations);
    }

    /**
     * 获取用户维度信息
     */
    @ApiOperation("获取用户维度信息")
    @GetMapping("/dimension/{userid}")
    public Result<UserDimension> getUserDimension(@PathVariable String userid) {
        log.info("获取用户维度信息：userid={}", userid);
        UserDimension dimension = userService.getUserDimension(userid);
        return Result.success(dimension);
    }
}
