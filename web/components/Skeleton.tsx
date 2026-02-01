'use client'

import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
  variant?: 'default' | 'shimmer'
}

export function Skeleton({ className, variant = 'shimmer' }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded-lg',
        variant === 'shimmer' ? 'skeleton-shimmer' : 'skeleton',
        className
      )}
    />
  )
}

// 消息骨架屏
export function MessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={cn('flex gap-4', isUser ? 'flex-row-reverse' : '')}>
      {/* 头像骨架 */}
      <Skeleton className="w-10 h-10 rounded-xl flex-shrink-0" />

      {/* 消息内容骨架 */}
      <div className={cn('max-w-[75%] space-y-2', isUser ? 'items-end' : '')}>
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-64" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-20 mt-3" />
      </div>
    </div>
  )
}

// 聊天列表骨架屏
export function ChatListSkeleton() {
  return (
    <div className="space-y-6 p-6 max-w-4xl mx-auto">
      <MessageSkeleton />
      <MessageSkeleton isUser />
      <MessageSkeleton />
    </div>
  )
}

// 侧边栏对话列表骨架屏
export function ConversationListSkeleton() {
  return (
    <div className="space-y-2 p-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-center gap-3 p-3">
          <Skeleton className="w-4 h-4 rounded" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}

// 角色列表骨架屏
export function RoleListSkeleton() {
  return (
    <div className="space-y-1 p-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center gap-3 p-3">
          <Skeleton className="w-10 h-10 rounded-xl" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-32" />
          </div>
        </div>
      ))}
    </div>
  )
}

// 工作空间列表骨架屏
export function WorkspaceListSkeleton() {
  return (
    <div className="space-y-1 p-3 mt-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-3 p-3">
          <Skeleton className="w-9 h-9 rounded-lg" />
          <Skeleton className="h-4 flex-1" />
        </div>
      ))}
    </div>
  )
}

// 卡片骨架屏
export function CardSkeleton() {
  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex items-center gap-4">
        <Skeleton className="w-12 h-12 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
      </div>
      <Skeleton className="h-20 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-9 w-24 rounded-xl" />
        <Skeleton className="h-9 w-24 rounded-xl" />
      </div>
    </div>
  )
}
