'use client'

import { useState, useEffect } from 'react'
import { Sidebar } from '@/components/Sidebar'
import { ChatWindow } from '@/components/ChatWindow'
import { useStore } from '@/lib/store'

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { currentRole, setCurrentRole } = useStore()
  
  useEffect(() => {
    // 获取当前角色
    fetch('/api/v1/roles/current')
      .then(res => res.json())
      .then(data => {
        if (data.data?.current) {
          setCurrentRole(data.data.current)
        }
      })
      .catch(console.error)
  }, [setCurrentRole])

  return (
    <main className="flex h-screen bg-slate-50 dark:bg-slate-900">
      {/* 侧边栏 */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)} 
      />
      
      {/* 主内容区 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ChatWindow />
      </div>
    </main>
  )
}
