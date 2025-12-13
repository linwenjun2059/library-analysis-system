import request from '@/utils/request'

/**
 * 获取用户排名
 */
export function getUserRanking(userid) {
  return request({
    url: `/statistics/user-ranking/${userid}`,
    method: 'get'
  })
}

/**
 * 获取院系借阅汇总
 */
export function getDeptLendSummary() {
  return request({
    url: '/statistics/dept-summary',
    method: 'get'
  })
}

/**
 * 获取院系偏好
 */
export function getDeptPreference(dept) {
  return request({
    url: `/statistics/dept-preference/${dept}`,
    method: 'get'
  })
}

/**
 * 获取主题借阅汇总
 */
export function getSubjectLendSummary() {
  return request({
    url: '/statistics/subject-summary',
    method: 'get'
  })
}

/**
 * 获取每日统计数据
 */
export function getDailyStats(params) {
  return request({
    url: '/statistics/daily-stats',
    method: 'get',
    params
  })
}

/**
 * 获取活跃用户列表
 */
export function getActiveUsers(params) {
  return request({
    url: '/statistics/active-users',
    method: 'get',
    params
  })
}

/**
 * 获取借阅趋势
 */
export function getLendTrend(params) {
  return request({
    url: '/statistics/lend-trend',
    method: 'get',
    params
  })
}

/**
 * 获取时间分布统计
 */
export function getTimeDistribution(params) {
  return request({
    url: '/statistics/time-distribution',
    method: 'get',
    params
  })
}

/**
 * 获取逾期分析
 */
export function getOverdueAnalysis(params) {
  return request({
    url: '/statistics/overdue-analysis',
    method: 'get',
    params
  })
}

/**
 * 获取运营看板数据
 */
export function getOperationDashboard() {
  return request({
    url: '/statistics/operation-dashboard',
    method: 'get'
  })
}

/**
 * 获取馆藏利用分析
 */
export function getCollectionUtilization(params) {
  return request({
    url: '/statistics/collection-utilization',
    method: 'get',
    params
  })
}

/**
 * 获取专业阅读特征
 */
export function getMajorReadingProfile() {
  return request({
    url: '/statistics/major-reading-profile',
    method: 'get'
  })
}

/**
 * 获取推荐统计
 */
export function getRecommendationStats() {
  return request({
    url: '/statistics/recommendation-stats',
    method: 'get'
  })
}

/**
 * 获取院系推荐图书
 */
export function getDeptRecommendBooks(params) {
  return request({
    url: '/statistics/dept-recommend-books',
    method: 'get',
    params
  })
}

/**
 * 获取借阅日历数据
 */
export function getBorrowCalendar(userid, params) {
  return request({
    url: `/statistics/borrow-calendar/${userid}`,
    method: 'get',
    params
  })
}

/**
 * 获取图书推荐基础数据
 */
export function getBookRecommendBase(params) {
  return request({
    url: '/statistics/book-recommend-base',
    method: 'get',
    params
  })
}

/**
 * 获取用户画像数据（全部）
 */
export function getUserProfile(params) {
  return request({
    url: '/statistics/user-profile',
    method: 'get',
    params
  })
}

/**
 * 获取指定用户的画像数据
 */
export function getUserProfileByUserid(userid) {
  return request({
    url: `/statistics/user-profile/${userid}`,
    method: 'get'
  })
}

/**
 * 获取出版社分析
 */
export function getPublisherAnalysis() {
  return request({
    url: '/statistics/publisher-analysis',
    method: 'get'
  })
}

/**
 * 获取出版年份分析
 */
export function getPublishYearAnalysis() {
  return request({
    url: '/statistics/publish-year-analysis',
    method: 'get'
  })
}

/**
 * 获取借阅时间分布
 */
export function getLendTimeDistribution() {
  return request({
    url: '/statistics/lend-time-distribution',
    method: 'get'
  })
}

/**
 * 获取续借行为分析
 */
export function getRenewAnalysis() {
  return request({
    url: '/statistics/renew-analysis',
    method: 'get'
  })
}