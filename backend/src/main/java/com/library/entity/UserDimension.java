package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 用户维度表实体
 */
@Data
@TableName("user_dimension")
public class UserDimension implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户ID
     */
    @TableId
    private String userid;

    /**
     * 性别
     */
    private String gender;

    /**
     * 院系名称
     */
    private String deptName;

    /**
     * 用户类型
     */
    private String userTypeName;

    /**
     * 创建时间(数据库中不存在，标记为非数据库字段)
     */
    @TableField(exist = false)
    private Date createTime;
}
