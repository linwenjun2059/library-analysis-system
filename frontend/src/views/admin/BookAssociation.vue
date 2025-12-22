<template>
  <div class="book-association-container">
    <!-- 统计概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="关联规则总数" :value="stats.totalRules || 0">
            <template #prefix>
              <el-icon color="#409eff"><Connection /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="平均置信度" :value="stats.avgConfidence || 0" :precision="2" suffix="%">
            <template #prefix>
              <el-icon color="#67c23a"><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="平均提升度" :value="stats.avgLift || 0" :precision="2">
            <template #prefix>
              <el-icon color="#e6a23c"><Top /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 关联类型分布 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span>关联类型分布</span>
          </template>
          <div ref="typeChartRef" style="width: 100%; height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span>置信度分布</span>
          </template>
          <div ref="confidenceChartRef" style="width: 100%; height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 关联规则列表 -->
    <el-card shadow="hover" class="rules-card">
      <template #header>
        <div class="card-header">
          <span>图书关联规则</span>
          <div class="filter-area">
            <el-select v-model="filterType" placeholder="关联类型" clearable style="width: 140px; margin-right: 10px;">
              <el-option label="同主题关联" value="同主题关联" />
              <el-option label="跨主题关联" value="跨主题关联" />
            </el-select>
            <el-select v-model="sortBy" placeholder="排序方式" style="width: 120px; margin-right: 10px;">
              <el-option label="置信度" value="confidence" />
              <el-option label="提升度" value="lift" />
              <el-option label="支持度" value="support" />
            </el-select>
            <el-button type="primary" @click="loadRules">查询</el-button>
          </div>
        </div>
      </template>

      <el-table :data="rules" v-loading="loading" stripe>
        <el-table-column label="前项图书" min-width="200">
          <template #default="{ row }">
            <div class="book-title">{{ row.antecedentTitle }}</div>
            <el-tag size="small" type="info">{{ row.antecedentSubject }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="" width="60" align="center">
          <template #default>
            <el-icon color="#409eff" size="20"><Right /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="后项图书" min-width="200">
          <template #default="{ row }">
            <div class="book-title">{{ row.consequentTitle }}</div>
            <el-tag size="small" type="info">{{ row.consequentSubject }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="120" align="center">
          <template #default="{ row }">
            <el-progress 
              :percentage="(row.confidence * 100).toFixed(1)" 
              :stroke-width="10"
              :format="() => (row.confidence * 100).toFixed(1) + '%'"
            />
          </template>
        </el-table-column>
        <el-table-column label="提升度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.lift > 100 ? 'danger' : row.lift > 10 ? 'warning' : 'success'">
              {{ row.lift.toFixed(2) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.associationType === '同主题关联' ? 'success' : 'primary'">
              {{ row.associationType }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-area">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadRules"
          @current-change="loadRules"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Connection, TrendCharts, Top, Right } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getAssociationRules, getAssociationStats } from '@/api/advanced'

const loading = ref(false)
const stats = ref({})
const rules = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterType = ref('')
const sortBy = ref('confidence')

const typeChartRef = ref(null)
const confidenceChartRef = ref(null)
let typeChart = null
let confidenceChart = null

const loadStats = async () => {
  try {
    const res = await getAssociationStats()
    if (res.code === 200) {
      stats.value = res.data
      renderTypeChart()
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadRules = async () => {
  loading.value = true
  try {
    const res = await getAssociationRules({
      current: currentPage.value,
      size: pageSize.value,
      associationType: filterType.value,
      sortBy: sortBy.value
    })
    if (res.code === 200) {
      rules.value = res.data.records
      total.value = res.data.total
      renderConfidenceChart()
    }
  } catch (error) {
    console.error('加载规则失败:', error)
  } finally {
    loading.value = false
  }
}

const renderTypeChart = () => {
  if (!typeChartRef.value) return
  
  if (!typeChart) {
    typeChart = echarts.init(typeChartRef.value)
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      bottom: '0%',
      left: 'center'
    },
    series: [{
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
        formatter: '{b}: {c}条\n({d}%)',
        fontSize: 12
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: true,
        length: 15,
        length2: 10
      },
      data: [
        { value: stats.value.sameSubjectRules || 0, name: '同主题关联', itemStyle: { color: '#67c23a' } },
        { value: stats.value.crossSubjectRules || 0, name: '跨主题关联', itemStyle: { color: '#409eff' } }
      ]
    }]
  }
  
  typeChart.setOption(option)
}

const renderConfidenceChart = () => {
  if (!confidenceChartRef.value || rules.value.length === 0) return
  
  if (!confidenceChart) {
    confidenceChart = echarts.init(confidenceChartRef.value)
  }
  
  // 统计置信度分布
  const ranges = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
  const counts = [0, 0, 0, 0, 0]
  
  rules.value.forEach(rule => {
    const conf = rule.confidence * 100
    if (conf < 20) counts[0]++
    else if (conf < 40) counts[1]++
    else if (conf < 60) counts[2]++
    else if (conf < 80) counts[3]++
    else counts[4]++
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: ranges
    },
    yAxis: {
      type: 'value',
      name: '规则数量'
    },
    series: [{
      type: 'bar',
      data: counts,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#409eff' },
          { offset: 1, color: '#67c23a' }
        ])
      },
      label: {
        show: true,
        position: 'top'
      }
    }]
  }
  
  confidenceChart.setOption(option)
}

onMounted(async () => {
  await loadStats()
  await loadRules()
  
  window.addEventListener('resize', () => {
    typeChart?.resize()
    confidenceChart?.resize()
  })
})
</script>

<style scoped>
.book-association-container {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  margin-bottom: 20px;
}

.chart-row {
  margin-bottom: 20px;
}

.rules-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-area {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.book-title {
  font-weight: 500;
  margin-bottom: 5px;
  color: #303133;
}

.pagination-area {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-area {
    width: 100%;
    margin-top: 10px;
  }
}
</style>
