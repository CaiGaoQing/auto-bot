/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // 增加代理超时时间
  experimental: {
    proxyTimeout: 120000, // 2 分钟
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
