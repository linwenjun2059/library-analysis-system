package com.library.vo;

import lombok.Data;

import java.io.Serializable;

/**
 * 登录响应VO
 */
@Data
public class LoginVO implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户ID
     */
    private String userid;

    /**
     * 用户名
     */
    private String username;

    /**
     * 真实姓名
     */
    private String realName;

    /**
     * 用户类型(1-系统管理员, 2-图书馆管理员, 3-普通用户)
     */
    private Integer userType;

    /**
     * 院系
     */
    private String dept;

    /**
     * 专业
     */
    private String occupation;

    /**
     * Token
     */
    private String token;
}
