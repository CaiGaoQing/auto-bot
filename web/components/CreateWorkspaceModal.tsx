'use client'

import { useState } from 'react'
import { X, FolderPlus, Loader2, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CreateWorkspaceModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (workspace: any) => void
}

const ROLES = [
  { id: 'assistant', name: '通用助手', desc: '智能对话与任务处理' },
  { id: 'developer', name: '开发助手', desc: '代码编写与技术支持' },
  { id: 'finance', name: '财务助手', desc: '财务分析与报表生成' },
  { id: 'product', name: '产品助手', desc: '需求文档与产品规划' },
  { id: 'project_manager', name: '项目管理', desc: '项目计划与任务拆分' },
  { id: 'operator', name: '运营助手', desc: '内容创作与社媒管理' },
  { id: 'tester', name: '测试助手', desc: '测试用例与自动化测试' },
  { id: 'researcher', name: '调研助手', desc: '市场调研与竞品分析' },
]

export function CreateWorkspaceModal({ isOpen, onClose, onCreated }: CreateWorkspaceModalProps) {
  const [name, setName] = useState('')
  const [selectedRoles, setSelectedRoles] = useState<string[]>(['assistant'])  // 多角色选择
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  if (!isOpen) return null

  // 切换角色选择
  const toggleRole = (roleId: string) => {
    setSelectedRoles(prev => {
      if (prev.includes(roleId)) {
        // 至少保留一个角色
        if (prev.length === 1) return prev
        return prev.filter(r => r !== roleId)
      } else {
        return [...prev, roleId]
      }
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name.trim()) {
      setError('请输入工作空间名称')
      return
    }
    
    if (selectedRoles.length === 0) {
      setError('请至少选择一个角色')
      return
    }
    
    setIsLoading(true)
    setError('')
    
    try {
      const res = await fetch('/api/v1/workspaces', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          roles: selectedRoles,  // 发送角色数组
          description: description.trim() || undefined,
        }),
      })
      
      const data = await res.json()
      
      if (data.code === 0 && data.data) {
        onCreated(data.data)
        onClose()
        setName('')
        setSelectedRoles(['assistant'])
        setDescription('')
      } else {
        setError(data.message || '创建失败')
      }
    } catch (err) {
      setError('网络错误，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 背景遮罩 */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* 对话框 */}
      <div className="relative w-full max-w-lg mx-4 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              <FolderPlus className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                新建工作空间
              </h2>
              <p className="text-sm text-slate-500">创建一个新的工作目录</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>
        
        {/* 表单 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* 名称 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              工作空间名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：2024年度财报分析"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          
          {/* 角色选择 - 多选 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              选择角色 <span className="text-slate-400 font-normal">（可多选）</span>
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {ROLES.map((r) => {
                const isSelected = selectedRoles.includes(r.id)
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => toggleRole(r.id)}
                    className={cn(
                      'p-3 rounded-xl border text-left transition-all cursor-pointer relative',
                      isSelected
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                    )}
                  >
                    {isSelected && (
                      <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    )}
                    <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {r.name}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">{r.desc}</div>
                  </button>
                )
              })}
            </div>
            {selectedRoles.length > 0 && (
              <p className="text-xs text-blue-600 mt-2">
                已选择 {selectedRoles.length} 个角色
              </p>
            )}
          </div>
          
          {/* 描述 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              描述（可选）
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="简要描述这个工作空间的用途..."
              rows={3}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
            />
          </div>
          
          {/* 错误提示 */}
          {error && (
            <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">
              {error}
            </div>
          )}
          
          {/* 按钮 */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-3 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-colors cursor-pointer font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  创建中...
                </>
              ) : (
                '创建工作空间'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
