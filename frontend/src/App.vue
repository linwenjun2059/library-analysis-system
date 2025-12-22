<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* 全局统一样式变量 */
:root {
  --kiro-spacing-xs: 8px;
  --kiro-spacing-sm: 12px;
  --kiro-spacing-md: 16px;
  --kiro-spacing-lg: 20px;
  --kiro-spacing-xl: 24px;
  --kiro-border-radius-sm: 8px;
  --kiro-border-radius-md: 12px;
  --kiro-border-radius-lg: 16px;
  --kiro-card-margin-bottom: 20px;
}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

#app {
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  min-height: 100vh;
}

::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-thumb {
  background: #3b82f6;
  border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
  background: #2563eb;
}

::-webkit-scrollbar-track {
  background: #e5e7eb;
  border-radius: 5px;
}

.el-card {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
  transition: all 0.2s ease !important;
}

.el-card:hover {
  border-color: #d1d5db !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
  transform: translateY(-2px) !important;
}

.el-button {
  border-radius: 8px;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
  transition: all 0.2s ease;
}

.el-button--primary {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
}

.el-button--primary:hover {
  background: #2563eb;
  border-color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.el-button--success {
  background: #10b981;
  border-color: #10b981;
  color: #ffffff;
}

.el-button--success:hover {
  background: #059669;
  border-color: #059669;
}

.el-button--warning {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #ffffff;
}

.el-button--warning:hover {
  background: #d97706;
  border-color: #d97706;
}

.el-button--danger {
  background: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}

.el-button--danger:hover {
  background: #dc2626;
  border-color: #dc2626;
}

.el-input__wrapper {
  background: #ffffff !important;
  border: 1px solid #d1d5db !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
  transition: all 0.2s !important;
}

.el-input__wrapper:hover {
  border-color: #9ca3af !important;
}

.el-input__wrapper.is-focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

.el-input__inner {
  color: #1f2937 !important;
  font-family: 'Inter', sans-serif;
}

.el-input__inner::placeholder {
  color: #9ca3af !important;
}

.el-table {
  background: #ffffff !important;
  color: #1f2937 !important;
}

.el-table th.el-table__cell {
  background: #f9fafb !important;
  color: #374151 !important;
  font-weight: 600 !important;
  font-family: 'Inter', sans-serif;
  border-bottom: 2px solid #e5e7eb !important;
}

.el-table tr {
  background: transparent !important;
}

.el-table td.el-table__cell {
  border-bottom: 1px solid #f3f4f6 !important;
}

.el-table__body tr:hover > td {
  background: #f9fafb !important;
}

.el-dialog {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15) !important;
}

.el-dialog__header {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 20px 24px;
}

.el-dialog__title {
  color: #111827 !important;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  font-size: 18px;
}

.el-dialog__body {
  color: #374151 !important;
  padding: 24px;
}

.el-dialog__close {
  color: #6b7280 !important;
  
  &:hover {
    color: #111827 !important;
  }
}

.el-select-dropdown {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.el-select-dropdown__item {
  color: #374151 !important;
  
  &:hover {
    background: #f3f4f6 !important;
  }
  
  &.selected {
    background: #eff6ff !important;
    color: #3b82f6 !important;
    font-weight: 600;
  }
}

.el-dropdown-menu {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.el-dropdown-menu__item {
  color: #374151 !important;
  
  &:hover {
    background: #f3f4f6 !important;
    color: #111827 !important;
  }
}

.el-pagination {
  .el-pager li {
    background: #ffffff !important;
    color: #374151 !important;
    border: 1px solid #e5e7eb;
    transition: all 0.2s;
    
    &:hover {
      background: #f9fafb !important;
      border-color: #d1d5db;
    }
    
    &.active {
      background: #3b82f6 !important;
      color: #ffffff !important;
      border-color: #3b82f6;
    }
  }
  
  button {
    background: #ffffff !important;
    color: #374151 !important;
    border: 1px solid #e5e7eb;
    
    &:hover:not(:disabled) {
      background: #f9fafb !important;
      border-color: #d1d5db;
    }
    
    &:disabled {
      opacity: 0.4;
    }
  }
}

.el-tag {
  background: #f3f4f6 !important;
  border-color: #e5e7eb !important;
  color: #374151 !important;
  
  &.el-tag--primary {
    background: #dbeafe !important;
    border-color: #93c5fd !important;
    color: #1e40af !important;
  }
  
  &.el-tag--success {
    background: #d1fae5 !important;
    border-color: #6ee7b7 !important;
    color: #065f46 !important;
  }
  
  &.el-tag--warning {
    background: #fef3c7 !important;
    border-color: #fcd34d !important;
    color: #92400e !important;
  }
  
  &.el-tag--danger {
    background: #fee2e2 !important;
    border-color: #fca5a5 !important;
    color: #991b1b !important;
  }
}

.el-message {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  
  .el-message__content {
    color: #374151 !important;
  }
}

.el-message--success {
  border-color: #10b981 !important;
}

.el-message--warning {
  border-color: #f59e0b !important;
}

.el-message--error {
  border-color: #ef4444 !important;
}

.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.9) !important;
}

.el-loading-spinner .circular {
  stroke: #3b82f6 !important;
}

.el-date-picker {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
}

.el-picker-panel__content {
  color: #374151 !important;
}

.el-date-table td.available:hover {
  background: #f3f4f6 !important;
  color: #111827 !important;
}

.el-date-table td.current {
  background: #3b82f6 !important;
  color: #ffffff !important;
}
</style>
