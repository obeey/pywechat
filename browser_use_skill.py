#!/usr/bin/env python3
"""
browser-use skill: 使用正确profile打开浏览器的固化操作
封装了browser-use工具的正确使用方法，避免重复尝试
"""

import subprocess
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

class BrowserUseSkill:
    """browser-use技能封装类"""

    def __init__(self, profile: str = "Default", headless: bool = False):
        """
        初始化browser-use技能

        Args:
            profile: Chrome profile名称，默认为"Default"（Nico的profile）
            headless: 是否无头模式，默认为False（显示浏览器窗口）
        """
        self.browser_path = r"C:\Users\Nico\.browser-use-env\Scripts\browser-use.exe"
        self.profile = profile
        self.headless = headless
        self.current_session = None

        if not os.path.exists(self.browser_path):
            raise FileNotFoundError(f"browser-use工具未找到: {self.browser_path}")

    def _run_command(self, cmd: str, args: Optional[List[str]] = None,
                    timeout: int = 30, session: Optional[str] = None) -> Dict:
        """运行browser-use命令的内部方法"""
        cmd_list = [self.browser_path]

        # 添加profile参数
        if self.profile:
            cmd_list.extend(["--profile", self.profile])

        # 添加headed/headless参数
        if not self.headless:
            cmd_list.append("--headed")

        # 添加session参数
        if session:
            cmd_list.extend(["--session", session])

        # 添加命令
        cmd_list.append(cmd)

        # 添加参数
        if args:
            if isinstance(args, list):
                cmd_list.extend(args)
            else:
                cmd_list.append(str(args))

        print(f"[BrowserUse] 执行命令: {' '.join(cmd_list)}")

        # 设置环境解决编码问题
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        try:
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                timeout=timeout,
                env=env
            )

            # 解码输出
            def decode(data: bytes) -> str:
                if not data:
                    return ""
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return data.decode('gbk')
                    except UnicodeDecodeError:
                        try:
                            return data.decode('latin-1')
                        except UnicodeDecodeError:
                            return str(data)

            stdout = decode(result.stdout)
            stderr = decode(result.stderr)

            return {
                'success': result.returncode == 0,
                'stdout': stdout,
                'stderr': stderr,
                'returncode': result.returncode
            }

        except subprocess.TimeoutExpired:
            print(f"[BrowserUse] 命令超时: {cmd}")
            return {'success': False, 'stdout': '', 'stderr': 'Timeout', 'returncode': -1}
        except Exception as e:
            print(f"[BrowserUse] 命令失败: {e}")
            return {'success': False, 'stdout': '', 'stderr': str(e), 'returncode': -1}

    def cleanup_sessions(self) -> bool:
        """清理所有browser-use会话"""
        print("[BrowserUse] 清理所有会话...")

        # 列出所有会话
        sessions_result = self._run_command("sessions", timeout=10)

        # 关闭所有会话
        success = True
        for i in range(3):
            close_result = self._run_command("close", timeout=10)
            if not close_result['success']:
                if "No session" in close_result['stderr'] or "already closed" in close_result['stderr']:
                    print("[BrowserUse] 没有活跃会话")
                    break
                else:
                    print(f"[BrowserUse] 关闭会话尝试 {i+1} 失败")
                    success = False
            time.sleep(2)

        time.sleep(3)
        print("[BrowserUse] 会话清理完成")
        return success

    def open_url(self, url: str, session_name: Optional[str] = None,
                wait_time: int = 5) -> bool:
        """
        打开指定URL

        Args:
            url: 要打开的URL
            session_name: 会话名称，如果为None则使用默认会话
            wait_time: 等待页面加载的时间（秒）

        Returns:
            是否成功打开
        """
        print(f"[BrowserUse] 打开URL: {url}")

        # 先清理会话
        self.cleanup_sessions()

        # 打开URL
        result = self._run_command("open", [url], timeout=60, session=session_name)

        if result['success']:
            print(f"[BrowserUse] 成功打开: {url}")
            self.current_session = session_name or "default"

            # 等待页面加载
            if wait_time > 0:
                print(f"[BrowserUse] 等待 {wait_time} 秒页面加载...")
                time.sleep(wait_time)

            return True
        else:
            print(f"[BrowserUse] 打开失败: {result['stderr'][:200]}")
            return False

    def get_page_state(self, session_name: Optional[str] = None) -> Optional[str]:
        """
        获取页面状态

        Args:
            session_name: 会话名称，如果为None则使用当前会话

        Returns:
            页面状态文本，失败返回None
        """
        session = session_name or self.current_session
        if not session:
            print("[BrowserUse] 错误: 没有活跃会话")
            return None

        print(f"[BrowserUse] 获取页面状态 (会话: {session})")
        result = self._run_command("state", timeout=30, session=session)

        if result['success']:
            return result['stdout']
        else:
            print(f"[BrowserUse] 获取状态失败: {result['stderr'][:200]}")
            return None

    def take_screenshot(self, filename: str, session_name: Optional[str] = None) -> bool:
        """
        截取屏幕截图

        Args:
            filename: 截图保存文件名
            session_name: 会话名称

        Returns:
            是否成功截图
        """
        session = session_name or self.current_session
        if not session:
            print("[BrowserUse] 错误: 没有活跃会话")
            return False

        print(f"[BrowserUse] 截图: {filename}")
        result = self._run_command("screenshot", [filename], timeout=30, session=session)
        return result['success']

    def scroll_page(self, direction: str = "down", amount: int = 800,
                   session_name: Optional[str] = None) -> bool:
        """
        滚动页面

        Args:
            direction: 滚动方向，"down"或"up"
            amount: 滚动像素数
            session_name: 会话名称

        Returns:
            是否成功滚动
        """
        session = session_name or self.current_session
        if not session:
            print("[BrowserUse] 错误: 没有活跃会话")
            return False

        print(f"[BrowserUse] 滚动页面: {direction} {amount}px")
        result = self._run_command("scroll", [direction, "--amount", str(amount)],
                                 timeout=20, session=session)

        if result['success']:
            time.sleep(2)  # 等待滚动完成
            return True
        else:
            print(f"[BrowserUse] 滚动失败: {result['stderr'][:100]}")
            return False

    def type_text(self, text: str, session_name: Optional[str] = None) -> bool:
        """
        在页面中输入文本

        Args:
            text: 要输入的文本
            session_name: 会话名称

        Returns:
            是否成功输入
        """
        session = session_name or self.current_session
        if not session:
            print("[BrowserUse] 错误: 没有活跃会话")
            return False

        print(f"[BrowserUse] 输入文本: {text[:50]}...")
        result = self._run_command("type", [text], timeout=20, session=session)
        return result['success']

    def press_enter(self, session_name: Optional[str] = None) -> bool:
        """
        按Enter键

        Args:
            session_name: 会话名称

        Returns:
            是否成功
        """
        session = session_name or self.current_session
        if not session:
            print("[BrowserUse] 错误: 没有活跃会话")
            return False

        print("[BrowserUse] 按Enter键")
        result = self._run_command("keys", ["Enter"], timeout=20, session=session)
        return result['success']

    def close_session(self, session_name: Optional[str] = None) -> bool:
        """
        关闭指定会话

        Args:
            session_name: 会话名称

        Returns:
            是否成功关闭
        """
        session = session_name or self.current_session
        if not session:
            print("[BrowserUse] 错误: 没有指定会话")
            return False

        print(f"[BrowserUse] 关闭会话: {session}")
        result = self._run_command("close", timeout=20, session=session)

        if result['success']:
            self.current_session = None
            return True
        else:
            print(f"[BrowserUse] 关闭失败: {result['stderr'][:100]}")
            return False

    def open_facebook(self, wait_login: int = 30) -> bool:
        """
        打开Facebook（使用Nico的profile）

        Args:
            wait_login: 等待登录的时间（秒）

        Returns:
            是否成功打开
        """
        print("[BrowserUse] 打开Facebook...")

        # 生成唯一会话名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_name = f"facebook_{timestamp}"

        # 打开Facebook
        if not self.open_url("https://www.facebook.com", session_name, wait_time=10):
            return False

        print(f"[BrowserUse] Facebook已打开，会话: {session_name}")
        print("[BrowserUse] 请检查是否已登录Nico的Facebook账号")

        if wait_login > 0:
            print(f"[BrowserUse] 等待 {wait_login} 秒供您登录...")
            for i in range(wait_login):
                remaining = wait_login - i
                print(f"\r[BrowserUse] 等待 {remaining} 秒...", end="", flush=True)
                time.sleep(1)
            print("\n[BrowserUse] 登录等待完成")

        return True

    def open_zhihu(self, wait_login: int = 30) -> bool:
        """
        打开知乎（使用Nico的profile）

        Args:
            wait_login: 等待登录的时间（秒）

        Returns:
            是否成功打开
        """
        print("[BrowserUse] 打开知乎...")

        # 生成唯一会话名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_name = f"zhihu_{timestamp}"

        # 打开知乎
        if not self.open_url("https://www.zhihu.com", session_name, wait_time=10):
            return False

        print(f"[BrowserUse] 知乎已打开，会话: {session_name}")
        print("[BrowserUse] 请检查是否已登录Nico的知乎账号")

        if wait_login > 0:
            print(f"[BrowserUse] 等待 {wait_login} 秒供您登录...")
            for i in range(wait_login):
                remaining = wait_login - i
                print(f"\r[BrowserUse] 等待 {remaining} 秒...", end="", flush=True)
                time.sleep(1)
            print("\n[BrowserUse] 登录等待完成")

        return True

    def search_on_page(self, search_term: str, session_name: Optional[str] = None) -> bool:
        """
        在页面中搜索（假设搜索框已获得焦点）

        Args:
            search_term: 搜索关键词
            session_name: 会话名称

        Returns:
            是否成功搜索
        """
        session = session_name or self.current_session
        if not session:
            print("[BrowserUse] 错误: 没有活跃会话")
            return False

        print(f"[BrowserUse] 搜索: {search_term}")

        # 输入搜索词
        if not self.type_text(search_term, session):
            return False

        time.sleep(1)

        # 按Enter搜索
        if not self.press_enter(session):
            return False

        time.sleep(3)  # 等待搜索结果
        return True


# 使用示例
def example_usage():
    """使用示例"""
    print("=" * 60)
    print("browser-use技能使用示例")
    print("=" * 60)

    try:
        # 创建技能实例（使用Nico的profile）
        browser = BrowserUseSkill(profile="Default", headless=False)

        # 示例1: 打开Facebook
        print("\n示例1: 打开Facebook")
        if browser.open_facebook(wait_login=10):
            print("✓ Facebook打开成功")

            # 获取页面状态
            state = browser.get_page_state()
            if state:
                print(f"页面状态长度: {len(state)} 字符")

            # 截图
            browser.take_screenshot("facebook_screenshot.png")

            # 关闭会话
            browser.close_session()

        # 示例2: 打开知乎
        print("\n示例2: 打开知乎")
        if browser.open_zhihu(wait_login=10):
            print("✓ 知乎打开成功")

            # 导航到邀请页面
            if browser.open_url("https://www.zhihu.com/question/waiting",
                              wait_time=5):
                print("✓ 邀请页面打开成功")

                # 滚动页面
                browser.scroll_page(amount=1000)

                # 截图
                browser.take_screenshot("zhihu_invitations.png")

            # 关闭会话
            browser.close_session()

        print("\n" + "=" * 60)
        print("示例完成!")
        print("=" * 60)

    except Exception as e:
        print(f"[错误] {e}")


if __name__ == "__main__":
    example_usage()