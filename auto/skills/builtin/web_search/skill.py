"""网络搜索技能"""

from typing import Optional
from urllib.parse import quote_plus

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class WebSearchSkill(Skill):
    """网络搜索技能
    
    提供网页搜索、网页抓取、信息提取等功能。
    """
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def display_name(self) -> str:
        return "网络搜索"
    
    @property
    def description(self) -> str:
        return "网页搜索、网页抓取、信息提取"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="search",
                description="搜索网络 (使用 DuckDuckGo)",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 10,
                        },
                        "region": {
                            "type": "string",
                            "description": "地区 (cn-zh, wt-wt)",
                            "default": "cn-zh",
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search,
            ),
            ToolDefinition(
                name="fetch_page",
                description="获取网页内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "网页 URL",
                        },
                        "extract_text": {
                            "type": "boolean",
                            "description": "仅提取文本内容",
                            "default": True,
                        },
                    },
                    "required": ["url"],
                },
                handler=self.fetch_page,
            ),
            ToolDefinition(
                name="extract_links",
                description="提取网页中的链接",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "网页 URL",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "链接过滤模式 (正则表达式)",
                        },
                    },
                    "required": ["url"],
                },
                handler=self.extract_links,
            ),
            ToolDefinition(
                name="search_news",
                description="搜索新闻",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search_news,
            ),
            ToolDefinition(
                name="search_images",
                description="搜索图片",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search_images,
            ),
            ToolDefinition(
                name="summarize_url",
                description="获取并总结网页内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "网页 URL",
                        },
                    },
                    "required": ["url"],
                },
                handler=self.summarize_url,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个网络搜索助手，可以帮助用户：
- 搜索互联网信息
- 获取网页内容
- 提取和总结关键信息
- 进行竞品调研和市场分析

使用原则：
1. 验证信息来源的可靠性
2. 多来源交叉验证
3. 注明信息出处
4. 区分事实和观点"""
    
    async def search(
        self,
        ctx: ToolContext,
        query: str,
        max_results: int = 10,
        region: str = "cn-zh",
    ) -> ToolResult:
        """搜索网络"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return await self._search_fallback(query, max_results)
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    region=region,
                    max_results=max_results,
                ))
            
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            
            return ToolResult.table(
                data=formatted,
                message=f"搜索 '{query}' 找到 {len(formatted)} 条结果",
            )
        except Exception as e:
            return await self._search_fallback(query, max_results)
    
    async def _search_fallback(
        self,
        query: str,
        max_results: int,
    ) -> ToolResult:
        """备用搜索方法"""
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            return ToolResult.error_result(
                "需要安装依赖: pip install duckduckgo-search 或 pip install httpx beautifulsoup4"
            )
        
        try:
            # 使用 DuckDuckGo HTML 搜索
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10,
                )
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            for result in soup.select(".result")[:max_results]:
                title_elem = result.select_one(".result__title")
                snippet_elem = result.select_one(".result__snippet")
                link_elem = result.select_one(".result__url")
                
                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": link_elem.get_text(strip=True) if link_elem else "",
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                    })
            
            return ToolResult.table(
                data=results,
                message=f"搜索 '{query}' 找到 {len(results)} 条结果",
            )
        except Exception as e:
            return ToolResult.error_result(f"搜索失败: {str(e)}")
    
    async def fetch_page(
        self,
        ctx: ToolContext,
        url: str,
        extract_text: bool = True,
    ) -> ToolResult:
        """获取网页内容"""
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            return ToolResult.error_result(
                "需要安装: pip install httpx beautifulsoup4"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15,
                    follow_redirects=True,
                )
            
            if response.status_code != 200:
                return ToolResult.error_result(
                    f"请求失败: HTTP {response.status_code}"
                )
            
            content_type = response.headers.get("content-type", "")
            
            if "text/html" not in content_type and "application/json" not in content_type:
                return ToolResult.error_result(
                    f"不支持的内容类型: {content_type}"
                )
            
            if extract_text:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 移除脚本和样式
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # 提取文本
                text = soup.get_text(separator="\n", strip=True)
                
                # 清理多余空行
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                text = "\n".join(lines)
                
                # 限制长度
                if len(text) > 10000:
                    text = text[:10000] + "\n... (内容已截断)"
                
                return ToolResult.success_result(
                    data={
                        "url": url,
                        "title": soup.title.string if soup.title else "",
                        "content": text,
                        "length": len(text),
                    },
                    message=f"获取到 {len(text)} 字符",
                )
            else:
                return ToolResult.success_result(
                    data={
                        "url": url,
                        "html": response.text[:50000],
                        "length": len(response.text),
                    },
                    message=f"获取到 HTML {len(response.text)} 字符",
                )
        except Exception as e:
            return ToolResult.error_result(f"获取网页失败: {str(e)}")
    
    async def extract_links(
        self,
        ctx: ToolContext,
        url: str,
        pattern: Optional[str] = None,
    ) -> ToolResult:
        """提取网页链接"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            import re
        except ImportError:
            return ToolResult.error_result(
                "需要安装: pip install httpx beautifulsoup4"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10,
                )
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # 转换为绝对 URL
                full_url = urljoin(url, href)
                
                # 过滤
                if pattern:
                    if not re.search(pattern, full_url):
                        continue
                
                text = a.get_text(strip=True)
                
                links.append({
                    "text": text[:100],
                    "url": full_url,
                })
            
            # 去重
            seen = set()
            unique_links = []
            for link in links:
                if link["url"] not in seen:
                    seen.add(link["url"])
                    unique_links.append(link)
            
            return ToolResult.table(
                data=unique_links[:50],
                message=f"提取到 {len(unique_links)} 个链接",
            )
        except Exception as e:
            return ToolResult.error_result(f"提取链接失败: {str(e)}")
    
    async def search_news(
        self,
        ctx: ToolContext,
        query: str,
        max_results: int = 10,
    ) -> ToolResult:
        """搜索新闻"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ToolResult.error_result(
                "需要安装: pip install duckduckgo-search"
            )
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    query,
                    max_results=max_results,
                ))
            
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                    "snippet": r.get("body", "")[:200],
                })
            
            return ToolResult.table(
                data=formatted,
                message=f"找到 {len(formatted)} 条新闻",
            )
        except Exception as e:
            return ToolResult.error_result(f"搜索新闻失败: {str(e)}")
    
    async def search_images(
        self,
        ctx: ToolContext,
        query: str,
        max_results: int = 10,
    ) -> ToolResult:
        """搜索图片"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ToolResult.error_result(
                "需要安装: pip install duckduckgo-search"
            )
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    query,
                    max_results=max_results,
                ))
            
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "image_url": r.get("image", ""),
                    "thumbnail": r.get("thumbnail", ""),
                    "source": r.get("source", ""),
                    "width": r.get("width", 0),
                    "height": r.get("height", 0),
                })
            
            return ToolResult.table(
                data=formatted,
                message=f"找到 {len(formatted)} 张图片",
            )
        except Exception as e:
            return ToolResult.error_result(f"搜索图片失败: {str(e)}")
    
    async def summarize_url(
        self,
        ctx: ToolContext,
        url: str,
    ) -> ToolResult:
        """获取并总结网页"""
        # 先获取网页内容
        page_result = await self.fetch_page(ctx, url, extract_text=True)
        
        if not page_result.success:
            return page_result
        
        content = page_result.data.get("content", "")
        title = page_result.data.get("title", "")
        
        # 返回内容，让 AI 进行总结
        return ToolResult.success_result(
            data={
                "url": url,
                "title": title,
                "content": content[:8000],  # 限制长度
                "suggestion": "请基于以上内容进行总结",
            },
            message=f"已获取 '{title}' 的内容，请进行总结",
        )
