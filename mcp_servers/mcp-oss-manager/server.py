from mcp.server.fastmcp import FastMCP, Context
from pywayne.aliyun_oss import OssManager
from typing import List, Optional, Dict
import oss2
import cv2
import numpy as np
from pathlib import Path
import os

# 默认配置
DEFAULT_CONFIG = {
    "OSS_ENDPOINT": "xxx",
    "OSS_BUCKET_NAME": "xxx",
    "OSS_ACCESS_KEY_ID": "xxx",
    "OSS_ACCESS_KEY_SECRET": "xxx"
}

# 初始化 MCP 服务器
mcp = FastMCP("OSS Bot")

class OssBot:
    def __init__(self):
        self.manager = None
        # 自动初始化
        self.init_manager()
    
    def init_manager(self):
        """初始化 OSS 管理器（使用默认配置）"""
        self.manager = OssManager(
            endpoint=DEFAULT_CONFIG["OSS_ENDPOINT"],
            bucket_name=DEFAULT_CONFIG["OSS_BUCKET_NAME"],
            api_key=DEFAULT_CONFIG["OSS_ACCESS_KEY_ID"],
            api_secret=DEFAULT_CONFIG["OSS_ACCESS_KEY_SECRET"],
            verbose=True
        )

# 创建全局 bot 实例        
bot = OssBot()

@mcp.tool()
def get_current_config() -> Dict[str, str]:
    """
    获取当前使用的配置信息
    
    Returns:
        当前配置信息
    """
    return {
        "oss_endpoint": DEFAULT_CONFIG["OSS_ENDPOINT"],
        "oss_bucket_name": DEFAULT_CONFIG["OSS_BUCKET_NAME"],
        "oss_access_key_id": DEFAULT_CONFIG["OSS_ACCESS_KEY_ID"],
        "oss_access_key_secret": "***"
    }

@mcp.tool()
def oss_download_file(key: str, root_dir: Optional[str] = None) -> bool:
    """从阿里云OSS下载指定 key 的文件到本地"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.download_file(key, root_dir)

@mcp.tool()
def oss_download_files_with_prefix(prefix: str, root_dir: Optional[str] = None) -> bool:
    """从阿里云OSS下载指定前缀的所有文件"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.download_files_with_prefix(prefix, root_dir)

@mcp.tool()
def oss_list_all_keys(sort: bool = True) -> List[str]:
    """列举阿里云OSS bucket 中所有 key"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.list_all_keys(sort)

@mcp.tool()
def oss_list_keys_with_prefix(prefix: str, sort: bool = True) -> List[str]:
    """列举阿里云OSS中指定前缀的所有 key"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.list_keys_with_prefix(prefix, sort)

@mcp.tool()
def oss_upload_file(key: str, file_path: str) -> bool:
    """上传本地文件到阿里云OSS"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.upload_file(key, file_path)

@mcp.tool()
def oss_upload_text(key: str, text: str) -> bool:
    """上传文本内容到阿里云OSS"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.upload_text(key, text)

@mcp.tool()
def oss_delete_file(key: str) -> bool:
    """从阿里云OSS删除指定 key 的文件"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.delete_file(key)

@mcp.tool()
def oss_delete_files_with_prefix(prefix: str) -> bool:
    """从阿里云OSS删除指定前缀的所有文件"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.delete_files_with_prefix(prefix)

@mcp.tool()
def oss_upload_directory(local_path: str, prefix: str = "") -> bool:
    """上传整个文件夹到阿里云OSS"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.upload_directory(local_path, prefix)

@mcp.tool()
def oss_download_directory(prefix: str, local_path: str) -> bool:
    """从阿里云OSS下载整个文件夹"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.download_directory(prefix, local_path)

@mcp.tool()
def oss_list_directory_contents(prefix: str, sort: bool = True) -> List[tuple[str, bool]]:
    """列出阿里云OSS指定文件夹下的所有文件和子文件夹（不深入子文件夹）"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    return bot.manager.list_directory_contents(prefix, sort)

# 添加一些有用的提示模板
@mcp.prompt()
def init_oss_connection() -> str:
    """初始化阿里云OSS连接的提示模板"""
    return """请帮我初始化阿里云OSS连接。我需要提供:
1. endpoint
2. bucket_name 
3. api_key (可选)
4. api_secret (可选)
5. verbose (可选,默认True)"""

@mcp.tool()
def oss_upload_image(key: str, image_path: str) -> bool:
    """
    上传图片到阿里云OSS
    
    Args:
        key: OSS 中的键值
        image_path: 图片文件路径
        
    Returns:
        是否上传成功
    """
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    
    # 读取图片文件
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图片文件: {image_path}")
        
    return bot.manager.upload_image(key, image)

@mcp.tool()
def oss_download_image(image_key: str, image_save_path: str) -> None:
    """从阿里云OSS下载图片"""
    if not bot.manager:
        raise ValueError("OSS 连接初始化失败")
    bot.manager.download_image(image_key, image_save_path)

@mcp.prompt()
def list_operations() -> str:
    """列出所有可用操作的提示模板"""
    return """我可以帮你完成以下 OSS 操作:
1. 下载文件 (download_file)
2. 批量下载文件 (download_files_with_prefix)
3. 列举所有文件 (list_all_keys)
4. 列举指定前缀的文件 (list_keys_with_prefix)
5. 上传文件 (upload_file)
6. 上传文本 (upload_text)
7. 上传图片 (upload_image)
8. 删除文件 (delete_file)
9. 批量删除文件 (delete_files_with_prefix)
10. 上传目录 (upload_directory)
11. 下载目录 (download_directory)
12. 列出目录内容 (list_directory_contents)

请告诉我你想执行哪个操作?""" 

if __name__ == "__main__":
    mcp.run() 