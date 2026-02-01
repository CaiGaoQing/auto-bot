'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  ArrowLeft,
  Upload,
  Download,
  Trash2,
  File,
  Folder,
  FolderOpen,
  FolderPlus,
  ChevronRight,
  ChevronDown,
  Code,
  FileText,
  FileSpreadsheet,
  Image,
  Presentation,
  MoreHorizontal,
  Eye,
  X,
  Play,
  Loader2,
  Home,
  Send,
  MessageSquare,
  Bot,
  User,
  Sparkles,
} from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  files?: string[]
}

interface FileItem {
  name: string
  path: string
  type: 'file' | 'folder'
  file_type?: string
  size?: number
  modified_at?: string
  children?: FileItem[]
  children_count?: number
}

interface Workspace {
  id: string
  name: string
  roles: string[]
  description: string
  created_at: string
}

// 文件图标映射
function getFileIcon(fileType: string, size: string = 'w-5 h-5') {
  const icons: Record<string, React.ReactNode> = {
    code: <Code className={cn(size, 'text-blue-500')} />,
    document: <FileText className={cn(size, 'text-orange-500')} />,
    data: <FileSpreadsheet className={cn(size, 'text-green-500')} />,
    presentation: <Presentation className={cn(size, 'text-red-500')} />,
    image: <Image className={cn(size, 'text-purple-500')} />,
    file: <File className={cn(size, 'text-slate-400')} />,
  }
  return icons[fileType] || icons.file
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// 文件树节点
function FileTreeNode({ 
  item, 
  level = 0,
  onSelect,
  selectedPath,
}: { 
  item: FileItem
  level?: number
  onSelect: (item: FileItem) => void
  selectedPath: string | null
}) {
  const [expanded, setExpanded] = useState(level < 1)
  
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (item.type === 'folder') {
      setExpanded(!expanded)
    }
    onSelect(item)
  }
  
  const handleExpandClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setExpanded(!expanded)
  }
  
  return (
    <div>
      <button
        type="button"
        onClick={handleClick}
        className={cn(
          'w-full flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors text-left',
          selectedPath === item.path
            ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
            : 'hover:bg-slate-100 dark:hover:bg-slate-800'
        )}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {item.type === 'folder' ? (
          <>
            <span onClick={handleExpandClick} className="flex-shrink-0">
              {expanded ? (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-400" />
              )}
            </span>
            {expanded ? (
              <FolderOpen className="w-5 h-5 text-amber-500 flex-shrink-0" />
            ) : (
              <Folder className="w-5 h-5 text-amber-500 flex-shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-4" />
            {getFileIcon(item.file_type || 'file')}
          </>
        )}
        <span className="text-sm truncate flex-1">{item.name}</span>
        {item.type === 'folder' && item.children_count !== undefined && item.children_count > 0 && (
          <span className="text-xs text-slate-400">{item.children_count}</span>
        )}
      </button>
      
      {item.type === 'folder' && expanded && item.children && (
        <div>
          {item.children.map((child) => (
            <FileTreeNode
              key={child.path}
              item={child}
              level={level + 1}
              onSelect={onSelect}
              selectedPath={selectedPath}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function WorkspacePage() {
  const params = useParams()
  const router = useRouter()
  const workspaceId = params.id as string
  
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [fileTree, setFileTree] = useState<FileItem[]>([])
  const [selectedItem, setSelectedItem] = useState<FileItem | null>(null)
  const [previewContent, setPreviewContent] = useState<{content: string, language: string} | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showNewFolder, setShowNewFolder] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [currentPath, setCurrentPath] = useState('')
  
  // 对话相关状态
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [activeView, setActiveView] = useState<'files' | 'chat'>('files')
  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 加载工作空间
  const loadWorkspace = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/workspaces/${workspaceId}`)
      const data = await res.json()
      if (data.code === 0 && data.data) {
        setWorkspace(data.data)
      }
    } catch (error) {
      console.error('加载工作空间失败:', error)
    }
  }, [workspaceId])

  // 加载文件树
  const loadFileTree = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/workspaces/${workspaceId}/tree`)
      const data = await res.json()
      if (data.code === 0 && data.data) {
        setFileTree(data.data.tree || [])
      }
    } catch (error) {
      console.error('加载文件树失败:', error)
    } finally {
      setLoading(false)
    }
  }, [workspaceId])

  useEffect(() => {
    loadWorkspace()
    loadFileTree()
  }, [loadWorkspace, loadFileTree])

  // 滚动到最新消息
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  // 发送消息
  const handleSendMessage = async () => {
    if (!chatInput.trim() || isSending) return
    
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date(),
      files: selectedItem?.type === 'file' ? [selectedItem.path] : undefined,
    }
    
    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setIsSending(true)
    
    // 添加助手占位消息
    const assistantId = `msg_${Date.now()}_assistant`
    setChatMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }])
    
    try {
      // 使用 AbortController 设置 2 分钟超时
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 120000)
      
      // 构建消息，如果有选中的文件，添加上下文
      let fullMessage = userMessage.content
      if (selectedItem?.type === 'file') {
        fullMessage = `[参考文件: ${selectedItem.path}]\n\n${userMessage.content}`
      }
      
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: fullMessage,
          workspace_id: workspaceId,
          save_to_workspace: true,
        }),
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)
      const data = await res.json()
      
      let responseContent = data.data?.content || '抱歉，处理时出错了。'
      
      // 如果保存了文件，添加提示
      if (data.data?.saved_file) {
        responseContent += `\n\n---\n📄 **已保存到**: \`${data.data.saved_file}\``
        // 刷新文件树
        await loadFileTree()
      }
      
      setChatMessages(prev => prev.map(msg => 
        msg.id === assistantId 
          ? { ...msg, content: responseContent }
          : msg
      ))
    } catch (error: unknown) {
      const errorMessage = error instanceof Error && error.name === 'AbortError'
        ? '请求超时，请重试。'
        : '网络错误，请重试。'
      setChatMessages(prev => prev.map(msg => 
        msg.id === assistantId 
          ? { ...msg, content: errorMessage }
          : msg
      ))
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 选择文件/文件夹
  const handleSelect = async (item: FileItem) => {
    setSelectedItem(item)
    setCurrentPath(item.path)
    
    if (item.type === 'file') {
      // 预览文件
      try {
        const res = await fetch(`/api/v1/workspaces/${workspaceId}/preview/${item.path}`)
        const data = await res.json()
        if (data.code === 0 && data.data?.preview) {
          setPreviewContent({
            content: data.data.content,
            language: data.data.language,
          })
        } else {
          setPreviewContent(null)
        }
      } catch (error) {
        setPreviewContent(null)
      }
    } else {
      setPreviewContent(null)
    }
  }

  // 上传文件
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    
    setUploading(true)
    
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)
        if (currentPath && selectedItem?.type === 'folder') {
          formData.append('path', currentPath)
        }
        
        await fetch(`/api/v1/workspaces/${workspaceId}/upload`, {
          method: 'POST',
          body: formData,
        })
      }
      
      await loadFileTree()
    } catch (error) {
      console.error('上传失败:', error)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  // 创建文件夹
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return
    
    const path = currentPath && selectedItem?.type === 'folder'
      ? `${currentPath}/${newFolderName}`
      : newFolderName
    
    try {
      await fetch(`/api/v1/workspaces/${workspaceId}/folders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      
      setShowNewFolder(false)
      setNewFolderName('')
      await loadFileTree()
    } catch (error) {
      console.error('创建文件夹失败:', error)
    }
  }

  // 下载文件
  const handleDownload = () => {
    if (!selectedItem || selectedItem.type !== 'file') return
    
    const url = `/api/v1/workspaces/${workspaceId}/download/${selectedItem.path}`
    const a = document.createElement('a')
    a.href = url
    a.download = selectedItem.name
    a.click()
  }

  // 删除
  const handleDelete = async () => {
    if (!selectedItem) return
    if (!confirm(`确定删除 ${selectedItem.name}？`)) return
    
    try {
      await fetch(`/api/v1/workspaces/${workspaceId}/path/${selectedItem.path}`, {
        method: 'DELETE',
      })
      
      setSelectedItem(null)
      setPreviewContent(null)
      await loadFileTree()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* 头部 */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 py-3 flex items-center gap-4">
        <Link
          href="/"
          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-5 h-5 text-slate-500" />
        </Link>
        
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100 truncate">
            {workspace?.name || '工作空间'}
          </h1>
          <div className="flex items-center gap-2">
            {workspace?.roles?.map((role) => (
              <span
                key={role}
                className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600"
              >
                {role}
              </span>
            ))}
          </div>
        </div>
        
        {/* 视图切换 + 操作按钮 */}
        <div className="flex items-center gap-2">
          {/* 视图切换 */}
          <div className="flex rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
            <button
              onClick={() => setActiveView('files')}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors cursor-pointer',
                activeView === 'files'
                  ? 'bg-white dark:bg-slate-700 text-blue-600 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <Folder className="w-4 h-4" />
              文件
            </button>
            <button
              onClick={() => setActiveView('chat')}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors cursor-pointer',
                activeView === 'chat'
                  ? 'bg-white dark:bg-slate-700 text-blue-600 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              <MessageSquare className="w-4 h-4" />
              对话
            </button>
          </div>
          
          {activeView === 'files' && (
            <>
              <label className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors cursor-pointer text-sm">
                {uploading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                上传
                <input
                  type="file"
                  multiple
                  onChange={handleUpload}
                  className="hidden"
                  disabled={uploading}
                />
              </label>
              
              <button
                onClick={() => setShowNewFolder(true)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer text-sm"
              >
                <FolderPlus className="w-4 h-4" />
                新建文件夹
              </button>
            </>
          )}
        </div>
      </header>

      {/* 主体 */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* 左侧文件树 - 始终显示，固定宽度和高度 */}
        <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex-shrink-0 flex flex-col">
          <div className="flex-1 overflow-y-auto">
          <div className="p-3">
            <div
              onClick={() => {
                setSelectedItem(null)
                setCurrentPath('')
                setPreviewContent(null)
              }}
              className={cn(
                'flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors mb-2',
                !selectedItem
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700'
                  : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              )}
            >
              <Home className="w-5 h-5 text-slate-500" />
              <span className="text-sm font-medium">根目录</span>
            </div>
            
            {fileTree.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Folder className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">暂无文件</p>
                <p className="text-xs mt-1">上传文件开始工作</p>
              </div>
            ) : (
              fileTree.map((item) => (
                <FileTreeNode
                  key={item.path}
                  item={item}
                  onSelect={handleSelect}
                  selectedPath={selectedItem?.path || null}
                />
              ))
            )}
          </div>
          </div>
        </aside>

        {activeView === 'files' ? (
          /* 右侧内容区 - 文件预览 */
          <main className="flex-1 flex flex-col overflow-hidden">
              {selectedItem ? (
                <>
                  {/* 文件信息栏 */}
                  <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 py-3 flex items-center gap-4">
                    {selectedItem.type === 'file' ? (
                      getFileIcon(selectedItem.file_type || 'file', 'w-6 h-6')
                    ) : (
                      <Folder className="w-6 h-6 text-amber-500" />
                    )}
                    
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-slate-900 dark:text-slate-100 truncate">
                        {selectedItem.name}
                      </div>
                      <div className="text-xs text-slate-500">
                        {selectedItem.path}
                        {selectedItem.size !== undefined && ` • ${formatFileSize(selectedItem.size)}`}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {selectedItem.type === 'file' && (
                        <button
                          onClick={handleDownload}
                          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-blue-500 transition-colors cursor-pointer"
                          title="下载"
                        >
                          <Download className="w-5 h-5" />
                        </button>
                      )}
                      <button
                        onClick={handleDelete}
                        className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-red-500 transition-colors cursor-pointer"
                        title="删除"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                  
                  {/* 预览区 */}
                  <div className="flex-1 overflow-auto p-4">
                    {previewContent ? (
                      <div className="bg-slate-900 rounded-xl overflow-hidden">
                        <div className="flex items-center justify-between px-4 py-2 bg-slate-800 text-slate-400 text-sm">
                          <span>{selectedItem.name}</span>
                          <span>{previewContent.language}</span>
                        </div>
                        <pre className="p-4 text-sm text-slate-300 overflow-x-auto">
                          <code>{previewContent.content}</code>
                        </pre>
                      </div>
                    ) : selectedItem.type === 'file' ? (
                      <div className="flex flex-col items-center justify-center h-full text-slate-400">
                        {getFileIcon(selectedItem.file_type || 'file', 'w-16 h-16')}
                        <p className="mt-4 text-lg">{selectedItem.name}</p>
                        <p className="text-sm mt-1">此文件类型不支持预览</p>
                        <button
                          onClick={handleDownload}
                          className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors cursor-pointer"
                        >
                          <Download className="w-4 h-4" />
                          下载文件
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-slate-400">
                        <Folder className="w-16 h-16 text-amber-500/50" />
                        <p className="mt-4 text-lg">{selectedItem.name}</p>
                        <p className="text-sm mt-1">
                          {selectedItem.children_count || 0} 个项目
                        </p>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
                  <Folder className="w-20 h-20 opacity-50" />
                  <p className="mt-4 text-xl">选择文件或文件夹</p>
                  <p className="text-sm mt-2">从左侧选择文件进行预览或管理</p>
                </div>
              )}
            </main>
        ) : (
          /* 对话视图 */
          <main className="flex-1 flex flex-col bg-white dark:bg-slate-900 overflow-hidden">
            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-6">
              {chatMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6 shadow-xl shadow-blue-500/20">
                    <Bot className="w-10 h-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
                    工作空间助手
                  </h2>
                  <p className="text-slate-500 dark:text-slate-400 max-w-md">
                    我可以帮你处理这个工作空间中的文件和任务
                  </p>
                  <div className="mt-6 flex flex-wrap justify-center gap-3">
                    <button
                      onClick={() => setChatInput('分析这个项目的结构')}
                      className="px-4 py-2 rounded-full bg-slate-100 dark:bg-slate-800 text-sm text-slate-600 dark:text-slate-300 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer"
                    >
                      分析项目结构
                    </button>
                    <button
                      onClick={() => setChatInput('帮我整理这些文件')}
                      className="px-4 py-2 rounded-full bg-slate-100 dark:bg-slate-800 text-sm text-slate-600 dark:text-slate-300 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer"
                    >
                      整理文件
                    </button>
                    <button
                      onClick={() => setChatInput('生成项目文档')}
                      className="px-4 py-2 rounded-full bg-slate-100 dark:bg-slate-800 text-sm text-slate-600 dark:text-slate-300 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer"
                    >
                      生成文档
                    </button>
                  </div>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto space-y-6">
                  {chatMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={cn(
                        'flex gap-4',
                        msg.role === 'user' ? 'flex-row-reverse' : ''
                      )}
                    >
                      <div className={cn(
                        'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0',
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-blue-500 to-blue-600'
                          : 'bg-gradient-to-br from-purple-500 to-purple-600'
                      )}>
                        {msg.role === 'user' ? (
                          <User className="w-5 h-5 text-white" />
                        ) : (
                          <Bot className="w-5 h-5 text-white" />
                        )}
                      </div>
                      
                      <div className={cn(
                        'max-w-[75%] px-4 py-3 rounded-2xl',
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                          : 'bg-slate-100 dark:bg-slate-800'
                      )}>
                        {msg.role === 'user' ? (
                          <>
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                            {msg.files && msg.files.length > 0 && (
                              <div className="mt-2 flex items-center gap-2 text-blue-100 text-sm">
                                <File className="w-4 h-4" />
                                <span>{msg.files[0]}</span>
                              </div>
                            )}
                          </>
                        ) : msg.content ? (
                          <div className="prose prose-sm dark:prose-invert max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-slate-400">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>思考中...</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>
              )}
            </div>
            
            {/* 输入区 */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800">
              <div className="max-w-3xl mx-auto">
                {selectedItem?.type === 'file' && (
                  <div className="mb-2 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-sm text-blue-600 flex items-center gap-2">
                    <File className="w-4 h-4" />
                    <span>已选择文件: {selectedItem.name}</span>
                    <button
                      onClick={() => setSelectedItem(null)}
                      className="ml-auto p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-800 cursor-pointer"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
                
                <div className="flex items-end gap-3 p-2 rounded-2xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-blue-500">
                  <textarea
                    ref={inputRef}
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="输入问题或任务..."
                    rows={1}
                    className="flex-1 resize-none bg-transparent px-2 py-2 focus:outline-none text-slate-900 dark:text-slate-100 placeholder:text-slate-400"
                    style={{ minHeight: '24px', maxHeight: '120px' }}
                  />
                  
                  <button
                    onClick={handleSendMessage}
                    disabled={!chatInput.trim() || isSending}
                    className={cn(
                      'p-2.5 rounded-xl transition-all cursor-pointer',
                      chatInput.trim() && !isSending
                        ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg shadow-blue-500/25'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                    )}
                  >
                    {isSending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </main>
        )}
      </div>

      {/* 新建文件夹对话框 */}
      {showNewFolder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowNewFolder(false)} />
          <div className="relative w-full max-w-md mx-4 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">新建文件夹</h3>
              <button
                onClick={() => setShowNewFolder(false)}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {currentPath && selectedItem?.type === 'folder' && (
              <p className="text-sm text-slate-500 mb-2">
                位置: {currentPath}/
              </p>
            )}
            
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateFolder()}
              placeholder="文件夹名称"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setShowNewFolder(false)}
                className="flex-1 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              >
                取消
              </button>
              <button
                onClick={handleCreateFolder}
                className="flex-1 px-4 py-2 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-colors cursor-pointer"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
