"""RPA 自动化技能

实现屏幕自动化操作，包括截图、OCR、鼠标键盘控制等。
"""

import asyncio
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class RPASkill(Skill):
    """RPA 自动化技能
    
    提供桌面自动化能力：截图、OCR 识别、鼠标键盘控制。
    """
    
    @property
    def name(self) -> str:
        return "rpa"
    
    @property
    def display_name(self) -> str:
        return "RPA 自动化"
    
    @property
    def description(self) -> str:
        return "屏幕截图、OCR 识别、鼠标键盘自动化"
    
    @property
    def category(self) -> str:
        return "automation"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="screenshot",
                description="截取屏幕或窗口截图",
                parameters={
                    "type": "object",
                    "properties": {
                        "output_path": {
                            "type": "string",
                            "description": "截图保存路径",
                        },
                        "region": {
                            "type": "object",
                            "description": "截取区域 {x, y, width, height}",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"},
                                "width": {"type": "integer"},
                                "height": {"type": "integer"},
                            },
                        },
                        "window_title": {
                            "type": "string",
                            "description": "窗口标题 (截取特定窗口)",
                        },
                    },
                },
                handler=self.screenshot,
            ),
            ToolDefinition(
                name="ocr_image",
                description="对图片进行 OCR 文字识别",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "图片路径",
                        },
                        "language": {
                            "type": "string",
                            "description": "语言 (chi_sim, eng)",
                            "default": "chi_sim+eng",
                        },
                    },
                    "required": ["image_path"],
                },
                handler=self.ocr_image,
            ),
            ToolDefinition(
                name="ocr_screen",
                description="截屏并进行 OCR 识别",
                parameters={
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "object",
                            "description": "截取区域",
                        },
                    },
                },
                handler=self.ocr_screen,
            ),
            ToolDefinition(
                name="find_element",
                description="在屏幕上查找图片元素位置",
                parameters={
                    "type": "object",
                    "properties": {
                        "template_path": {
                            "type": "string",
                            "description": "模板图片路径",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "匹配置信度 (0-1)",
                            "default": 0.8,
                        },
                    },
                    "required": ["template_path"],
                },
                handler=self.find_element,
            ),
            ToolDefinition(
                name="click",
                description="点击屏幕坐标或元素",
                dangerous=True,
                requires_confirmation=True,
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "integer",
                            "description": "X 坐标",
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y 坐标",
                        },
                        "button": {
                            "type": "string",
                            "enum": ["left", "right", "middle"],
                            "default": "left",
                        },
                        "clicks": {
                            "type": "integer",
                            "description": "点击次数",
                            "default": 1,
                        },
                    },
                    "required": ["x", "y"],
                },
                handler=self.click,
            ),
            ToolDefinition(
                name="type_text",
                description="输入文本",
                dangerous=True,
                requires_confirmation=True,
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要输入的文本",
                        },
                        "interval": {
                            "type": "number",
                            "description": "按键间隔 (秒)",
                            "default": 0.05,
                        },
                    },
                    "required": ["text"],
                },
                handler=self.type_text,
            ),
            ToolDefinition(
                name="hotkey",
                description="按下快捷键组合",
                dangerous=True,
                requires_confirmation=True,
                parameters={
                    "type": "object",
                    "properties": {
                        "keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "按键列表 (如 ['ctrl', 'c'])",
                        },
                    },
                    "required": ["keys"],
                },
                handler=self.hotkey,
            ),
            ToolDefinition(
                name="move_mouse",
                description="移动鼠标到指定位置",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X 坐标"},
                        "y": {"type": "integer", "description": "Y 坐标"},
                        "duration": {
                            "type": "number",
                            "description": "移动时长 (秒)",
                            "default": 0.2,
                        },
                    },
                    "required": ["x", "y"],
                },
                handler=self.move_mouse,
            ),
            ToolDefinition(
                name="scroll",
                description="滚动鼠标滚轮",
                parameters={
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "integer",
                            "description": "滚动量 (正数向上，负数向下)",
                        },
                        "x": {"type": "integer", "description": "X 坐标"},
                        "y": {"type": "integer", "description": "Y 坐标"},
                    },
                    "required": ["amount"],
                },
                handler=self.scroll,
            ),
            ToolDefinition(
                name="get_screen_size",
                description="获取屏幕尺寸",
                parameters={"type": "object", "properties": {}},
                handler=self.get_screen_size,
            ),
            ToolDefinition(
                name="list_windows",
                description="列出所有窗口",
                parameters={"type": "object", "properties": {}},
                handler=self.list_windows,
            ),
            ToolDefinition(
                name="activate_window",
                description="激活指定窗口",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "窗口标题 (支持模糊匹配)",
                        },
                    },
                    "required": ["title"],
                },
                handler=self.activate_window,
            ),
            ToolDefinition(
                name="wait_for_element",
                description="等待元素出现",
                parameters={
                    "type": "object",
                    "properties": {
                        "template_path": {
                            "type": "string",
                            "description": "模板图片路径",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间 (秒)",
                            "default": 30,
                        },
                    },
                    "required": ["template_path"],
                },
                handler=self.wait_for_element,
            ),
            ToolDefinition(
                name="click_element",
                description="查找并点击元素",
                dangerous=True,
                requires_confirmation=True,
                parameters={
                    "type": "object",
                    "properties": {
                        "template_path": {
                            "type": "string",
                            "description": "模板图片路径",
                        },
                        "confidence": {
                            "type": "number",
                            "default": 0.8,
                        },
                    },
                    "required": ["template_path"],
                },
                handler=self.click_element,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个 RPA 自动化助手，可以控制桌面进行自动化操作：
- 截图和 OCR 文字识别
- 查找屏幕上的元素
- 鼠标点击、移动、滚动
- 键盘输入和快捷键

安全注意事项：
1. 鼠标键盘操作是危险操作，需要确认
2. 操作前先截图确认当前状态
3. 操作后验证结果"""
    
    def _check_pyautogui(self):
        """检查 pyautogui 是否可用"""
        try:
            import pyautogui
            return pyautogui
        except ImportError:
            return None
    
    async def screenshot(
        self,
        ctx: ToolContext,
        output_path: Optional[str] = None,
        region: Optional[dict] = None,
        window_title: Optional[str] = None,
    ) -> ToolResult:
        """截取屏幕"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui pillow")
        
        try:
            if region:
                img = pyautogui.screenshot(
                    region=(region["x"], region["y"], region["width"], region["height"])
                )
            else:
                img = pyautogui.screenshot()
            
            if output_path:
                path = Path(output_path).expanduser()
                if ctx.security.is_allowed_path(path):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    img.save(str(path))
                    return ToolResult.file(
                        path=str(path),
                        message=f"截图已保存 ({img.width}x{img.height})",
                    )
            
            # 返回 base64
            import io
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return ToolResult.success_result(
                data={
                    "width": img.width,
                    "height": img.height,
                    "image_base64": img_base64[:100] + "...",  # 截断显示
                },
                message=f"截图完成 ({img.width}x{img.height})",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"截图失败: {str(e)}")
    
    async def ocr_image(
        self,
        ctx: ToolContext,
        image_path: str,
        language: str = "chi_sim+eng",
    ) -> ToolResult:
        """OCR 识别图片"""
        path = Path(image_path).expanduser()
        
        if not path.exists():
            return ToolResult.error_result(f"图片不存在: {image_path}")
        
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return ToolResult.error_result(
                "需要安装: pip install pytesseract pillow\n"
                "并安装 Tesseract OCR: brew install tesseract tesseract-lang"
            )
        
        try:
            img = Image.open(path)
            text = pytesseract.image_to_string(img, lang=language)
            
            return ToolResult.success_result(
                data={
                    "text": text.strip(),
                    "length": len(text),
                    "image": str(path),
                },
                message=f"OCR 完成 ({len(text)} 字符)",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"OCR 失败: {str(e)}")
    
    async def ocr_screen(
        self,
        ctx: ToolContext,
        region: Optional[dict] = None,
    ) -> ToolResult:
        """截屏并 OCR"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        try:
            import pytesseract
        except ImportError:
            return ToolResult.error_result("需要安装: pip install pytesseract")
        
        try:
            if region:
                img = pyautogui.screenshot(
                    region=(region["x"], region["y"], region["width"], region["height"])
                )
            else:
                img = pyautogui.screenshot()
            
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            
            return ToolResult.success_result(
                data={
                    "text": text.strip(),
                    "length": len(text),
                    "screen_size": f"{img.width}x{img.height}",
                },
                message=f"屏幕 OCR 完成 ({len(text)} 字符)",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"屏幕 OCR 失败: {str(e)}")
    
    async def find_element(
        self,
        ctx: ToolContext,
        template_path: str,
        confidence: float = 0.8,
    ) -> ToolResult:
        """查找屏幕元素"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        path = Path(template_path).expanduser()
        if not path.exists():
            return ToolResult.error_result(f"模板图片不存在: {template_path}")
        
        try:
            location = pyautogui.locateOnScreen(str(path), confidence=confidence)
            
            if location:
                center = pyautogui.center(location)
                return ToolResult.success_result(
                    data={
                        "found": True,
                        "x": center.x,
                        "y": center.y,
                        "left": location.left,
                        "top": location.top,
                        "width": location.width,
                        "height": location.height,
                    },
                    message=f"找到元素: ({center.x}, {center.y})",
                )
            else:
                return ToolResult.success_result(
                    data={"found": False},
                    message="未找到匹配元素",
                )
        
        except Exception as e:
            return ToolResult.error_result(f"查找失败: {str(e)}")
    
    async def click(
        self,
        ctx: ToolContext,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1,
    ) -> ToolResult:
        """点击操作"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        try:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            
            return ToolResult.success_result(
                data={"x": x, "y": y, "button": button, "clicks": clicks},
                message=f"点击 ({x}, {y})",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"点击失败: {str(e)}")
    
    async def type_text(
        self,
        ctx: ToolContext,
        text: str,
        interval: float = 0.05,
    ) -> ToolResult:
        """输入文本"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        try:
            pyautogui.write(text, interval=interval)
            
            return ToolResult.success_result(
                data={"text": text, "length": len(text)},
                message=f"输入文本 ({len(text)} 字符)",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"输入失败: {str(e)}")
    
    async def hotkey(
        self,
        ctx: ToolContext,
        keys: list[str],
    ) -> ToolResult:
        """快捷键"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        try:
            pyautogui.hotkey(*keys)
            
            return ToolResult.success_result(
                data={"keys": keys},
                message=f"按下快捷键: {'+'.join(keys)}",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"快捷键失败: {str(e)}")
    
    async def move_mouse(
        self,
        ctx: ToolContext,
        x: int,
        y: int,
        duration: float = 0.2,
    ) -> ToolResult:
        """移动鼠标"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        try:
            pyautogui.moveTo(x, y, duration=duration)
            
            return ToolResult.success_result(
                data={"x": x, "y": y},
                message=f"移动到 ({x}, {y})",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"移动失败: {str(e)}")
    
    async def scroll(
        self,
        ctx: ToolContext,
        amount: int,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> ToolResult:
        """滚动"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        try:
            if x is not None and y is not None:
                pyautogui.scroll(amount, x=x, y=y)
            else:
                pyautogui.scroll(amount)
            
            direction = "向上" if amount > 0 else "向下"
            return ToolResult.success_result(
                data={"amount": amount, "x": x, "y": y},
                message=f"滚动 {direction} {abs(amount)}",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"滚动失败: {str(e)}")
    
    async def get_screen_size(self, ctx: ToolContext) -> ToolResult:
        """获取屏幕尺寸"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        size = pyautogui.size()
        
        return ToolResult.success_result(
            data={"width": size.width, "height": size.height},
            message=f"屏幕尺寸: {size.width}x{size.height}",
        )
    
    async def list_windows(self, ctx: ToolContext) -> ToolResult:
        """列出窗口"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        try:
            import pygetwindow as gw
        except ImportError:
            return ToolResult.error_result("需要安装: pip install pygetwindow")
        
        try:
            windows = gw.getAllTitles()
            windows = [w for w in windows if w.strip()]  # 过滤空标题
            
            return ToolResult.success_result(
                data={"windows": windows, "count": len(windows)},
                message=f"找到 {len(windows)} 个窗口",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"获取窗口列表失败: {str(e)}")
    
    async def activate_window(
        self,
        ctx: ToolContext,
        title: str,
    ) -> ToolResult:
        """激活窗口"""
        try:
            import pygetwindow as gw
        except ImportError:
            return ToolResult.error_result("需要安装: pip install pygetwindow")
        
        try:
            windows = gw.getWindowsWithTitle(title)
            
            if not windows:
                return ToolResult.error_result(f"未找到窗口: {title}")
            
            window = windows[0]
            window.activate()
            
            return ToolResult.success_result(
                data={"title": window.title},
                message=f"已激活窗口: {window.title}",
            )
        
        except Exception as e:
            return ToolResult.error_result(f"激活窗口失败: {str(e)}")
    
    async def wait_for_element(
        self,
        ctx: ToolContext,
        template_path: str,
        timeout: int = 30,
    ) -> ToolResult:
        """等待元素出现"""
        pyautogui = self._check_pyautogui()
        if not pyautogui:
            return ToolResult.error_result("需要安装: pip install pyautogui")
        
        path = Path(template_path).expanduser()
        if not path.exists():
            return ToolResult.error_result(f"模板图片不存在: {template_path}")
        
        start_time = datetime.now()
        
        while True:
            try:
                location = pyautogui.locateOnScreen(str(path), confidence=0.8)
                
                if location:
                    center = pyautogui.center(location)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    return ToolResult.success_result(
                        data={
                            "found": True,
                            "x": center.x,
                            "y": center.y,
                            "elapsed_seconds": elapsed,
                        },
                        message=f"元素已出现: ({center.x}, {center.y})",
                    )
            except Exception:
                pass
            
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= timeout:
                return ToolResult.success_result(
                    data={"found": False, "elapsed_seconds": elapsed},
                    message=f"等待超时 ({timeout}s)",
                )
            
            await asyncio.sleep(0.5)
    
    async def click_element(
        self,
        ctx: ToolContext,
        template_path: str,
        confidence: float = 0.8,
    ) -> ToolResult:
        """查找并点击元素"""
        result = await self.find_element(ctx, template_path, confidence)
        
        if not result.success:
            return result
        
        if not result.data.get("found"):
            return ToolResult.error_result("未找到元素，无法点击")
        
        x = result.data["x"]
        y = result.data["y"]
        
        return await self.click(ctx, x, y)
