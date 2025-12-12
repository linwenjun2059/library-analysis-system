import request from '@/utils/request'

// ==================== 关联规则分析 ====================

/**
 * 获取图书关联规则列表（分页）
 */
export function getAssociationRules(params) {
  return request({
    url: '/analysis/advanced/association/rules',
    method: 'get',
    params
  })
}

/**
 * 获取指定图书的关联推荐
 */
export function getBookAssociations(bookTitle, limit = 10) {
  return request({
    url: `/analysis/advanced/association/book/${encodeURIComponent(bookTitle)}`,
    method: 'get',
    params: { limit }
  })
}

/**
 * 获取关联规则统计概览
 */
export function getAssociationStats() {
  return request({
    url: '/analysis/advanced/association/stats',
    method: 'get'
  })
}

// ==================== 用户聚类分群 ====================

/**
 * 获取聚类统计摘要
 */
export function getClusterSummary() {
  return request({
    url: '/analysis/advanced/cluster/summary',
    method: 'get'
  })
}

/**
 * 获取指定聚类的用户列表（分页）
 */
export function getClusterUsers(clusterId, params) {
  return request({
    url: `/analysis/advanced/cluster/${clusterId}/users`,
    method: 'get',
    params
  })
}

/**
 * 获取用户所属聚类信息
 */
export function getUserCluster(userid) {
  return request({
    url: `/analysis/advanced/cluster/user/${userid}`,
    method: 'get'
  })
}

/**
 * 获取各院系的聚类分布
 */
export function getDeptClusterDistribution(dept) {
  return request({
    url: '/analysis/advanced/cluster/dept-distribution',
    method: 'get',
    params: { dept }
  })
}

/**
 * 获取聚类整体统计
 */
export function getClusterStats() {
  return request({
    url: '/analysis/advanced/cluster/stats',
    method: 'get'
  })
}

// ==================== 预测分析 ====================

/**
 * 获取逾期风险预测列表
 */
export function getOverdueRiskList(params) {
  return request({
    url: '/analysis/prediction/overdue/list',
    method: 'get',
    params
  })
}

/**
 * 获取逾期风险统计
 */
export function getOverdueRiskStats() {
  return request({
    url: '/analysis/prediction/overdue/stats',
    method: 'get'
  })
}

/**
 * 获取用户逾期风险
 */
export function getUserOverdueRisk(userid) {
  return request({
    url: `/analysis/prediction/overdue/user/${userid}`,
    method: 'get'
  })
}

/**
 * 获取借阅趋势预测
 */
export function getLendTrendPrediction(dataType) {
  return request({
    url: '/analysis/prediction/trend/list',
    method: 'get',
    params: { dataType }
  })
}

/**
 * 获取借阅趋势统计
 */
export function getLendTrendStats() {
  return request({
    url: '/analysis/prediction/trend/stats',
    method: 'get'
  })
}

/**
 * 获取图书热度预测列表
 */
export function getBookHeatList(params) {
  return request({
    url: '/analysis/prediction/heat/list',
    method: 'get',
    params
  })
}

/**
 * 获取图书热度统计
 */
export function getBookHeatStats() {
  return request({
    url: '/analysis/prediction/heat/stats',
    method: 'get'
  })
}

/**
 * 获取热门图书TOP
 */
export function getTopHotBooks(limit = 20) {
  return request({
    url: '/analysis/prediction/heat/top',
    method: 'get',
    params: { limit }
  })
}

/**
 * 获取采购建议
 */
export function getPurchaseSuggestions() {
  return request({
    url: '/analysis/prediction/heat/purchase-suggestions',
    method: 'get'
  })
}
