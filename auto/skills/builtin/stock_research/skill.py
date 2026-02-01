"""A股调研技能"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class StockResearchSkill(Skill):
    """A股调研技能
    
    提供股票数据查询、财报分析、行业研究等功能。
    """
    
    @property
    def name(self) -> str:
        return "stock_research"
    
    @property
    def display_name(self) -> str:
        return "A股调研"
    
    @property
    def description(self) -> str:
        return "A股数据查询、财报分析、行业研究、技术分析"
    
    @property
    def category(self) -> str:
        return "finance"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="get_realtime_quote",
                description="获取股票实时行情",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码 (如 000001, 600519)",
                        },
                    },
                    "required": ["symbol"],
                },
                handler=self.get_realtime_quote,
            ),
            ToolDefinition(
                name="get_history",
                description="获取股票历史行情",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码",
                        },
                        "period": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"],
                            "description": "周期",
                            "default": "daily",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "开始日期 (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期 (YYYY-MM-DD)",
                        },
                    },
                    "required": ["symbol"],
                },
                handler=self.get_history,
            ),
            ToolDefinition(
                name="get_stock_info",
                description="获取股票基本信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码",
                        },
                    },
                    "required": ["symbol"],
                },
                handler=self.get_stock_info,
            ),
            ToolDefinition(
                name="get_financial_report",
                description="获取财务报表数据",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码",
                        },
                        "report_type": {
                            "type": "string",
                            "enum": ["income", "balance", "cashflow"],
                            "description": "报表类型: income(利润表), balance(资产负债表), cashflow(现金流量表)",
                            "default": "income",
                        },
                    },
                    "required": ["symbol"],
                },
                handler=self.get_financial_report,
            ),
            ToolDefinition(
                name="get_sector_stocks",
                description="获取板块成分股",
                parameters={
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "板块名称 (如 半导体, 新能源, 白酒)",
                        },
                    },
                    "required": ["sector"],
                },
                handler=self.get_sector_stocks,
            ),
            ToolDefinition(
                name="search_stocks",
                description="搜索股票",
                parameters={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词 (股票名称或代码)",
                        },
                    },
                    "required": ["keyword"],
                },
                handler=self.search_stocks,
            ),
            ToolDefinition(
                name="generate_stock_report",
                description="生成个股研究报告",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["symbol"],
                },
                handler=self.generate_stock_report,
            ),
            ToolDefinition(
                name="get_market_overview",
                description="获取市场概况 (指数、涨跌统计)",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.get_market_overview,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的A股市场分析师，擅长：
- 个股基本面分析（财务报表、估值）
- 技术面分析（K线、均线、成交量）
- 行业研究和板块分析
- 投资策略建议

注意事项：
- 所有分析仅供参考，不构成投资建议
- 投资有风险，入市需谨慎
- 数据来源于公开市场，可能存在延迟"""
    
    def _ensure_akshare(self):
        """确保 akshare 已安装"""
        try:
            import akshare
            return akshare
        except ImportError:
            raise ImportError("需要安装 akshare: pip install akshare")
    
    async def get_realtime_quote(
        self,
        ctx: ToolContext,
        symbol: str,
    ) -> ToolResult:
        """获取实时行情"""
        try:
            ak = self._ensure_akshare()
        except ImportError as e:
            return ToolResult.error_result(str(e))
        
        try:
            # 标准化股票代码
            symbol = symbol.strip().replace(".", "")
            
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            
            # 查找匹配的股票
            row = df[df["代码"] == symbol]
            if row.empty:
                # 尝试用名称搜索
                row = df[df["名称"].str.contains(symbol)]
            
            if row.empty:
                return ToolResult.error_result(f"未找到股票: {symbol}")
            
            stock = row.iloc[0].to_dict()
            
            # 格式化数据
            quote = {
                "symbol": stock.get("代码", ""),
                "name": stock.get("名称", ""),
                "price": float(stock.get("最新价", 0)),
                "change": float(stock.get("涨跌额", 0)),
                "change_pct": float(stock.get("涨跌幅", 0)),
                "open": float(stock.get("今开", 0)),
                "high": float(stock.get("最高", 0)),
                "low": float(stock.get("最低", 0)),
                "volume": float(stock.get("成交量", 0)),
                "amount": float(stock.get("成交额", 0)),
                "turnover": float(stock.get("换手率", 0)),
                "pe": float(stock.get("市盈率-动态", 0)) if stock.get("市盈率-动态") else None,
                "pb": float(stock.get("市净率", 0)) if stock.get("市净率") else None,
                "market_cap": float(stock.get("总市值", 0)),
            }
            
            return ToolResult.success_result(
                data=quote,
                message=f"{quote['name']}({quote['symbol']}) 当前价格: {quote['price']} 涨跌幅: {quote['change_pct']}%",
            )
        except Exception as e:
            return ToolResult.error_result(f"获取行情失败: {str(e)}")
    
    async def get_history(
        self,
        ctx: ToolContext,
        symbol: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ToolResult:
        """获取历史行情"""
        try:
            ak = self._ensure_akshare()
        except ImportError as e:
            return ToolResult.error_result(str(e))
        
        try:
            symbol = symbol.strip()
            
            # 默认日期范围
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            else:
                end_date = end_date.replace("-", "")
            
            if not start_date:
                start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
            else:
                start_date = start_date.replace("-", "")
            
            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",  # 前复权
            )
            
            if df.empty:
                return ToolResult.error_result(f"未找到历史数据: {symbol}")
            
            # 转换为列表
            data = df.to_dict(orient="records")
            
            # 计算统计信息
            stats = {
                "period": period,
                "start": start_date,
                "end": end_date,
                "count": len(data),
                "high": float(df["最高"].max()),
                "low": float(df["最低"].min()),
                "avg_volume": float(df["成交量"].mean()),
            }
            
            return ToolResult.success_result(
                data={
                    "history": data[-30:],  # 只返回最近30条
                    "stats": stats,
                },
                message=f"获取到 {len(data)} 条历史数据",
            )
        except Exception as e:
            return ToolResult.error_result(f"获取历史数据失败: {str(e)}")
    
    async def get_stock_info(
        self,
        ctx: ToolContext,
        symbol: str,
    ) -> ToolResult:
        """获取股票基本信息"""
        try:
            ak = self._ensure_akshare()
        except ImportError as e:
            return ToolResult.error_result(str(e))
        
        try:
            symbol = symbol.strip()
            
            # 获取个股信息
            df = ak.stock_individual_info_em(symbol=symbol)
            
            if df.empty:
                return ToolResult.error_result(f"未找到股票信息: {symbol}")
            
            # 转换为字典
            info = {}
            for _, row in df.iterrows():
                key = row["item"]
                value = row["value"]
                info[key] = value
            
            return ToolResult.success_result(
                data=info,
                message=f"获取到 {symbol} 的基本信息",
            )
        except Exception as e:
            return ToolResult.error_result(f"获取股票信息失败: {str(e)}")
    
    async def get_financial_report(
        self,
        ctx: ToolContext,
        symbol: str,
        report_type: str = "income",
    ) -> ToolResult:
        """获取财务报表"""
        try:
            ak = self._ensure_akshare()
        except ImportError as e:
            return ToolResult.error_result(str(e))
        
        try:
            symbol = symbol.strip()
            
            # 根据类型获取对应报表
            if report_type == "income":
                df = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
            elif report_type == "balance":
                df = ak.stock_financial_report_sina(stock=symbol, symbol="资产负债表")
            elif report_type == "cashflow":
                df = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
            else:
                return ToolResult.error_result(f"不支持的报表类型: {report_type}")
            
            if df.empty:
                return ToolResult.error_result(f"未找到财务数据: {symbol}")
            
            # 取最近4个季度
            data = df.head(4).to_dict(orient="records")
            
            return ToolResult.success_result(
                data={
                    "report_type": report_type,
                    "symbol": symbol,
                    "reports": data,
                },
                message=f"获取到 {symbol} 的{report_type}报表",
            )
        except Exception as e:
            return ToolResult.error_result(f"获取财务报表失败: {str(e)}")
    
    async def get_sector_stocks(
        self,
        ctx: ToolContext,
        sector: str,
    ) -> ToolResult:
        """获取板块成分股"""
        try:
            ak = self._ensure_akshare()
        except ImportError as e:
            return ToolResult.error_result(str(e))
        
        try:
            # 获取板块列表
            sectors_df = ak.stock_board_industry_name_em()
            
            # 查找匹配的板块
            matched = sectors_df[sectors_df["板块名称"].str.contains(sector)]
            
            if matched.empty:
                return ToolResult.success_result(
                    data={
                        "available_sectors": sectors_df["板块名称"].tolist()[:20],
                    },
                    message=f"未找到板块 '{sector}'，请参考可用板块列表",
                )
            
            sector_name = matched.iloc[0]["板块名称"]
            
            # 获取成分股
            stocks_df = ak.stock_board_industry_cons_em(symbol=sector_name)
            
            stocks = stocks_df.head(20).to_dict(orient="records")
            
            return ToolResult.success_result(
                data={
                    "sector": sector_name,
                    "stocks": stocks,
                    "total": len(stocks_df),
                },
                message=f"板块 {sector_name} 共有 {len(stocks_df)} 只成分股",
            )
        except Exception as e:
            return ToolResult.error_result(f"获取板块成分股失败: {str(e)}")
    
    async def search_stocks(
        self,
        ctx: ToolContext,
        keyword: str,
    ) -> ToolResult:
        """搜索股票"""
        try:
            ak = self._ensure_akshare()
        except ImportError as e:
            return ToolResult.error_result(str(e))
        
        try:
            # 获取所有股票
            df = ak.stock_zh_a_spot_em()
            
            # 搜索匹配
            keyword = keyword.strip()
            matches = df[
                df["代码"].str.contains(keyword) | 
                df["名称"].str.contains(keyword)
            ]
            
            if matches.empty:
                return ToolResult.success_result(
                    data={"results": []},
                    message=f"未找到匹配 '{keyword}' 的股票",
                )
            
            results = []
            for _, row in matches.head(10).iterrows():
                results.append({
                    "symbol": row["代码"],
                    "name": row["名称"],
                    "price": float(row["最新价"]) if row["最新价"] else 0,
                    "change_pct": float(row["涨跌幅"]) if row["涨跌幅"] else 0,
                })
            
            return ToolResult.table(
                data=results,
                message=f"找到 {len(matches)} 只匹配的股票",
            )
        except Exception as e:
            return ToolResult.error_result(f"搜索失败: {str(e)}")
    
    async def generate_stock_report(
        self,
        ctx: ToolContext,
        symbol: str,
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成个股研究报告"""
        try:
            # 获取各类数据
            quote_result = await self.get_realtime_quote(ctx, symbol)
            if not quote_result.success:
                return quote_result
            
            info_result = await self.get_stock_info(ctx, symbol)
            history_result = await self.get_history(ctx, symbol)
            
            quote = quote_result.data
            info = info_result.data if info_result.success else {}
            history = history_result.data if history_result.success else {}
            
            # 生成报告内容
            report = {
                "title": f"{quote['name']}({quote['symbol']}) 个股研究报告",
                "generated_at": datetime.now().isoformat(),
                "basic_info": {
                    "name": quote["name"],
                    "symbol": quote["symbol"],
                    "industry": info.get("所处行业", ""),
                    "listed_date": info.get("上市时间", ""),
                },
                "market_data": {
                    "price": quote["price"],
                    "change_pct": quote["change_pct"],
                    "market_cap": quote["market_cap"],
                    "pe": quote["pe"],
                    "pb": quote["pb"],
                    "turnover": quote["turnover"],
                },
                "history_stats": history.get("stats", {}),
                "disclaimer": "本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。",
            }
            
            # 输出到文件
            if output_path:
                import json
                path = Path(output_path).expanduser()
                
                if ctx.security.is_allowed_path(path):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if path.suffix == ".json":
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(report, f, ensure_ascii=False, indent=2)
                    else:
                        # Markdown 格式
                        md_content = f"""# {report['title']}

生成时间: {report['generated_at']}

## 基本信息

- 股票名称: {report['basic_info']['name']}
- 股票代码: {report['basic_info']['symbol']}
- 所属行业: {report['basic_info'].get('industry', 'N/A')}

## 市场数据

| 指标 | 数值 |
|------|------|
| 最新价 | {report['market_data']['price']} |
| 涨跌幅 | {report['market_data']['change_pct']}% |
| 总市值 | {report['market_data']['market_cap']:,.0f} |
| 市盈率 | {report['market_data']['pe']} |
| 市净率 | {report['market_data']['pb']} |
| 换手率 | {report['market_data']['turnover']}% |

## 历史统计

- 统计周期: {report['history_stats'].get('start', '')} ~ {report['history_stats'].get('end', '')}
- 最高价: {report['history_stats'].get('high', 'N/A')}
- 最低价: {report['history_stats'].get('low', 'N/A')}

---

> {report['disclaimer']}
"""
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(md_content)
                    
                    report["output_file"] = str(path)
            
            return ToolResult.success_result(
                data=report,
                message=f"已生成 {quote['name']} 的研究报告",
            )
        except Exception as e:
            return ToolResult.error_result(f"生成报告失败: {str(e)}")
    
    async def get_market_overview(
        self,
        ctx: ToolContext,
    ) -> ToolResult:
        """获取市场概况"""
        try:
            ak = self._ensure_akshare()
        except ImportError as e:
            return ToolResult.error_result(str(e))
        
        try:
            # 获取主要指数
            index_df = ak.stock_zh_index_spot_em()
            
            main_indices = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300"]
            indices = []
            
            for idx_name in main_indices:
                row = index_df[index_df["名称"] == idx_name]
                if not row.empty:
                    data = row.iloc[0]
                    indices.append({
                        "name": idx_name,
                        "price": float(data["最新价"]),
                        "change_pct": float(data["涨跌幅"]),
                    })
            
            # 获取涨跌统计
            stocks_df = ak.stock_zh_a_spot_em()
            
            rise_count = len(stocks_df[stocks_df["涨跌幅"] > 0])
            fall_count = len(stocks_df[stocks_df["涨跌幅"] < 0])
            flat_count = len(stocks_df[stocks_df["涨跌幅"] == 0])
            limit_up = len(stocks_df[stocks_df["涨跌幅"] >= 9.9])
            limit_down = len(stocks_df[stocks_df["涨跌幅"] <= -9.9])
            
            overview = {
                "indices": indices,
                "market_stats": {
                    "total": len(stocks_df),
                    "rise": rise_count,
                    "fall": fall_count,
                    "flat": flat_count,
                    "limit_up": limit_up,
                    "limit_down": limit_down,
                },
                "timestamp": datetime.now().isoformat(),
            }
            
            return ToolResult.success_result(
                data=overview,
                message=f"涨: {rise_count}, 跌: {fall_count}, 涨停: {limit_up}, 跌停: {limit_down}",
            )
        except Exception as e:
            return ToolResult.error_result(f"获取市场概况失败: {str(e)}")
