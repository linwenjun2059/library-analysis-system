import request from '@/utils/request'

/**
 * 获取用户画像
 */
export function getUserProfile(userid) {
  return request({
    url: `/user/profile/${userid}`,
    method: 'get'
  })
}

/**
 * 获取用户借阅汇总
 */
export function getUserLendSummary(userid) {
  return request({
    url: `/user/summary/${userid}`,
    method: 'get'
  })
}

/**
 * 获取用户借阅记录
 */
export function getUserLendRecords(userid, params) {
  return request({
    url: `/user/records/${userid}`,
    method: 'get',
    params
  })
}

/**
 * 获取用户推荐图书
 */
export function getUserRecommendations(userid, params) {
  return request({
    url: `/user/recommendations/${userid}`,
    method: 'get',
    params
  })
}

/**
 * 获取用户维度信息
 */
export function getUserDimension(userid) {
  return request({
    url: `/user/dimension/${userid}`,
    method: 'get'
  })
}

/**
 * 管理员查询所有借阅记录
 */
export function getAllLendRecords(params) {
  return request({
    url: '/user/all-records',
    method: 'get',
    params
  })
}
