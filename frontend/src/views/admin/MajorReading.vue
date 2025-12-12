<template>
  <div class="major-reading-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Reading /></el-icon> 专业阅读特征分析</span>
        </div>
      </template>
      <!-- 分析图表 -->
      <el-card shadow="hover" style="margin-bottom: 16px;">
      <template #header>
        <div class="card-header">
          <span><el-icon><DataAnalysis /></el-icon> 可视化分析</span>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="chart-title">院系总借阅量 Top10</div>
          <div ref="deptBorrowChartRef" class="chart-box"></div>
        </el-col>
        <el-col :span="12">
          <div class="chart-title">专业人均借阅 Top10</div>
          <div ref="avgBorrowChartRef" class="chart-box"></div>
        </el-col>
      </el-row>
      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="24">
          <div class="chart-title">阅读广度得分分布</div>
          <div ref="breadthDistChartRef" class="chart-box" style="height: 320px;"></div>
        </el-col>
      </el-row>
    </el-card>

      <el-table :data="pagedProfiles" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="dept" label="院系" min-width="150" />
        <el-table-column prop="occupation" label="专业" min-width="150">
          <template #default="{ row }">
            {{ row.occupation || '未填写' }}
          </template>
        </el-table-column>
        <el-table-column prop="studentCount" label="学生数量" min-width="120" align="center" sortable />
        <el-table-column prop="totalBorrowCount" label="总借阅量" min-width="120" align="center" sortable />
        <el-table-column prop="avgBorrowPerStudent" label="人均借阅" min-width="120" align="center" sortable>
          <template #default="{ row }">
            {{ row.avgBorrowPerStudent ? row.avgBorrowPerStudent.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="readingBreadthScore" label="阅读广度得分" min-width="180" align="center" sortable>
          <template #default="{ row }">
            <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
              <el-rate
                :model-value="normalizeStar(row.readingBreadthScore)"
                disabled
                allow-half
                show-score
                score-template="{value} 星"
              />
              <small style="color:#909399;">原始得分 {{ (row.readingBreadthScore || 0).toFixed(2) }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 详情对话框 -->
      <el-dialog v-model="dialogVisible" title="专业阅读详情" width="70%">
        <div v-if="currentProfile">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="院系">{{ currentProfile.dept }}</el-descriptions-item>
            <el-descriptions-item label="专业">{{ currentProfile.occupation || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="学生数量">{{ currentProfile.studentCount }}</el-descriptions-item>
            <el-descriptions-item label="总借阅量">{{ currentProfile.totalBorrowCount }}</el-descriptions-item>
            <el-descriptions-item label="人均借阅">{{ currentProfile.avgBorrowPerStudent?.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="阅读广度得分">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-rate
                  :model-value="normalizeStar(currentProfile.readingBreadthScore)"
                  disabled
                  allow-half
                  show-score
                  score-template="{value} 星"
                />
                <span style="color:#909399;">原始 {{ currentProfile.readingBreadthScore?.toFixed(2) || '0.00' }}</span>
              </div>
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider>核心学科 TOP 5</el-divider>
          <el-tag v-for="(subject, index) in getCoreSubjects(currentProfile)" :key="index" style="margin-right: 10px;" type="success">
            {{ subject }}
          </el-tag>
          
          <el-divider>跨学科借阅 TOP 3</el-divider>
          <el-tag v-for="(subject, index) in getCrossSubjects(currentProfile)" :key="index" style="margin-right: 10px;" type="warning">
            {{ subject }}
          </el-tag>
          
          <el-divider>热门书目 TOP 10</el-divider>
          <el-tag v-for="(book, index) in getPopularBooks(currentProfile)" :key="index" style="margin-right: 10px; margin-bottom: 10px;" type="info">
            {{ book }}
          </el-tag>
        </div>
      </el-dialog>
    </el-card>
    <div style="margin-top: 16px; text-align: right;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="profiles.length"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, onBeforeUnmount } from 'vue'
import { getMajorReadingProfile } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const profiles = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const currentProfile = ref(null)

const deptBorrowChartRef = ref(null)
const avgBorrowChartRef = ref(null)
const breadthDistChartRef = ref(null)
let deptBorrowChart, avgBorrowChart, breadthDistChart

const pagedProfiles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return profiles.value.slice(start, end)
})

const normalizeStar = (score) => {
  const val = (score || 0) * 5 // 0-1 映射到 0-5 星
  return Math.min(5, Math.max(0, parseFloat(val.toFixed(2))))
}

const getProgressColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 40) return '#e6a23c'
  return '#f56c6c'
}

const getCoreSubjects = (profile) => {
  try {
    return profile.coreSubjects ? JSON.parse(profile.coreSubjects) : []
  } catch {
    return []
  }
}

const getCrossSubjects = (profile) => {
  try {
    return profile.crossSubjects ? JSON.parse(profile.crossSubjects) : []
  } catch {
    return []
  }
}

const getPopularBooks = (profile) => {
  try {
    return profile.popularBooks ? JSON.parse(profile.popularBooks) : []
  } catch {
    return []
  }
}

const showDetail = (profile) => {
  currentProfile.value = profile
  dialogVisible.value = true
}

const renderDeptBorrowChart = () => {
  if (!deptBorrowChartRef.value) return
  if (!deptBorrowChart) {
    deptBorrowChart = echarts.init(deptBorrowChartRef.value)
  }
  const top10 = [...profiles.value]
    .sort((a, b) => (b.totalBorrowCount || 0) - (a.totalBorrowCount || 0))
    .slice(0, 10)
  deptBorrowChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '15%', right: '6%', bottom: '8%', top: '12%' },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: top10.map((item) => item.dept || '未知'),
      axisLabel: { width: 220, overflow: 'break' }
    },
    series: [
      {
        type: 'bar',
        data: top10.map((item) => item.totalBorrowCount || 0),
        label: { show: true, position: 'right' },
        itemStyle: { color: '#5b8ff9' }
      }
    ]
  })
}

const renderAvgBorrowChart = () => {
  if (!avgBorrowChartRef.value) return
  if (!avgBorrowChart) {
    avgBorrowChart = echarts.init(avgBorrowChartRef.value)
  }
  const top10 = [...profiles.value]
    .filter((item) => item.avgBorrowPerStudent !== null && item.avgBorrowPerStudent !== undefined)
    .sort((a, b) => (b.avgBorrowPerStudent || 0) - (a.avgBorrowPerStudent || 0))
    .slice(0, 10)
  avgBorrowChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '30%', right: '6%', bottom: '8%', top: '12%' },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: top10.map((item) => item.occupation || '未填写'),
      axisLabel: { width: 220, overflow: 'break' }
    },
    series: [
      {
        type: 'bar',
        data: top10.map((item) => Number((item.avgBorrowPerStudent || 0).toFixed(2))),
        label: { show: true, position: 'right' },
        itemStyle: { color: '#5ad8a6' }
      }
    ]
  })
}

const renderBreadthDistChart = () => {
  if (!breadthDistChartRef.value) return
  if (!breadthDistChart) {
    breadthDistChart = echarts.init(breadthDistChartRef.value)
  }
  const buckets = [
    { label: '0~0.2', min: 0, max: 0.2, count: 0 },
    { label: '0.2~0.4', min: 0.2, max: 0.4, count: 0 },
    { label: '0.4~0.6', min: 0.4, max: 0.6, count: 0 },
    { label: '0.6~0.8', min: 0.6, max: 0.8, count: 0 },
    { label: '0.8~1.0', min: 0.8, max: 1.0, count: 0 }
  ]
  profiles.value.forEach((item) => {
    const score = item.readingBreadthScore || 0
    const bucket = buckets.find((b) => score >= b.min && score < b.max || (b.max === 1.0 && score <= 1.0 && score >= b.min))
    if (bucket) bucket.count += 1
  })
  breadthDistChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '5%', right: '4%', bottom: '10%', top: '12%' },
    xAxis: {
      type: 'category',
      data: buckets.map((b) => b.label),
      axisLabel: { interval: 0 }
    },
    yAxis: { type: 'value', name: '专业数量', minInterval: 1 },
    series: [
      {
        type: 'bar',
        data: buckets.map((b) => b.count),
        label: { show: true, position: 'top' },
        itemStyle: { color: '#f6bd16' }
      }
    ]
  })
}

const renderCharts = () => {
  nextTick(() => {
    renderDeptBorrowChart()
    renderAvgBorrowChart()
    renderBreadthDistChart()
  })
}

const handleResize = () => {
  deptBorrowChart?.resize()
  avgBorrowChart?.resize()
  breadthDistChart?.resize()
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getMajorReadingProfile()
    profiles.value = res.data
    renderCharts()
  } catch (error) {
    console.error('加载专业阅读特征失败：', error)
    ElMessage.error('加载专业阅读特征失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  deptBorrowChart?.dispose()
  avgBorrowChart?.dispose()
  breadthDistChart?.dispose()
})
</script>

<style scoped lang="scss">
.major-reading-container {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
}

.chart-box {
  width: 100%;
  height: 280px;
}

.chart-title {
  margin-bottom: 8px;
  font-weight: 600;
  color: #303133;
}
</style>
