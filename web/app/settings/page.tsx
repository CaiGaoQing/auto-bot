'use client'

import { useState, useEffect } from 'react'
import { 
  ArrowLeft, 
  Bot, 
  Key, 
  Plus, 
  Trash2, 
  Check, 
  X,
  Eye,
  EyeOff,
  Loader2,
  Server,
  Zap,
  Image,
  TestTube,
} from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

interface Provider {
  name: string
  display_name: string
  api_key_set: boolean
  base_url?: string
  models: string[]
  enabled: boolean
}

interface ProviderForm {
  name: string
  api_key: string
  base_url: string
  models: string
}

interface ImageGenConfig {
  enabled: boolean
  provider: string
  base_url: string
  api_key_set: boolean
  model: string
  default_size: string
  available_models: string[]
  available_sizes: string[]
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'providers' | 'image' | 'general'>('providers')
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState<ProviderForm>({
    name: '',
    api_key: '',
    base_url: '',
    models: '',
  })
  const [showApiKey, setShowApiKey] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  
  // 图像生成配置
  const [imageConfig, setImageConfig] = useState<ImageGenConfig | null>(null)
  const [imageForm, setImageForm] = useState({
    base_url: '',
    api_key: '',
    model: '',
  })
  const [showImageApiKey, setShowImageApiKey] = useState(false)
  const [testingImage, setTestingImage] = useState(false)

  useEffect(() => {
    loadProviders()
    loadImageConfig()
  }, [])

  const loadProviders = async () => {
    try {
      const res = await fetch('/api/v1/providers')
      const data = await res.json()
      if (data.data?.items) {
        setProviders(data.data.items)
      }
    } catch (error) {
      console.error('加载提供商失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadImageConfig = async () => {
    try {
      const res = await fetch('/api/v1/image-gen/config')
      const data = await res.json()
      if (data.data) {
        setImageConfig(data.data)
        setImageForm({
          base_url: data.data.base_url || '',
          api_key: '',
          model: data.data.model || 'dall-e-3',
        })
      }
    } catch (error) {
      console.error('加载图像配置失败:', error)
    }
  }
  
  const handleSaveImageConfig = async () => {
    setSaving(true)
    setMessage(null)
    
    try {
      const payload: Record<string, string | boolean> = {}
      if (imageForm.base_url) payload.base_url = imageForm.base_url
      if (imageForm.api_key) payload.api_key = imageForm.api_key
      if (imageForm.model) payload.model = imageForm.model
      
      const res = await fetch('/api/v1/image-gen/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      
      if (res.ok) {
        setMessage({ type: 'success', text: '图像生成配置已保存' })
        loadImageConfig()
      } else {
        setMessage({ type: 'error', text: '保存失败' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误' })
    } finally {
      setSaving(false)
    }
  }
  
  const handleTestImage = async () => {
    setTestingImage(true)
    setMessage(null)
    
    try {
      const res = await fetch('/api/v1/image-gen/test', {
        method: 'POST',
      })
      const data = await res.json()
      
      if (data.data?.success) {
        setMessage({ type: 'success', text: '图像生成测试成功！' })
      } else {
        setMessage({ type: 'error', text: data.message || '测试失败' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: '测试请求失败' })
    } finally {
      setTestingImage(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)

    try {
      const res = await fetch('/api/v1/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          api_key: formData.api_key,
          base_url: formData.base_url || undefined,
          models: formData.models ? formData.models.split(',').map(m => m.trim()) : undefined,
        }),
      })

      const data = await res.json()

      if (res.ok) {
        setMessage({ type: 'success', text: '提供商添加成功' })
        setShowForm(false)
        setFormData({ name: '', api_key: '', base_url: '', models: '' })
        loadProviders()
      } else {
        setMessage({ type: 'error', text: data.message || '添加失败' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误' })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (name: string) => {
    if (!confirm(`确定删除提供商 "${name}" ?`)) return

    try {
      const res = await fetch(`/api/v1/providers/${name}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        setMessage({ type: 'success', text: '删除成功' })
        loadProviders()
      } else {
        setMessage({ type: 'error', text: '删除失败' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误' })
    }
  }

  const handleToggle = async (name: string, enabled: boolean) => {
    try {
      const res = await fetch(`/api/v1/providers/${name}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !enabled }),
      })

      if (res.ok) {
        loadProviders()
      }
    } catch (error) {
      console.error('切换失败:', error)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* 头部 */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link 
            href="/"
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-xl font-semibold">设置</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* 标签页 */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <button
            onClick={() => setActiveTab('providers')}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer',
              activeTab === 'providers'
                ? 'bg-blue-500 text-white'
                : 'bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700'
            )}
          >
            <Bot className="w-4 h-4 inline-block mr-2" />
            AI 提供商
          </button>
          <button
            onClick={() => setActiveTab('image')}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer',
              activeTab === 'image'
                ? 'bg-blue-500 text-white'
                : 'bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700'
            )}
          >
            <Image className="w-4 h-4 inline-block mr-2" />
            图像生成
          </button>
          <button
            onClick={() => setActiveTab('general')}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer',
              activeTab === 'general'
                ? 'bg-blue-500 text-white'
                : 'bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700'
            )}
          >
            <Zap className="w-4 h-4 inline-block mr-2" />
            通用设置
          </button>
        </div>

        {/* 消息提示 */}
        {message && (
          <div
            className={cn(
              'mb-6 p-4 rounded-lg flex items-center gap-2',
              message.type === 'success'
                ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'
            )}
          >
            {message.type === 'success' ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
            {message.text}
          </div>
        )}

        {/* AI 提供商配置 */}
        {activeTab === 'providers' && (
          <div className="space-y-6">
            {/* 添加按钮 */}
            <div className="flex justify-between items-center">
              <p className="text-slate-600 dark:text-slate-400">
                配置 AI 提供商的 API Key 和模型
              </p>
              <button
                onClick={() => setShowForm(!showForm)}
                className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                添加提供商
              </button>
            </div>

            {/* 添加表单 */}
            {showForm && (
              <form
                onSubmit={handleSubmit}
                className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700"
              >
                <h3 className="text-lg font-semibold mb-4">添加 AI 提供商</h3>
                
                <div className="grid gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      提供商名称 <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                      required
                    >
                      <option value="">选择提供商</option>
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic (Claude)</option>
                      <option value="deepseek">DeepSeek</option>
                      <option value="openrouter">OpenRouter</option>
                      <option value="azure">Azure OpenAI</option>
                      <option value="custom">自定义</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      API Key <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={formData.api_key}
                        onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                        placeholder="sk-..."
                        className="w-full px-3 py-2 pr-10 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600"
                      >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      API 地址 (可选，用于代理/中转)
                    </label>
                    <input
                      type="url"
                      value={formData.base_url}
                      onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                      placeholder="https://api.openai.com/v1"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      支持 API 代理/中转站地址
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      模型列表 (可选，逗号分隔)
                    </label>
                    <input
                      type="text"
                      value={formData.models}
                      onChange={(e) => setFormData({ ...formData, models: e.target.value })}
                      placeholder="gpt-4o, gpt-4o-mini, gpt-3.5-turbo"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
                  >
                    {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                    保存
                  </button>
                </div>
              </form>
            )}

            {/* 提供商列表 */}
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
              </div>
            ) : providers.length === 0 ? (
              <div className="bg-white dark:bg-slate-800 rounded-xl p-12 text-center border border-slate-200 dark:border-slate-700">
                <Server className="w-12 h-12 mx-auto text-slate-400 mb-4" />
                <p className="text-slate-500">暂无配置的 AI 提供商</p>
                <p className="text-sm text-slate-400 mt-1">点击上方按钮添加</p>
              </div>
            ) : (
              <div className="space-y-4">
                {providers.map((provider) => (
                  <div
                    key={provider.name}
                    className="bg-white dark:bg-slate-800 rounded-xl p-5 border border-slate-200 dark:border-slate-700"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          'w-10 h-10 rounded-lg flex items-center justify-center',
                          provider.enabled
                            ? 'bg-green-100 dark:bg-green-900/20 text-green-600'
                            : 'bg-slate-100 dark:bg-slate-700 text-slate-400'
                        )}>
                          <Bot className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{provider.display_name || provider.name}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={cn(
                              'text-xs px-2 py-0.5 rounded-full',
                              provider.api_key_set
                                ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                                : 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                            )}>
                              {provider.api_key_set ? 'API Key 已配置' : '未配置'}
                            </span>
                            {provider.base_url && (
                              <span className="text-xs text-slate-500">
                                {new URL(provider.base_url).host}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggle(provider.name, provider.enabled)}
                          className={cn(
                            'relative w-12 h-6 rounded-full transition-colors',
                            provider.enabled ? 'bg-green-500' : 'bg-slate-300 dark:bg-slate-600'
                          )}
                        >
                          <span
                            className={cn(
                              'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                              provider.enabled ? 'translate-x-7' : 'translate-x-1'
                            )}
                          />
                        </button>
                        <button
                          onClick={() => handleDelete(provider.name)}
                          className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {provider.models && provider.models.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {provider.models.slice(0, 5).map((model) => (
                          <span
                            key={model}
                            className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded"
                          >
                            {model}
                          </span>
                        ))}
                        {provider.models.length > 5 && (
                          <span className="text-xs text-slate-500">
                            +{provider.models.length - 5} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 图像生成配置 */}
        {activeTab === 'image' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <Image className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">图像生成配置</h3>
                  <p className="text-sm text-slate-500">配置 AI 图像生成服务（支持 Nano Banana 中转站）</p>
                </div>
              </div>
              
              {imageConfig && (
                <div className="mb-6 p-4 rounded-lg bg-slate-50 dark:bg-slate-900">
                  <div className="flex items-center gap-4 text-sm">
                    <span className={cn(
                      'px-2 py-1 rounded-full',
                      imageConfig.api_key_set
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                        : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400'
                    )}>
                      {imageConfig.api_key_set ? '已配置' : '未配置'}
                    </span>
                    <span className="text-slate-500">模型: {imageConfig.model}</span>
                    <span className="text-slate-500">尺寸: {imageConfig.default_size}</span>
                  </div>
                </div>
              )}
              
              <div className="grid gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    API 地址（中转站地址）
                  </label>
                  <input
                    type="url"
                    value={imageForm.base_url}
                    onChange={(e) => setImageForm({ ...imageForm, base_url: e.target.value })}
                    placeholder="https://api.nanobanana.com/v1 或 https://api.openai.com/v1"
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    支持 OpenAI 官方或兼容的中转站（如 Nano Banana）
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">
                    API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showImageApiKey ? 'text' : 'password'}
                      value={imageForm.api_key}
                      onChange={(e) => setImageForm({ ...imageForm, api_key: e.target.value })}
                      placeholder={imageConfig?.api_key_set ? '已配置，留空保持不变' : 'sk-...'}
                      className="w-full px-3 py-2 pr-10 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowImageApiKey(!showImageApiKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      {showImageApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">
                    模型
                  </label>
                  <select
                    value={imageForm.model}
                    onChange={(e) => setImageForm({ ...imageForm, model: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {imageConfig?.available_models?.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={handleTestImage}
                  disabled={testingImage}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors cursor-pointer disabled:opacity-50"
                >
                  {testingImage ? <Loader2 className="w-4 h-4 animate-spin" /> : <TestTube className="w-4 h-4" />}
                  测试连接
                </button>
                <button
                  onClick={handleSaveImageConfig}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors cursor-pointer disabled:opacity-50"
                >
                  {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                  保存配置
                </button>
              </div>
            </div>
            
            {/* 说明 */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold text-blue-700 dark:text-blue-300 mb-2">如何使用 Nano Banana 中转站</h4>
              <ol className="text-sm text-blue-600 dark:text-blue-400 space-y-2 list-decimal list-inside">
                <li>访问 Nano Banana 获取 API Key</li>
                <li>将 API 地址设置为中转站地址（如 https://api.nanobanana.com/v1）</li>
                <li>填入获取的 API Key</li>
                <li>选择模型（如 dall-e-3）</li>
                <li>点击"测试连接"验证配置</li>
              </ol>
              <p className="text-sm text-blue-600 dark:text-blue-400 mt-3">
                配置完成后，在工作空间对话中请求生成 PPT 时会自动生成配图。
              </p>
            </div>
          </div>
        )}

        {/* 通用设置 */}
        {activeTab === 'general' && (
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700">
            <h3 className="text-lg font-semibold mb-4">通用设置</h3>
            <p className="text-slate-500">更多设置功能开发中...</p>
          </div>
        )}
      </main>
    </div>
  )
}
