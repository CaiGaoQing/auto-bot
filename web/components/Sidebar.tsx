'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { 
  MessageSquare, 
  FolderOpen, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  Plus,
  User,
  Sparkles,
  Trash2,
  Code,
  DollarSign,
  ClipboardList,
  BarChart3,
  Megaphone,
  Search,
  FlaskConical,
  Bot,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useStore } from '@/lib/store'
import { CreateWorkspaceModal } from './CreateWorkspaceModal'
import { RoleListSkeleton } from './Skeleton'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

// Role icons using Lucide
const ROLE_ICONS: Record<string, React.ReactNode> = {
  developer: <Code className="w-5 h-5" />,
  finance: <DollarSign className="w-5 h-5" />,
  product: <ClipboardList className="w-5 h-5" />,
  project_manager: <BarChart3 className="w-5 h-5" />,
  operator: <Megaphone className="w-5 h-5" />,
  tester: <Search className="w-5 h-5" />,
  researcher: <FlaskConical className="w-5 h-5" />,
  assistant: <Bot className="w-5 h-5" />,
}

export function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const router = useRouter()
  const { 
    roles, 
    setRoles, 
    currentRole, 
    setCurrentRole,
    workspaces,
    setWorkspaces,
    currentWorkspace,
    setCurrentWorkspace,
    conversations,
    currentConversationId,
    createConversation,
    deleteConversation,
    setCurrentConversation,
  } = useStore()
  
  const [activeTab, setActiveTab] = useState<'chat' | 'roles' | 'workspaces'>('chat')
  const [hoveredConversation, setHoveredConversation] = useState<string | null>(null)
  const [showCreateWorkspace, setShowCreateWorkspace] = useState(false)

  useEffect(() => {
    // 加载角色列表
    fetch('/api/v1/roles')
      .then(res => res.json())
      .then(data => {
        if (data.data?.items) {
          setRoles(data.data.items)
        }
      })
      .catch(console.error)
    
    // 加载工作空间
    fetch('/api/v1/workspaces')
      .then(res => res.json())
      .then(data => {
        if (data.data?.items) {
          setWorkspaces(data.data.items)
        }
      })
      .catch(console.error)
  }, [setRoles, setWorkspaces])

  const handleRoleSelect = async (roleId: string) => {
    try {
      const res = await fetch(`/api/v1/roles/${roleId}/activate`, {
        method: 'POST',
      })
      const data = await res.json()
      if (data.data) {
        setCurrentRole({
          id: roleId,
          display_name: data.data.display_name,
          icon: roleId,
        })
        // 创建新对话
        createConversation(roleId, currentWorkspace?.id)
      }
    } catch (error) {
      console.error('切换角色失败:', error)
    }
  }

  const handleNewConversation = () => {
    createConversation(currentRole?.id, currentWorkspace?.id)
  }

  const handleDeleteConversation = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    deleteConversation(id)
  }

  // 格式化时间
  const formatTime = (date: Date) => {
    const d = new Date(date)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) {
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (days === 1) {
      return '昨天'
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    }
  }

  return (
    <aside
      className={cn(
        'flex flex-col bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-r border-slate-200/50 dark:border-slate-700/50 transition-all duration-300 ease-out',
        isOpen ? 'w-72' : 'w-16'
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200/50 dark:border-slate-700/50">
        {isOpen && (
          <div className="flex items-center gap-3 animate-fade-in">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-semibold text-lg text-gradient">
              AI Auto
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200 cursor-pointer hover:scale-105 active:scale-95"
          aria-label={isOpen ? '收起侧边栏' : '展开侧边栏'}
        >
          {isOpen ? (
            <ChevronLeft className="w-5 h-5 text-slate-500 transition-transform duration-200" />
          ) : (
            <ChevronRight className="w-5 h-5 text-slate-500 transition-transform duration-200" />
          )}
        </button>
      </div>

      {/* 导航标签 */}
      <div className="flex border-b border-slate-200/50 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-800/30">
        <button
          onClick={() => setActiveTab('chat')}
          className={cn(
            'flex-1 p-3 flex justify-center items-center transition-all duration-200 cursor-pointer relative',
            activeTab === 'chat'
              ? 'text-blue-600 dark:text-blue-400'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100/50 dark:hover:bg-slate-700/30'
          )}
          title="对话"
        >
          <MessageSquare className="w-5 h-5" />
          {activeTab === 'chat' && (
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('roles')}
          className={cn(
            'flex-1 p-3 flex justify-center items-center transition-all duration-200 cursor-pointer relative',
            activeTab === 'roles'
              ? 'text-blue-600 dark:text-blue-400'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100/50 dark:hover:bg-slate-700/30'
          )}
          title="角色"
        >
          <User className="w-5 h-5" />
          {activeTab === 'roles' && (
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('workspaces')}
          className={cn(
            'flex-1 p-3 flex justify-center items-center transition-all duration-200 cursor-pointer relative',
            activeTab === 'workspaces'
              ? 'text-blue-600 dark:text-blue-400'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100/50 dark:hover:bg-slate-700/30'
          )}
          title="工作空间"
        >
          <FolderOpen className="w-5 h-5" />
          {activeTab === 'workspaces' && (
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" />
          )}
        </button>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'chat' && isOpen && (
          <div className="p-3 space-y-2 animate-fade-in">
            {/* 新对话按钮 */}
            <button
              onClick={handleNewConversation}
              className="w-full flex items-center gap-2 p-3 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-700 text-slate-500 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/20 transition-all duration-200 cursor-pointer group"
            >
              <Plus className="w-5 h-5 group-hover:scale-110 group-hover:rotate-90 transition-transform duration-300" />
              <span className="font-medium">新对话</span>
            </button>
            
            {/* 历史对话列表 */}
            {conversations.length > 0 && (
              <>
                <div className="text-xs font-medium text-slate-400 uppercase tracking-wider px-2 pt-4 pb-2">
                  对话历史
                </div>
                <div className="space-y-1">
                  {conversations.map((conv, index) => (
                    <div
                      key={conv.id}
                      onClick={() => setCurrentConversation(conv.id)}
                      onMouseEnter={() => setHoveredConversation(conv.id)}
                      onMouseLeave={() => setHoveredConversation(null)}
                      style={{ animationDelay: `${index * 50}ms` }}
                      className={cn(
                        'group flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200 animate-slide-up',
                        currentConversationId === conv.id
                          ? 'bg-gradient-to-r from-blue-50 to-blue-50/50 dark:from-blue-900/30 dark:to-blue-900/10 text-blue-700 dark:text-blue-300 shadow-sm border border-blue-100 dark:border-blue-800/50'
                          : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                      )}
                    >
                      <MessageSquare className={cn(
                        'w-4 h-4 flex-shrink-0 transition-colors duration-200',
                        currentConversationId === conv.id ? 'text-blue-500' : 'text-slate-400 group-hover:text-slate-500'
                      )} />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{conv.title}</div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          {formatTime(conv.updatedAt)}
                        </div>
                      </div>
                      {hoveredConversation === conv.id && (
                        <button
                          onClick={(e) => handleDeleteConversation(e, conv.id)}
                          className="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-slate-400 hover:text-red-500 transition-all duration-200 cursor-pointer hover:scale-110 active:scale-95"
                          title="删除对话"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
            
            {conversations.length === 0 && (
              <div className="text-center py-10 text-slate-400">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                  <MessageSquare className="w-8 h-8 opacity-50" />
                </div>
                <p className="text-sm font-medium">暂无对话记录</p>
                <p className="text-xs mt-1 text-slate-400">点击上方按钮开始新对话</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'roles' && isOpen && (
          <div className="p-3 space-y-1 animate-fade-in">
            {roles.length === 0 ? (
              <RoleListSkeleton />
            ) : (
              roles.map((role, index) => (
                <button
                  key={role.id}
                  onClick={() => handleRoleSelect(role.id)}
                  style={{ animationDelay: `${index * 50}ms` }}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-xl transition-all duration-200 text-left cursor-pointer group animate-slide-up',
                    currentRole?.id === role.id
                      ? 'bg-gradient-to-r from-blue-50 to-blue-50/50 dark:from-blue-900/30 dark:to-blue-900/10 text-blue-700 dark:text-blue-300 shadow-sm border border-blue-100 dark:border-blue-800/50'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  )}
                >
                  <div className={cn(
                    'w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 shadow-sm',
                    currentRole?.id === role.id
                      ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-blue-500/30'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-500 group-hover:bg-slate-200 dark:group-hover:bg-slate-700 group-hover:scale-105'
                  )}>
                    {ROLE_ICONS[role.id] || <User className="w-5 h-5" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{role.display_name}</div>
                    <div className="text-xs text-slate-400 truncate">
                      {role.id === 'developer' && '代码开发与技术支持'}
                      {role.id === 'finance' && '财务分析与报表'}
                      {role.id === 'product' && '产品规划与需求'}
                      {role.id === 'project_manager' && '项目管理与协调'}
                      {role.id === 'operator' && '运营与推广'}
                      {role.id === 'tester' && '测试与质量保证'}
                      {role.id === 'researcher' && '调研与分析'}
                      {role.id === 'assistant' && '通用智能助手'}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        )}

        {activeTab === 'workspaces' && isOpen && (
          <div className="p-3 space-y-2 animate-fade-in">
            <button
              onClick={() => setShowCreateWorkspace(true)}
              className="w-full flex items-center gap-2 p-3 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-700 text-slate-500 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/20 transition-all duration-200 cursor-pointer group"
            >
              <Plus className="w-5 h-5 group-hover:scale-110 group-hover:rotate-90 transition-transform duration-300" />
              <span className="font-medium">新建工作空间</span>
            </button>
            
            {workspaces.length > 0 ? (
              <div className="space-y-1 mt-2">
                {workspaces.map((ws, index) => (
                  <div
                    key={ws.id}
                    style={{ animationDelay: `${index * 50}ms` }}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-xl transition-all duration-200 cursor-pointer group animate-slide-up',
                      currentWorkspace?.id === ws.id
                        ? 'bg-gradient-to-r from-blue-50 to-blue-50/50 dark:from-blue-900/30 dark:to-blue-900/10 text-blue-700 dark:text-blue-300 shadow-sm border border-blue-100 dark:border-blue-800/50'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                    )}
                    onClick={() => {
                      setCurrentWorkspace(ws)
                      router.push(`/workspace/${ws.id}`)
                    }}
                  >
                    <div className={cn(
                      'w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200',
                      currentWorkspace?.id === ws.id
                        ? 'bg-blue-500 text-white shadow-sm shadow-blue-500/30'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-400 group-hover:bg-slate-200 dark:group-hover:bg-slate-700'
                    )}>
                      <FolderOpen className="w-4 h-4" />
                    </div>
                    <span className="flex-1 text-sm font-medium truncate">{ws.name}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10 text-slate-400">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                  <FolderOpen className="w-8 h-8 opacity-50" />
                </div>
                <p className="text-sm font-medium">暂无工作空间</p>
                <p className="text-xs mt-1 text-slate-400">点击上方按钮创建</p>
              </div>
            )}
          </div>
        )}

        {/* 折叠状态下的图标导航 */}
        {!isOpen && (
          <div className="p-2 space-y-1">
            <button
              onClick={handleNewConversation}
              className="w-full p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200 cursor-pointer hover:scale-105 active:scale-95"
              title="新对话"
            >
              <Plus className="w-5 h-5 mx-auto text-slate-500" />
            </button>
          </div>
        )}
      </div>

      {/* 底部设置 */}
      <div className="p-3 border-t border-slate-200/50 dark:border-slate-700/50">
        <Link
          href="/settings"
          className={cn(
            'flex items-center gap-3 p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200 text-slate-600 dark:text-slate-400 cursor-pointer group',
            !isOpen && 'justify-center'
          )}
        >
          <Settings className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
          {isOpen && <span className="text-sm font-medium">设置</span>}
        </Link>
      </div>

      {/* 创建工作空间对话框 */}
      <CreateWorkspaceModal
        isOpen={showCreateWorkspace}
        onClose={() => setShowCreateWorkspace(false)}
        onCreated={(workspace) => {
          setWorkspaces([workspace, ...workspaces])
          setCurrentWorkspace(workspace)
          router.push(`/workspace/${workspace.id}`)
        }}
      />
    </aside>
  )
}
