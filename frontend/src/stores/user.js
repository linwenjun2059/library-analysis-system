import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))

  // 设置Token
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  // 设置用户信息
  const setUserInfo = (info) => {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  // 登出
  const logout = () => {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  // 判断是否登录
  const isLogin = () => {
    return !!token.value
  }

  // 获取用户类型
  const getUserType = () => {
    return userInfo.value.userType || 3
  }

  // 获取用户ID
  const getUserId = () => {
    return userInfo.value.userid || ''
  }

  return {
    token,
    userInfo,
    setToken,
    setUserInfo,
    logout,
    isLogin,
    getUserType,
    getUserId
  }
})
