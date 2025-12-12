package com.library.service.impl;

import cn.hutool.core.bean.BeanUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.library.common.ResultCode;
import com.library.dto.LoginDTO;
import com.library.entity.SysUser;
import com.library.entity.UserDimension;
import com.library.exception.BusinessException;
import com.library.mapper.SysUserMapper;
import com.library.mapper.UserDimensionMapper;
import com.library.service.AuthService;
import com.library.utils.JwtUtil;
import com.library.vo.LoginVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.Date;

/**
 * 认证服务实现类
 */
@Slf4j
@Service
public class AuthServiceImpl implements AuthService {

    @Resource
    private SysUserMapper sysUserMapper;

    @Resource
    private UserDimensionMapper userDimensionMapper;

    @Resource
    private JwtUtil jwtUtil;

    @Override
    public LoginVO login(LoginDTO loginDTO) {
        String username = loginDTO.getUsername();
        String password = loginDTO.getPassword();

        // 先尝试作为管理员登录
        LambdaQueryWrapper<SysUser> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(SysUser::getUsername, username)
                .or()
                .eq(SysUser::getUserid, username);
        SysUser sysUser = sysUserMapper.selectOne(wrapper);

        LoginVO loginVO = new LoginVO();

        if (sysUser != null) {
            // 管理员登录
            if (!password.equals(sysUser.getPassword())) {
                throw new BusinessException(ResultCode.LOGIN_ERROR);
            }

            if (sysUser.getStatus() == 0) {
                throw new BusinessException("账号已被禁用");
            }

            // 更新最后登录时间
            sysUser.setLastLoginTime(new Date());
            sysUserMapper.updateById(sysUser);

            BeanUtil.copyProperties(sysUser, loginVO);
            String token = jwtUtil.generateToken(sysUser.getUserid(), sysUser.getUserType());
            loginVO.setToken(token);

            log.info("管理员登录成功：userid={}, userType={}", sysUser.getUserid(), sysUser.getUserType());
        } else {
            // 普通用户登录(使用userid作为用户名和密码)
            UserDimension userDimension = userDimensionMapper.selectById(username);
            if (userDimension == null || !username.equals(password)) {
                throw new BusinessException(ResultCode.LOGIN_ERROR);
            }

            loginVO.setUserid(userDimension.getUserid());
            loginVO.setUsername(userDimension.getUserid());
            loginVO.setDept(userDimension.getDeptName());
            loginVO.setUserType(3); // 普通用户

            String token = jwtUtil.generateToken(userDimension.getUserid(), 3);
            loginVO.setToken(token);

            log.info("普通用户登录成功：userid={}", userDimension.getUserid());
        }

        return loginVO;
    }
}
