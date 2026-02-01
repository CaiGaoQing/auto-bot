"""财务助手技能"""

from pathlib import Path
from typing import Any, Optional
import json

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class FinanceSkill(Skill):
    """财务助手技能
    
    提供 Excel 处理、数据分析、报表生成等功能。
    """
    
    @property
    def name(self) -> str:
        return "finance"
    
    @property
    def display_name(self) -> str:
        return "财务助手"
    
    @property
    def description(self) -> str:
        return "Excel 处理、工资表整理、数据分析、财务报表生成"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="read_excel",
                description="读取 Excel 文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Excel 文件路径",
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "工作表名称，默认第一个",
                        },
                        "max_rows": {
                            "type": "integer",
                            "description": "最大读取行数",
                            "default": 100,
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.read_excel,
            ),
            ToolDefinition(
                name="write_excel",
                description="写入数据到 Excel 文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                        "data": {
                            "type": "array",
                            "description": "数据列表 (每行是一个字典)",
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "工作表名称",
                            "default": "Sheet1",
                        },
                    },
                    "required": ["file_path", "data"],
                },
                handler=self.write_excel,
            ),
            ToolDefinition(
                name="analyze_data",
                description="分析数据并生成统计报告",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "数据文件路径 (Excel/CSV)",
                        },
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要分析的列名",
                        },
                        "group_by": {
                            "type": "string",
                            "description": "分组列名",
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.analyze_data,
            ),
            ToolDefinition(
                name="organize_salary",
                description="整理工资表，进行分类汇总",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "工资表文件路径",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                        },
                        "group_by": {
                            "type": "string",
                            "description": "分组字段 (如部门)",
                            "default": "部门",
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.organize_salary,
            ),
            ToolDefinition(
                name="generate_report",
                description="生成财务报表",
                parameters={
                    "type": "object",
                    "properties": {
                        "data_path": {
                            "type": "string",
                            "description": "数据文件路径",
                        },
                        "report_type": {
                            "type": "string",
                            "enum": ["summary", "detail", "chart"],
                            "description": "报表类型",
                            "default": "summary",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出路径",
                        },
                    },
                    "required": ["data_path"],
                },
                handler=self.generate_report,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的财务助手，擅长：
- Excel 数据处理和分析
- 工资表整理和汇总
- 财务报表生成
- 数据可视化

请确保：
1. 数据处理准确无误
2. 保护敏感财务信息
3. 输出格式规范专业
4. 提供清晰的数据分析"""
    
    async def read_excel(
        self,
        ctx: ToolContext,
        file_path: str,
        sheet_name: Optional[str] = None,
        max_rows: int = 100,
    ) -> ToolResult:
        """读取 Excel 文件"""
        try:
            import pandas as pd
        except ImportError:
            return ToolResult.error_result("需要安装 pandas: pip install pandas openpyxl")
        
        path = Path(file_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {file_path}")
        
        try:
            # 读取 Excel
            if sheet_name:
                df = pd.read_excel(path, sheet_name=sheet_name, nrows=max_rows)
            else:
                df = pd.read_excel(path, nrows=max_rows)
            
            # 转换为字典列表
            data = df.head(max_rows).to_dict(orient="records")
            
            # 获取基本信息
            info = {
                "total_rows": len(df),
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            }
            
            return ToolResult.success_result(
                data={
                    "info": info,
                    "preview": data[:10],  # 只返回前10行预览
                    "data": data,
                },
                message=f"读取成功: {len(data)} 行, {len(df.columns)} 列",
            )
        except Exception as e:
            return ToolResult.error_result(f"读取失败: {str(e)}")
    
    async def write_excel(
        self,
        ctx: ToolContext,
        file_path: str,
        data: list[dict],
        sheet_name: str = "Sheet1",
    ) -> ToolResult:
        """写入 Excel 文件"""
        try:
            import pandas as pd
        except ImportError:
            return ToolResult.error_result("需要安装 pandas: pip install pandas openpyxl")
        
        path = Path(file_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建 DataFrame 并写入
            df = pd.DataFrame(data)
            df.to_excel(path, sheet_name=sheet_name, index=False)
            
            return ToolResult.file(
                path=str(path),
                message=f"Excel 已保存: {len(data)} 行",
            )
        except Exception as e:
            return ToolResult.error_result(f"写入失败: {str(e)}")
    
    async def analyze_data(
        self,
        ctx: ToolContext,
        file_path: str,
        columns: Optional[list[str]] = None,
        group_by: Optional[str] = None,
    ) -> ToolResult:
        """分析数据"""
        try:
            import pandas as pd
        except ImportError:
            return ToolResult.error_result("需要安装 pandas")
        
        path = Path(file_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {file_path}")
        
        try:
            # 读取数据
            if path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(path)
            else:
                df = pd.read_csv(path)
            
            # 选择列
            if columns:
                df = df[columns]
            
            # 基础统计
            stats = {
                "shape": {"rows": len(df), "columns": len(df.columns)},
                "columns": list(df.columns),
            }
            
            # 数值列统计
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                stats["numeric_summary"] = df[numeric_cols].describe().to_dict()
            
            # 分组统计
            if group_by and group_by in df.columns:
                grouped = df.groupby(group_by)
                stats["group_counts"] = grouped.size().to_dict()
                
                # 数值列的分组汇总
                if len(numeric_cols) > 0:
                    stats["group_summary"] = grouped[numeric_cols].sum().to_dict()
            
            return ToolResult.success_result(
                data=stats,
                message=f"分析完成: {len(df)} 行数据",
            )
        except Exception as e:
            return ToolResult.error_result(f"分析失败: {str(e)}")
    
    async def organize_salary(
        self,
        ctx: ToolContext,
        file_path: str,
        output_path: Optional[str] = None,
        group_by: str = "部门",
    ) -> ToolResult:
        """整理工资表"""
        try:
            import pandas as pd
        except ImportError:
            return ToolResult.error_result("需要安装 pandas")
        
        path = Path(file_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {file_path}")
        
        try:
            # 读取工资表
            df = pd.read_excel(path)
            
            # 识别工资相关列
            salary_cols = [col for col in df.columns if any(
                keyword in col for keyword in ["工资", "薪资", "金额", "奖金", "补贴", "扣款", "实发"]
            )]
            
            if not salary_cols:
                # 尝试识别数值列
                salary_cols = list(df.select_dtypes(include=["number"]).columns)
            
            result = {
                "original": {
                    "rows": len(df),
                    "columns": list(df.columns),
                },
                "salary_columns": salary_cols,
            }
            
            # 按部门分组汇总
            if group_by in df.columns:
                grouped = df.groupby(group_by)
                
                # 人数统计
                result["headcount"] = grouped.size().to_dict()
                
                # 工资汇总
                if salary_cols:
                    summary = grouped[salary_cols].agg(["sum", "mean", "min", "max"])
                    result["salary_summary"] = {}
                    
                    for dept in grouped.groups.keys():
                        dept_data = summary.loc[dept]
                        result["salary_summary"][dept] = {
                            col: {
                                "sum": float(dept_data[(col, "sum")]),
                                "avg": float(dept_data[(col, "mean")]),
                                "min": float(dept_data[(col, "min")]),
                                "max": float(dept_data[(col, "max")]),
                            }
                            for col in salary_cols
                        }
                
                # 总计
                if salary_cols:
                    result["total"] = {
                        col: {
                            "sum": float(df[col].sum()),
                            "avg": float(df[col].mean()),
                        }
                        for col in salary_cols
                    }
            
            # 输出到新文件
            if output_path:
                out_path = Path(output_path).expanduser()
                if ctx.security.is_allowed_path(out_path):
                    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                        # 原始数据
                        df.to_excel(writer, sheet_name="原始数据", index=False)
                        
                        # 汇总表
                        if group_by in df.columns and salary_cols:
                            summary_df = grouped[salary_cols].sum()
                            summary_df["人数"] = grouped.size()
                            summary_df.to_excel(writer, sheet_name="部门汇总")
                    
                    result["output_file"] = str(out_path)
            
            return ToolResult.success_result(
                data=result,
                message=f"整理完成: {len(df)} 条记录",
            )
        except Exception as e:
            return ToolResult.error_result(f"整理失败: {str(e)}")
    
    async def generate_report(
        self,
        ctx: ToolContext,
        data_path: str,
        report_type: str = "summary",
        output_path: Optional[str] = None,
    ) -> ToolResult:
        """生成财务报表"""
        try:
            import pandas as pd
        except ImportError:
            return ToolResult.error_result("需要安装 pandas")
        
        path = Path(data_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {data_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {data_path}")
        
        try:
            # 读取数据
            if path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(path)
            else:
                df = pd.read_csv(path)
            
            report = {
                "type": report_type,
                "data_source": str(path),
                "generated_at": pd.Timestamp.now().isoformat(),
            }
            
            numeric_cols = df.select_dtypes(include=["number"]).columns
            
            if report_type == "summary":
                # 汇总报表
                report["summary"] = {
                    "total_records": len(df),
                    "columns": list(df.columns),
                }
                
                if len(numeric_cols) > 0:
                    report["summary"]["totals"] = {
                        col: float(df[col].sum()) for col in numeric_cols
                    }
                    report["summary"]["averages"] = {
                        col: float(df[col].mean()) for col in numeric_cols
                    }
            
            elif report_type == "detail":
                # 明细报表
                report["detail"] = df.to_dict(orient="records")
            
            elif report_type == "chart":
                # 图表数据
                report["chart_data"] = {
                    "labels": list(df.index) if len(df) <= 20 else list(range(len(df))),
                    "datasets": [
                        {"label": col, "data": df[col].tolist()}
                        for col in numeric_cols[:5]  # 最多5个数据集
                    ],
                }
            
            # 输出报表文件
            if output_path:
                out_path = Path(output_path).expanduser()
                if ctx.security.is_allowed_path(out_path):
                    if out_path.suffix == ".xlsx":
                        df.to_excel(out_path, index=False)
                    elif out_path.suffix == ".json":
                        with open(out_path, "w", encoding="utf-8") as f:
                            json.dump(report, f, ensure_ascii=False, indent=2)
                    else:
                        df.to_csv(out_path, index=False)
                    
                    report["output_file"] = str(out_path)
            
            return ToolResult.success_result(
                data=report,
                message=f"报表生成完成: {report_type}",
            )
        except Exception as e:
            return ToolResult.error_result(f"报表生成失败: {str(e)}")
