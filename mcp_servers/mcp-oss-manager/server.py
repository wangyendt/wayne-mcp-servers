from mcp.server.fastmcp import FastMCP, Context
from pywayne.aliyun_oss import OssManager
from typing import List, Optional
import oss2
import cv2
import numpy as np
from pathlib import Path
import os

# 初始化 MCP 服务器
mcp = FastMCP("OSS Bot")

class OssBot:
    def __init__(self):
        self.manager = None
    
    def init_manager(self, endpoint: str, bucket_name: str, 
                    api_key: Optional[str] = None, 
                    api_secret: Optional[str] = None,
                    verbose: bool = True):
        """初始化 OSS 管理器"""
        self.manager = OssManager(endpoint, bucket_name, api_key, api_secret, verbose)

# 创建全局 bot 实例        
bot = OssBot()

@mcp.tool()
def init_oss(endpoint: str, bucket_name: str, 
             api_key: Optional[str] = None,
             api_secret: Optional[str] = None,
             verbose: bool = True) -> str:
    """
    初始化 OSS 连接
    
    Args:
        endpoint: OSS endpoint
        bucket_name: Bucket 名称
        api_key: API Key（可选）
        api_secret: API Secret（可选）
        verbose: 是否打印操作信息
    """
    bot.init_manager(endpoint, bucket_name, api_key, api_secret, verbose)
    return "OSS 连接已初始化"

@mcp.tool()
def download_file(key: str, root_dir: Optional[str] = None) -> bool:
    """
    下载指定 key 的文件到本地
    
    Args:
        key: OSS 中的键值
        root_dir: 下载文件的根目录
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.download_file(key, root_dir)

@mcp.tool()
def download_files_with_prefix(prefix: str, root_dir: Optional[str] = None) -> bool:
    """
    下载指定前缀的所有文件
    
    Args:
        prefix: 键值前缀
        root_dir: 下载文件的根目录
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.download_files_with_prefix(prefix, root_dir)

@mcp.tool()
def list_all_keys(sort: bool = True) -> List[str]:
    """
    列举 bucket 中所有 key
    
    Args:
        sort: 是否进行自然排序
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.list_all_keys(sort)

@mcp.tool()
def list_keys_with_prefix(prefix: str, sort: bool = True) -> List[str]:
    """
    列举指定前缀的所有 key
    
    Args:
        prefix: 键值前缀
        sort: 是否进行自然排序
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.list_keys_with_prefix(prefix, sort)

@mcp.tool()
def upload_file(key: str, file_path: str) -> bool:
    """
    上传本地文件
    
    Args:
        key: OSS 中的键值
        file_path: 本地文件路径
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.upload_file(key, file_path)

@mcp.tool()
def upload_text(key: str, text: str) -> bool:
    """
    上传文本内容
    
    Args:
        key: OSS 中的键值
        text: 要上传的文本内容
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.upload_text(key, text)

@mcp.tool()
def delete_file(key: str) -> bool:
    """
    删除指定 key 的文件
    
    Args:
        key: 要删除的文件的键值
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.delete_file(key)

@mcp.tool()
def delete_files_with_prefix(prefix: str) -> bool:
    """
    删除指定前缀的所有文件
    
    Args:
        prefix: 要删除的文件的键值前缀
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.delete_files_with_prefix(prefix)

@mcp.tool()
def upload_directory(local_path: str, prefix: str = "") -> bool:
    """
    上传整个文件夹到 OSS
    
    Args:
        local_path: 本地文件夹路径
        prefix: OSS 中的前缀路径
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.upload_directory(local_path, prefix)

@mcp.tool()
def download_directory(prefix: str, local_path: str) -> bool:
    """
    从 OSS 下载整个文件夹
    
    Args:
        prefix: OSS 中的前缀路径
        local_path: 下载到本地的目标路径
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.download_directory(prefix, local_path)

# 添加一些有用的提示模板
@mcp.prompt()
def init_connection() -> str:
    """初始化 OSS 连接的提示模板"""
    return """请帮我初始化 OSS 连接。我需要提供:
1. endpoint
2. bucket_name 
3. api_key (可选)
4. api_secret (可选)
5. verbose (可选,默认True)"""

@mcp.tool()
def list_directory_contents(prefix: str, sort: bool = True) -> List[tuple[str, bool]]:
    """
    列出指定文件夹下的所有文件和子文件夹（不深入子文件夹）
    
    Args:
        prefix: OSS 中的前缀路径
        sort: 是否排序，默认为 True
        
    Returns:
        包含 (name, is_directory) 元组的列表，name 是文件或文件夹名，is_directory 表示是否是文件夹
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    return bot.manager.list_directory_contents(prefix, sort) 

@mcp.tool()
def upload_image(key: str, image_path: str) -> bool:
    """
    上传图片到 OSS
    
    Args:
        key: OSS 中的键值
        image_path: 图片文件路径
        
    Returns:
        是否上传成功
    """
    if not bot.manager:
        raise ValueError("请先初始化 OSS 连接")
    
    # 读取图片文件
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图片文件: {image_path}")
        
    return bot.manager.upload_image(key, image) 

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