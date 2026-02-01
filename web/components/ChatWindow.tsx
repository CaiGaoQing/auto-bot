'use client'

import { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  Loader2, 
  Paperclip, 
  Mic, 
  StopCircle, 
  User, 
  Bot,
  Sparkles,
  MessageSquare,
  Code,
  DollarSign,
  ClipboardList,
  BarChart3,
  Megaphone,
  Search,
  FlaskConical,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn, formatDate } from '@/lib/utils'
import { useStore } from '@/lib/store'

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

export function ChatWindow() {
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  const { 
    messages, 
    addMessage, 
    updateMessage, 
    isLoading, 
    setLoading,
    currentRole,
    currentWorkspace,
    currentConversationId,
    createConversation,
  } = useStore()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading) return
    
    // 如果没有当前对话，创建一个
    if (!currentConversationId) {
      createConversation(currentRole?.id || 'assistant', currentWorkspace?.id)
    }
    
    const userMessage = input.trim()
    setInput('')
    
    // 添加用户消息
    addMessage({ role: 'user', content: userMessage })
    
    // 添加助手消息占位
    const assistantMsgId = addMessage({ 
      role: 'assistant', 
      content: '', 
      isStreaming: true,
    })
    
    setLoading(true)
    
    try {
      // 使用 AbortController 设置 2 分钟超时
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 120000)
      
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          workspace_id: currentWorkspace?.id,
          role_id: currentRole?.id || 'assistant',
        }),
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)
      const data = await res.json()
      
      if (data.data?.content) {
        updateMessage(assistantMsgId, data.data.content)
      } else if (data.detail) {
        updateMessage(assistantMsgId, `错误: ${data.detail}`)
      } else {
        updateMessage(assistantMsgId, '抱歉，处理请求时出错了。')
      }
    } catch (error: unknown) {
      console.error('请求失败:', error)
      const errorMessage = error instanceof Error && error.name === 'AbortError'
        ? '请求超时，请重试。'
        : '网络错误，请重试。'
      updateMessage(assistantMsgId, errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const getRoleIcon = () => {
    if (currentRole?.id && ROLE_ICONS[currentRole.id]) {
      return ROLE_ICONS[currentRole.id]
    }
    return <Bot className="w-5 h-5" />
  }

  return (
    <div className="flex-1 flex flex-col bg-slate-50 dark:bg-slate-950 gradient-mesh">
      {/* 头部 */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          {currentRole ? (
            <>
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/30 animate-scale-in">
                {getRoleIcon()}
              </div>
              <div className="animate-fade-in">
                <h1 className="font-semibold text-slate-900 dark:text-slate-100">
                  {currentRole.display_name}
                </h1>
                <div className="flex items-center gap-2">
                  <span className="status-dot online" />
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {currentWorkspace ? currentWorkspace.name : '在线'}
                  </p>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-slate-400 to-slate-500 flex items-center justify-center text-white shadow-lg">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h1 className="font-semibold text-slate-900 dark:text-slate-100">AI Auto</h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">选择一个角色开始对话</p>
              </div>
            </>
          )}
        </div>
      </header>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center mb-6 shadow-2xl shadow-blue-500/30 animate-float">
              <MessageSquare className="w-12 h-12 text-white" />
            </div>
            <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-3">
              开始新对话
            </h2>
            <p className="text-slate-500 dark:text-slate-400 max-w-md leading-relaxed">
              {currentRole
                ? `${currentRole.display_name} 已准备就绪，随时为您服务`
                : '直接输入问题开始对话，或从左侧选择专业角色'
              }
            </p>
            
            {/* Quick prompts */}
            <div className="mt-8 flex flex-wrap justify-center gap-3 max-w-2xl">
              {currentRole?.id === 'developer' && (
                <>
                  <QuickPrompt text="帮我写一个 Python 脚本" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="解释这段代码" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="如何优化性能" onClick={(t) => setInput(t)} />
                </>
              )}
              {currentRole?.id === 'finance' && (
                <>
                  <QuickPrompt text="分析这份财务报表" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="帮我做预算规划" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="计算投资回报率" onClick={(t) => setInput(t)} />
                </>
              )}
              {currentRole?.id === 'product' && (
                <>
                  <QuickPrompt text="写一份需求文档" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="分析竞品功能" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="设计用户故事" onClick={(t) => setInput(t)} />
                </>
              )}
              {!currentRole && (
                <>
                  <QuickPrompt text="你好，介绍一下你自己" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="帮我写一段代码" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="分析一份文档" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="帮我做个计划" onClick={(t) => setInput(t)} />
                </>
              )}
              {currentRole && !['developer', 'finance', 'product'].includes(currentRole.id || '') && (
                <>
                  <QuickPrompt text="你能帮我做什么？" onClick={(t) => setInput(t)} />
                  <QuickPrompt text="介绍一下你的能力" onClick={(t) => setInput(t)} />
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message, index) => (
              <div
                key={message.id}
                style={{ animationDelay: `${index * 100}ms` }}
                className={cn(
                  'flex gap-4 animate-slide-up',
                  message.role === 'user' ? 'flex-row-reverse' : ''
                )}
              >
                {/* 头像 */}
                <div
                  className={cn(
                    'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg transition-transform duration-200 hover:scale-105',
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-slate-600 to-slate-700 shadow-slate-500/20'
                      : 'bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 shadow-blue-500/30'
                  )}
                >
                  {message.role === 'user' ? (
                    <User className="w-5 h-5 text-white" />
                  ) : (
                    <span className="text-white">{getRoleIcon()}</span>
                  )}
                </div>

                {/* 消息内容 */}
                <div
                  className={cn(
                    'max-w-[75%] rounded-2xl px-5 py-4 relative',
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/20'
                      : 'glass-card'
                  )}
                >
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  ) : (
                    <div className={cn(
                      'prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-100 prose-pre:dark:bg-slate-800 prose-pre:rounded-xl',
                      message.isStreaming && !message.content && 'typing-cursor'
                    )}>
                      {message.content ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <div className="flex items-center gap-3 text-slate-400">
                          <div className="flex gap-1">
                            <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                          <span>思考中...</span>
                        </div>
                      )}
                    </div>
                  )}
                  <div
                    className={cn(
                      'text-xs mt-3 opacity-60',
                      message.role === 'user'
                        ? 'text-blue-100'
                        : 'text-slate-400'
                    )}
                  >
                    {formatDate(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区 */}
      <div className="p-4 border-t border-slate-200/50 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex items-end gap-3 p-3 rounded-2xl bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/50 dark:border-slate-700/50 focus-within:ring-2 focus-within:ring-blue-500/50 focus-within:border-blue-500/50 transition-all duration-200 shadow-lg shadow-slate-200/50 dark:shadow-slate-900/50">
            {/* 附件按钮 */}
            <button
              type="button"
              className="p-2.5 text-slate-400 hover:text-blue-500 transition-all duration-200 cursor-pointer rounded-xl hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:scale-105 active:scale-95"
              title="添加附件"
            >
              <Paperclip className="w-5 h-5" />
            </button>

            {/* 输入框 */}
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                currentRole
                  ? `向 ${currentRole.display_name} 提问...`
                  : '输入问题开始对话...'
              }
              rows={1}
              className="flex-1 resize-none bg-transparent px-2 py-2 focus:outline-none text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
              style={{
                minHeight: '24px',
                maxHeight: '200px',
              }}
            />

            {/* 语音按钮 */}
            <button
              type="button"
              onClick={() => setIsRecording(!isRecording)}
              className={cn(
                'p-2.5 rounded-xl transition-all duration-200 cursor-pointer',
                isRecording
                  ? 'text-red-500 bg-red-50 dark:bg-red-900/20 shadow-lg shadow-red-500/20'
                  : 'text-slate-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:scale-105 active:scale-95'
              )}
              title={isRecording ? '停止录音' : '语音输入'}
            >
              {isRecording ? (
                <StopCircle className="w-5 h-5 animate-pulse" />
              ) : (
                <Mic className="w-5 h-5" />
              )}
            </button>

            {/* 发送按钮 */}
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={cn(
                'p-3 rounded-xl transition-all duration-200 cursor-pointer',
                input.trim() && !isLoading
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 hover:scale-105 active:scale-95'
                  : 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
              )}
              title="发送"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          <p className="text-xs text-center text-slate-400 mt-3">
            按 <kbd className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono text-[10px]">Enter</kbd> 发送，<kbd className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono text-[10px]">Shift + Enter</kbd> 换行
          </p>
        </form>
      </div>
    </div>
  )
}

// Quick prompt button component
function QuickPrompt({ text, onClick }: { text: string; onClick: (text: string) => void }) {
  return (
    <button
      onClick={() => onClick(text)}
      className="px-4 py-2.5 rounded-xl bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50 text-sm text-slate-600 dark:text-slate-300 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/20 transition-all duration-200 cursor-pointer shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0"
    >
      {text}
    </button>
  )
}
