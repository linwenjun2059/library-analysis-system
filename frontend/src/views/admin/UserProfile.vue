<template>
  <div class="user-profile-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><UserFilled /></el-icon> 用户画像分析</span>
          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Tab 1: 用户标签云 -->
        <el-tab-pane label="用户标签" name="tags">
          <el-empty v-if="userProfiles.length === 0" description="暂无用户画像数据" />
        <div v-else>
          <div ref="tagsChartRef" style="width: 100%; height: 480px; margin-bottom: 20px;"></div>
          <el-divider>标签词云</el-divider>
          <div ref="wordCloudChartRef" style="width: 100%; height: 420px; min-height: 320px;"></div>
        </div>
        </el-tab-pane>
        
        <!-- Tab 2: 借阅等级分布 -->
        <el-tab-pane label="借阅等级" name="level">
          <el-empty v-if="userProfiles.length === 0" description="暂无用户画像数据" />
          <div v-else>
            <el-row :gutter="20" style="margin-bottom: 20px;">
              <el-col :span="8" v-for="level in borrowLevelStats" :key="level.name">
                <el-card shadow="hover">
                  <el-statistic :title="level.name" :value="level.count">
                    <template #suffix>人</template>
                  </el-statistic>
                  <div style="margin-top: 10px; color: #909399;">占比: {{ level.percentage }}%</div>
                </el-card>
              </el-col>
            </el-row>
            <div ref="levelChartRef" style="width: 100%; height: 400px;"></div>
          </div>
        </el-tab-pane>
        
        <!-- Tab 3: 性别年龄分布 -->
        <el-tab-pane label="性别年龄" name="demographics">
          <el-empty v-if="userProfiles.length === 0" description="暂无用户画像数据" />
          <el-row v-else :gutter="20">
            <el-col :span="12">
              <el-card shadow="hover">
                <template #header>性别分布</template>
                <div ref="genderChartRef" style="width: 100%; height: 350px;"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="hover">
                <template #header>年龄段分布</template>
                <div ref="ageChartRef" style="width: 100%; height: 350px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <!-- Tab 4: 偏好主题分析 -->
        <el-tab-pane label="偏好主题" name="subjects">
          <el-empty v-if="userProfiles.length === 0" description="暂无用户画像数据" />
          <div v-else ref="subjectsChartRef" style="width: 100%; height: 500px;"></div>
        </el-tab-pane>
        
        <!-- Tab 5: 用户详情列表 -->
        <el-tab-pane label="用户列表" name="list">
          <el-table :data="pagedUserProfiles" v-loading="loading" stripe style="width: 100%">
            <el-table-column prop="userid" label="用户ID" width="120" />
            <el-table-column prop="userType" label="类型" width="80" />
            <el-table-column prop="dept" label="院系" width="180" show-overflow-tooltip />
            <el-table-column prop="occupation" label="专业" width="150" show-overflow-tooltip />
            <el-table-column prop="borrowLevel" label="等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getLevelTagType(row.borrowLevel)">{{ row.borrowLevel }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="totalBorrowCount" label="借阅量" width="100" align="center" sortable />
            <el-table-column prop="readingBreadth" label="广度" width="80" align="center" sortable />
            <el-table-column prop="overdueRate" label="逾期率" width="100" align="center" sortable>
              <template #default="{ row }">
                <span :style="{ color: getOverdueRateColor(row.overdueRate) }">
                  {{ (row.overdueRate * 100).toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="userTags" label="标签" min-width="200">
              <template #default="{ row }">
                <el-tag v-for="(tag, idx) in parseJsonArray(row.userTags)" :key="idx" size="small" style="margin-right: 5px;">
                  {{ tag }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="userProfiles.length"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getUserProfile } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

const loading = ref(false)
const activeTab = ref('tags')

const tagsChartRef = ref(null)
const wordCloudChartRef = ref(null)
const levelChartRef = ref(null)
const genderChartRef = ref(null)
const ageChartRef = ref(null)
const subjectsChartRef = ref(null)

const userProfiles = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

let tagsChart = null
let wordCloudChart = null
let levelChart = null
let genderChart = null
let ageChart = null
let subjectsChart = null

// 分页后的用户数据
const pagedUserProfiles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return userProfiles.value.slice(start, end)
})

// 借阅等级统计
const borrowLevelStats = computed(() => {
  const stats = {}
  userProfiles.value.forEach(user => {
    const level = user.borrowLevel || '未知'
    stats[level] = (stats[level] || 0) + 1
  })
  
  const total = userProfiles.value.length
  return Object.entries(stats).map(([name, count]) => ({
    name,
    count,
    percentage: ((count / total) * 100).toFixed(1)
  })).sort((a, b) => b.count - a.count)
})

// 解析JSON数组字符串
const parseJsonArray = (jsonStr) => {
  if (!jsonStr) return []
  try {
    return JSON.parse(jsonStr)
  } catch (e) {
    return []
  }
}

// 获取等级标签类型
const getLevelTagType = (level) => {
  const map = {
    '超级读者': 'danger',
    '高级读者': 'warning',
    '中级读者': 'success',
    '初级读者': 'info',
    '不活跃': ''
  }
  return map[level] || 'info'
}

// 获取逾期率颜色
const getOverdueRateColor = (rate) => {
  if (rate > 0.3) return '#f56c6c'
  if (rate > 0.1) return '#e6a23c'
  return '#67c23a'
}

// 初始化标签词云图
const initTagsChart = () => {
  if (!tagsChartRef.value || userProfiles.value.length === 0) return
  
  if (!tagsChart) {
    tagsChart = echarts.init(tagsChartRef.value)
  }
  
  // 统计所有user_tags标签
  const tagCounts = {}
  userProfiles.value.forEach(user => {
    const tags = parseJsonArray(user.userTags)
    tags.forEach(tag => {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1
    })
  })
  
  const tagData = Object.entries(tagCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
  
  const option = {
    title: { text: '用户标签分布TOP50' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '1%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      splitNumber: 20  // 提高刻度密度
    },
    yAxis: {
      type: 'category',
      data: tagData.slice(0, 20).map(item => item.name).reverse()
    },
    series: [{
      name: '用户数',
      type: 'bar',
      data: tagData.slice(0, 20).map(item => item.value).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#5470c6' },
          { offset: 1, color: '#91cc75' }
        ])
      },
      label: {
        show: true,
        position: 'right'
      }
    }]
  }
  
  tagsChart.setOption(option)
}

// 初始化用户标签词云（前端聚合，不改 Spark）
const initWordCloudChart = () => {
  if (!wordCloudChartRef.value || userProfiles.value.length === 0) return

  if (!wordCloudChart) {
    wordCloudChart = echarts.init(wordCloudChartRef.value)
  }

  const tagCounts = {}
  userProfiles.value.forEach(user => {
    parseJsonArray(user.userTags).forEach(tag => {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1
    })
  })

  const data = Object.entries(tagCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 200) // 取前200个标签，词云更丰富
  if (data.length === 0) return

  const option = {
    tooltip: { show: true },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      gridSize: 6,
      sizeRange: [14, 46],
      rotationRange: [-45, 45],
      textStyle: {
        color: () => {
          const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      data
    }]
  }

  wordCloudChart.setOption(option)
}

// 初始化借阅等级图
const initLevelChart = () => {
  if (!levelChartRef.value || borrowLevelStats.value.length === 0) return
  
  if (!levelChart) {
    levelChart = echarts.init(levelChartRef.value)
  }
  
  const option = {
    title: { text: '借阅等级分布' },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    series: [{
      name: '用户数',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {c}人'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 18,
          fontWeight: 'bold'
        }
      },
      data: borrowLevelStats.value.map(item => ({
        value: item.count,
        name: item.name
      }))
    }]
  }
  
  levelChart.setOption(option)
}

// 初始化性别分布图
const initGenderChart = () => {
  if (!genderChartRef.value || userProfiles.value.length === 0) return
  
  if (!genderChart) {
    genderChart = echarts.init(genderChartRef.value)
  }
  
  // 统计性别
  const genderStats = {}
  userProfiles.value.forEach(user => {
    const gender = user.gender || '未知'
    genderStats[gender] = (genderStats[gender] || 0) + 1
  })
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    series: [{
      name: '性别分布',
      type: 'pie',
      radius: '70%',
      data: Object.entries(genderStats).map(([name, value]) => ({ name, value })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  genderChart.setOption(option)
}

// 初始化年龄分布图
const initAgeChart = () => {
  if (!ageChartRef.value || userProfiles.value.length === 0) return
  
  if (!ageChart) {
    ageChart = echarts.init(ageChartRef.value)
  }
  
  // 统计年龄段
  const ageStats = {}
  userProfiles.value.forEach(user => {
    const age = user.ageGroup || '未知'
    ageStats[age] = (ageStats[age] || 0) + 1
  })
  
  const ageData = Object.entries(ageStats)
    .sort((a, b) => a[0].localeCompare(b[0]))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: ageData.map(item => item[0])
    },
    yAxis: {
      type: 'value',
      name: '用户数'
    },
    series: [{
      name: '用户数',
      type: 'bar',
      data: ageData.map(item => item[1]),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 1, color: '#188df0' }
        ])
      },
      label: {
        show: true,
        position: 'top'
      }
    }]
  }
  
  ageChart.setOption(option)
}

// 初始化偏好主题图
const initSubjectsChart = () => {
  if (!subjectsChartRef.value || userProfiles.value.length === 0) return
  
  if (!subjectsChart) {
    subjectsChart = echarts.init(subjectsChartRef.value)
  }
  
  // 统计所有偏好主题
  const subjectCounts = {}
  userProfiles.value.forEach(user => {
    const subjects = parseJsonArray(user.favoriteSubjects)
    subjects.forEach(subject => {
      subjectCounts[subject] = (subjectCounts[subject] || 0) + 1
    })
  })
  
  const subjectData = Object.entries(subjectCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 30)
  
  const option = {
    title: { text: '用户偏好主题TOP30' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '1%',
      right: '10%',
      bottom: '6%',
      top: '6%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: subjectData.map(item => item.name).reverse(),
      axisLabel: {
        interval: 0,
        width: 180,
        overflow: 'truncate'  // 超长截断，避免遮挡
      }
    },
    series: [{
      name: '偏好人数',
      type: 'bar',
      label: {
        show: true,
        position: 'right'
      },
      data: subjectData.map(item => item.value).reverse(),
      itemStyle: {
        color: (params) => {
          const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }
  
  subjectsChart.setOption(option)
}

const handleTabChange = (tabName) => {
  nextTick(() => {
    setTimeout(() => {
      if (tabName === 'tags') initTagsChart()
      else if (tabName === 'level') initLevelChart()
      else if (tabName === 'demographics') {
        initGenderChart()
        initAgeChart()
      }
      else if (tabName === 'subjects') initSubjectsChart()
      if (tabName === 'tags') initWordCloudChart()
    }, 200)
  })
}

const loadData = async () => {
  try {
    loading.value = true
    console.log('🔄 加载用户画像数据...')
    
    const res = await getUserProfile()
    userProfiles.value = res.data || []
    
    console.log('📥 收到数据:', userProfiles.value.length, '条')
    
    if (userProfiles.value.length === 0) {
      console.warn('⚠️ 暂无用户画像数据')
      ElMessage.warning('暂无用户画像数据')
      return
    }
    
    console.log('📊 数据示例:', userProfiles.value.slice(0, 2))
    
    // 初始化当前tab的图表
    await nextTick()
    setTimeout(() => {
      if (activeTab.value === 'tags') {
        initTagsChart()
        initWordCloudChart()
      }
      else if (activeTab.value === 'level') initLevelChart()
      else if (activeTab.value === 'demographics') {
        initGenderChart()
        initAgeChart()
      }
      else if (activeTab.value === 'subjects') initSubjectsChart()
    }, 300)
    
    console.log('✅ 用户画像数据加载成功')
  } catch (error) {
    console.error('❌ 加载用户画像数据失败：', error)
    ElMessage.error('加载用户画像数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    tagsChart?.resize()
    wordCloudChart?.resize()
    levelChart?.resize()
    genderChart?.resize()
    ageChart?.resize()
    subjectsChart?.resize()
  })
})

onUnmounted(() => {
  tagsChart?.dispose()
  wordCloudChart?.dispose()
  levelChart?.dispose()
  genderChart?.dispose()
  ageChart?.dispose()
  subjectsChart?.dispose()
})
</script>

<style scoped lang="scss">
.user-profile-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 600;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}
</style>
