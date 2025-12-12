import request from '@/utils/request'

/**
 * 获取热门图书
 */
export function getHotBooks(params) {
  return request({
    url: '/book/hot',
    method: 'get',
    params
  })
}

/**
 * 搜索图书
 */
export function searchBooks(params) {
  return request({
    url: '/book/search',
    method: 'get',
    params
  })
}

/**
 * 获取图书详情
 */
export function getBookDetail(bookId) {
  return request({
    url: `/book/detail/${bookId}`,
    method: 'get'
  })
}

/**
 * 获取图书借阅汇总
 */
export function getBookLendSummary(bookId) {
  return request({
    url: `/book/summary/${bookId}`,
    method: 'get'
  })
}

/**
 * 获取图书排行榜（多维度）
 */
export function getBookRanking(params) {
  return request({
    url: '/book/ranking',
    method: 'get',
    params
  })
}

/**
 * 获取图书健康度分析
 */
export function getBookHealthAnalysis(bookId) {
  return request({
    url: `/book/health-analysis/${bookId}`,
    method: 'get'
  })
}