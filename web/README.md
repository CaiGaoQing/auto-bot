# AI Auto Web 前端

基于 Next.js 14 + React + TailwindCSS 构建的 AI 个人助手 Web 界面。

## 功能特性

- 🎨 现代化 UI 设计
- 🌙 深色模式支持
- 💬 实时对话
- 👤 多角色切换
- 📁 工作空间管理
- ⌨️ Markdown 渲染

## 快速开始

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 启动生产服务
npm start
```

## 技术栈

- **框架**: Next.js 14 (App Router)
- **UI**: TailwindCSS
- **状态管理**: Zustand
- **图标**: Lucide React
- **Markdown**: react-markdown + remark-gfm

## 目录结构

```
web/
├── app/              # Next.js 页面
│   ├── layout.tsx    # 根布局
│   ├── page.tsx      # 首页
│   └── globals.css   # 全局样式
├── components/       # React 组件
│   ├── Sidebar.tsx   # 侧边栏
│   └── ChatWindow.tsx # 聊天窗口
├── lib/              # 工具函数
│   ├── store.ts      # Zustand 状态
│   └── utils.ts      # 通用工具
└── public/           # 静态资源
```

## API 代理

开发模式下，`/api/*` 请求会被代理到 `http://localhost:8000`，请确保后端服务已启动。

## 环境变量

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```
