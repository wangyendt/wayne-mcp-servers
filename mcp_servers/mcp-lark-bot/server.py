from mcp.server.fastmcp import FastMCP
from pywayne.lark_bot import LarkBot, TextContent, PostContent
from typing import Dict, List, Optional, Union
import os
import inspect

# 默认配置
DEFAULT_CONFIG = {
    # 飞书配置
    "LARK_APP_ID": "xxx",
    "LARK_APP_SECRET": "xxx"
}

# 创建MCP服务器
mcp = FastMCP("飞书机器人服务")

# 全局变量
bot: Optional[LarkBot] = None

def init_feishu_bot() -> Dict[str, str]:
    """
    初始化飞书机器人（使用默认配置）
    
    Returns:
        初始化结果
    """
    global bot
    try:
        bot = LarkBot(
            app_id=DEFAULT_CONFIG["LARK_APP_ID"],
            app_secret=DEFAULT_CONFIG["LARK_APP_SECRET"]
        )
        # 测试连接是否成功（获取群组列表）
        bot.get_group_list()
        return {"status": "success", "message": "飞书机器人初始化成功"}
    except Exception as e:
        return {"status": "error", "message": f"飞书机器人初始化失败: {str(e)}"}

def ensure_bot_initialized() -> bool:
    """
    确保机器人已经初始化
    
    Returns:
        是否已初始化
    """
    if bot is None:
        # 使用默认配置初始化
        result = init_feishu_bot()
        return result["status"] == "success"
    return True

@mcp.tool()
def get_current_config() -> Dict[str, str]:
    """
    获取当前使用的配置信息
    
    Returns:
        当前配置信息
    """
    return {
        "lark_app_id": DEFAULT_CONFIG["LARK_APP_ID"],
        "lark_app_secret": "***"
    }

@mcp.tool()
def update_config(
    lark_app_id: str = "",
    lark_app_secret: str = ""
) -> Dict[str, str]:
    """
    更新配置信息（通过环境变量）
    
    Args:
        lark_app_id: 飞书应用的App ID
        lark_app_secret: 飞书应用的App Secret
        
    Returns:
        更新结果
    """
    if lark_app_id:
        os.environ["LARK_APP_ID"] = lark_app_id
    if lark_app_secret:
        os.environ["LARK_APP_SECRET"] = lark_app_secret
        
    # 如果更新了飞书配置，重新初始化机器人
    if lark_app_id or lark_app_secret:
        return init_feishu_bot(lark_app_id, lark_app_secret)
    
    return {"status": "success", "message": "配置更新成功"}

# 高级功能 - 飞书用户和群组查找
@mcp.tool()
def find_feishu_user(mobile: str = "", email: str = "") -> Dict[str, str]:
    """
    通过手机号或邮箱查找飞书用户
    
    Args:
        mobile: 用户手机号
        email: 用户邮箱
        
    Returns:
        包含用户信息的字典，包括user_id等
        如果未找到用户或机器人未初始化，返回空字典
    """
    if not ensure_bot_initialized():
        return {"error": "飞书机器人未初始化"}
    
    # 确保手机号是字符串类型
    if mobile and not isinstance(mobile, str):
        mobile = str(mobile)
    # 移除可能的引号
    if mobile and mobile.startswith('"') and mobile.endswith('"'):
        mobile = mobile[1:-1]
    
    mobiles = [mobile] if mobile else []
    emails = [email] if email else []
    users = bot.get_user_info(emails, mobiles)
    if users:
        return users[0]
    return {}

@mcp.tool()
def find_feishu_group(group_name: str) -> Dict[str, Union[str, List[Dict]]]:
    """
    查找飞书群组信息
    
    Args:
        group_name: 群组名称
        
    Returns:
        包含群组信息的字典：
        {
            "chat_id": "群组ID",
            "name": "群组名称",
            "members": [群成员信息列表]
        }
        如果未找到群组，返回空字典
    """
    chat_ids = bot.get_group_chat_id_by_name(group_name)
    if not chat_ids:
        return {}
    
    chat_id = chat_ids[0]
    members = bot.get_members_in_group_by_group_chat_id(chat_id)
    
    return {
        "chat_id": chat_id,
        "name": group_name,
        "members": members
    }

@mcp.tool()
def find_feishu_group_member(group_name: str, member_name: str) -> Dict[str, str]:
    """
    在指定群组中查找成员
    
    Args:
        group_name: 群组名称
        member_name: 成员名称
        
    Returns:
        包含成员信息的字典：
        {
            "name": "成员名称",
            "open_id": "成员ID"
        }
        如果未找到成员，返回空字典
    """
    group = find_feishu_group(group_name)
    if not group:
        return {}
    
    member_ids = bot.get_member_open_id_by_name(group["chat_id"], member_name)
    if not member_ids:
        return {}
    
    return {
        "name": member_name,
        "open_id": member_ids[0]
    }

# 高级功能 - 飞书消息发送
@mcp.tool()
def send_message(
    message: str,
    *,
    to_user_mobile: str = "",
    to_user_email: str = "",
    to_group: str = "",
    at_all: bool = False,
    at_members: List[str] = None,
    is_important: bool = False,
    message_type: str = "text"  # text, post, image, file, audio, video
) -> Dict:
    """
    统一的消息发送接口
    
    Args:
        message: 消息内容。如果是文本消息，直接是文本内容；如果是富文本，则是JSON格式的富文本内容；如果是文件类消息，则是文件路径
        to_user_mobile: 接收用户的手机号
        to_user_email: 接收用户的邮箱
        to_group: 接收群组的名称
        at_all: 是否@所有人(仅群消息有效)
        at_members: 需要@的群成员名称列表(仅群消息有效)
        is_important: 是否是重要消息(仅文本消息有效)
        message_type: 消息类型，支持:
            - text: 文本消息
            - post: 富文本消息
            - image: 图片消息
            - file: 文件消息
            - audio: 音频消息
            - video: 视频消息
        
    Returns:
        发送结果
    """
    # 确保机器人已初始化
    if not ensure_bot_initialized():
        return {"error": "飞书机器人未初始化"}
    
    # 确定接收者
    if to_user_mobile or to_user_email:
        # 发送给个人
        user = find_feishu_user(to_user_mobile, to_user_email)
        if not user:
            return {"error": "未找到用户"}
        receiver_id = user["user_id"]
        is_group = False
    elif to_group:
        # 发送给群组
        group = find_feishu_group(to_group)
        if not group:
            return {"error": "未找到群组"}
        receiver_id = group["chat_id"]
        is_group = True
    else:
        return {"error": "必须指定接收用户或群组"}
    
    # 根据消息类型发送
    try:
        if message_type == "text":
            # 构建文本消息
            text = ""
            if is_group:
                if at_all:
                    text += TextContent.make_at_all_pattern() + " "
                if at_members:
                    for member in at_members:
                        member_info = find_feishu_group_member(to_group, member)
                        if member_info:
                            text += TextContent.make_at_someone_pattern(
                                member_info["open_id"],
                                member_info["name"],
                                "open_id"
                            ) + " "
            
            text += message if not is_important else TextContent.make_bold_pattern(message)
            
            # 发送文本消息
            if is_group:
                return bot.send_text_to_chat(receiver_id, text)
            else:
                return bot.send_text_to_user(receiver_id, text)
                
        elif message_type == "post":
            # 发送富文本消息
            if is_group:
                return bot.send_post_to_chat(receiver_id, message)
            else:
                return bot.send_post_to_user(receiver_id, message)
                
        elif message_type == "image":
            # 上传并发送图片
            image_key = bot.upload_image(message)
            if not image_key:
                return {"error": "图片上传失败"}
            if is_group:
                return bot.send_image_to_chat(receiver_id, image_key)
            else:
                return bot.send_image_to_user(receiver_id, image_key)
                
        elif message_type == "file":
            # 上传并发送文件
            file_key = bot.upload_file(message, "stream")
            if not file_key:
                return {"error": "文件上传失败"}
            if is_group:
                return bot.send_file_to_chat(receiver_id, file_key)
            else:
                return bot.send_file_to_user(receiver_id, file_key)
                
        elif message_type == "audio":
            # 上传并发送音频
            audio_key = bot.upload_file(message, "opus")
            if not audio_key:
                return {"error": "音频上传失败"}
            if is_group:
                return bot.send_audio_to_chat(receiver_id, audio_key)
            else:
                return bot.send_audio_to_user(receiver_id, audio_key)
                
        elif message_type == "video":
            # 上传并发送视频
            video_key = bot.upload_file(message, "mp4")
            if not video_key:
                return {"error": "视频上传失败"}
            if is_group:
                return bot.send_media_to_chat(receiver_id, video_key)
            else:
                return bot.send_media_to_user(receiver_id, video_key)
                
        else:
            return {"error": f"不支持的消息类型: {message_type}"}
            
    except Exception as e:
        return {"error": f"消息发送失败: {str(e)}"}

@mcp.tool()
def send_feishu_rich_message(
    title: str,
    content_elements: List[Dict],
    *,
    to_user_mobile: str = "",
    to_user_email: str = "",
    to_group: str = ""
) -> Dict:
    """
    发送飞书富文本消息的高级功能
    
    Args:
        title: 消息标题
        content_elements: 消息元素列表，每个元素是一个字典，支持以下类型：
            - {"type": "text", "content": "文本内容", "bold": True}
            - {"type": "at_user", "name": "用户名"}
            - {"type": "at_all"}
            - {"type": "link", "text": "显示文本", "url": "链接地址"}
            - {"type": "markdown", "content": "Markdown内容"}
            - {"type": "divider"}  # 分割线
        to_user_mobile: 接收用户的手机号
        to_user_email: 接收用户的邮箱
        to_group: 接收群组的名称
        
    Returns:
        发送结果
    """
    post = PostContent(title)
    
    for element in content_elements:
        if element["type"] == "text":
            styles = ["bold"] if element.get("bold") else []
            post.add_content_in_new_line(
                post.make_text_content(element["content"], styles)
            )
        elif element["type"] == "at_user" and to_group:
            member = find_feishu_group_member(to_group, element["name"])
            if member:
                post.add_content_in_new_line(
                    post.make_at_content(member["open_id"])
                )
        elif element["type"] == "at_all":
            text = TextContent.make_at_all_pattern()
            post.add_content_in_new_line(
                post.make_text_content(text)
            )
        elif element["type"] == "link":
            post.add_content_in_new_line(
                post.make_link_content(element["text"], element["url"])
            )
        elif element["type"] == "markdown":
            post.add_content_in_new_line(
                post.make_markdown_content(element["content"])
            )
        elif element["type"] == "divider":
            post.add_content_in_new_line(
                post.make_hr_content()
            )
    
    # 发送消息
    if to_user_mobile or to_user_email:
        user = find_feishu_user(to_user_mobile, to_user_email)
        if user:
            return bot.send_post_to_user(user["user_id"], post.get_content())
        return {"error": "User not found"}
    
    if to_group:
        group = find_feishu_group(to_group)
        if group:
            return bot.send_post_to_chat(group["chat_id"], post.get_content())
        return {"error": "Group not found"}
    
    return {"error": "No valid recipient specified"}

@mcp.tool()
def send_feishu_file(
    file_path: str,
    *,
    to_user_mobile: str = "",
    to_user_email: str = "",
    to_group: str = "",
    file_type: str = "stream",  # stream, opus, mp4, pdf, doc, xls, ppt
    message: str = ""
) -> Dict:
    """
    发送飞书文件的高级功能
    
    Args:
        file_path: 文件路径
        to_user_mobile: 接收用户的手机号
        to_user_email: 接收用户的邮箱
        to_group: 接收群组的名称
        file_type: 文件类型
        message: 随附的消息文本
        
    Returns:
        发送结果
    """
    # 上传文件
    if file_type == "image":
        file_key = bot.upload_image(file_path)
    else:
        file_key = bot.upload_file(file_path, file_type)
    
    if not file_key:
        return {"error": "File upload failed"}
    
    # 发送文件
    if to_user_mobile or to_user_email:
        user = find_feishu_user(to_user_mobile, to_user_email)
        if not user:
            return {"error": "User not found"}
        
        # 发送消息（如果有）
        if message:
            bot.send_text_to_user(user["user_id"], message)
        
        # 发送文件
        if file_type == "image":
            return bot.send_image_to_user(user["user_id"], file_key)
        elif file_type == "opus":
            return bot.send_audio_to_user(user["user_id"], file_key)
        elif file_type == "mp4":
            return bot.send_media_to_user(user["user_id"], file_key)
        else:
            return bot.send_file_to_user(user["user_id"], file_key)
    
    if to_group:
        group = find_feishu_group(to_group)
        if not group:
            return {"error": "Group not found"}
        
        # 发送消息（如果有）
        if message:
            bot.send_text_to_chat(group["chat_id"], message)
        
        # 发送文件
        if file_type == "image":
            return bot.send_image_to_chat(group["chat_id"], file_key)
        elif file_type == "opus":
            return bot.send_audio_to_chat(group["chat_id"], file_key)
        elif file_type == "mp4":
            return bot.send_media_to_chat(group["chat_id"], file_key)
        else:
            return bot.send_file_to_chat(group["chat_id"], file_key)
    
    return {"error": "No valid recipient specified"}

# API文档工具
@mcp.tool()
def get_api_documentation() -> Dict[str, str]:
    """
    获取LarkBot、TextContent和PostContent类的完整API文档
    
    Returns:
        包含三个类的完整文档信息的字典，包括：
        - 类的文档字符串
        - 所有公共方法及其文档
        - 方法的参数信息
        - 方法的返回值信息
    """
    def get_class_info(cls):
        # 获取类的文档
        class_doc = inspect.getdoc(cls) or ""
        
        # 获取所有公共方法
        methods_info = {}
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_'):  # 只获取公共方法
                # 获取方法的文档
                method_doc = inspect.getdoc(method) or ""
                
                # 获取方法的签名
                try:
                    signature = str(inspect.signature(method))
                except ValueError:
                    signature = "(无法获取参数信息)"
                
                methods_info[name] = {
                    "signature": signature,
                    "doc": method_doc
                }
        
        return {
            "doc": class_doc,
            "methods": methods_info
        }
    
    return {
        "LarkBot": get_class_info(LarkBot),
        "TextContent": get_class_info(TextContent),
        "PostContent": get_class_info(PostContent)
    }

@mcp.tool()
def get_usage_examples() -> Dict[str, List[Dict[str, str]]]:
    """
    获取各种常见用法的示例
    
    Returns:
        包含各种场景示例的字典，每个场景包含：
        - 场景描述
        - 示例代码
        - 预期结果
    """
    return {
        "基础消息": [
            {
                "场景": "发送普通文本消息",
                "代码": """
group_chat_ids = bot.get_group_chat_id_by_name("测试群")
bot.send_text_to_chat(group_chat_ids[0], "Hello, World!")
                """,
                "说明": "最基本的消息发送方式"
            },
            {
                "场景": "发送@消息",
                "代码": """
group_chat_ids = bot.get_group_chat_id_by_name("测试群")
member_id = bot.get_member_open_id_by_name(group_chat_ids[0], "张三")[0]
text = TextContent.make_at_someone_pattern(member_id, "张三", "open_id")
bot.send_text_to_chat(group_chat_ids[0], f"{text} 请查看文档")
                """,
                "说明": "发送带有@提醒的消息"
            }
        ],
        "富文本消息": [
            {
                "场景": "发送带格式的文本",
                "代码": """
text = TextContent.make_bold_pattern("重要通知") + "\\n"
text += TextContent.make_at_all_pattern() + "\\n"
text += "1. " + TextContent.make_underline_pattern("项目进度") + "\\n"
text += "2. " + TextContent.make_italian_pattern("风险提示")
bot.send_text_to_chat(chat_id, text)
                """,
                "说明": "使用加粗、下划线、斜体等格式"
            }
        ],
        "复杂消息": [
            {
                "场景": "发送会议纪要",
                "代码": """
post = PostContent("项目周会")
post.add_content_in_new_line(post.make_text_content("与会人员：", ["bold"]))
post.add_content_in_new_line(post.make_at_content(member_id, ["italic"]))
post.add_content_in_new_line(post.make_hr_content())
post.add_content_in_new_line(post.make_markdown_content("## 会议要点"))
post.add_content_in_new_line(post.make_text_content("1. 项目进展顺利"))
bot.send_post_to_chat(chat_id, post.get_content())
                """,
                "说明": "创建包含多种元素的富文本消息"
            }
        ],
        "文件处理": [
            {
                "场景": "发送文件",
                "代码": """
# 上传并发送图片
image_key = bot.upload_image("path/to/image.png")
bot.send_image_to_chat(chat_id, image_key)

# 上传并发送文件
file_key = bot.upload_file("path/to/doc.pdf", "pdf")
bot.send_file_to_chat(chat_id, file_key)
                """,
                "说明": "上传并发送各种类型的文件"
            }
        ]
    }

# 用户信息相关工具
@mcp.tool()
def get_user_info(emails: List[str], mobiles: List[str]) -> Optional[Dict]:
    """获取用户信息"""
    return bot.get_user_info(emails, mobiles)

# 群组相关工具
@mcp.tool()
def get_group_list() -> List[Dict]:
    """获取群组列表"""
    return bot.get_group_list()

@mcp.tool()
def get_group_chat_id_by_name(group_name: str) -> List[str]:
    """通过群组名称获取群组ID"""
    return bot.get_group_chat_id_by_name(group_name)

@mcp.tool()
def get_members_in_group_by_group_chat_id(group_chat_id: str) -> List[Dict]:
    """获取群组成员列表"""
    return bot.get_members_in_group_by_group_chat_id(group_chat_id)

@mcp.tool()
def get_member_open_id_by_name(group_chat_id: str, member_name: str) -> List[str]:
    """通过成员名称获取成员open_id"""
    return bot.get_member_open_id_by_name(group_chat_id, member_name)

# 消息发送工具 - 文本消息
@mcp.tool()
def send_text_to_user(user_open_id: str, text: str = '') -> Dict:
    """发送文本消息给用户"""
    return bot.send_text_to_user(user_open_id, text)

@mcp.tool()
def send_text_to_chat(chat_id: str, text: str = '') -> Dict:
    """发送文本消息到群组"""
    return bot.send_text_to_chat(chat_id, text)

# 消息发送工具 - 图片消息
@mcp.tool()
def send_image_to_user(user_open_id: str, image_key: str) -> Dict:
    """发送图片给用户"""
    return bot.send_image_to_user(user_open_id, image_key)

@mcp.tool()
def send_image_to_chat(chat_id: str, image_key: str) -> Dict:
    """发送图片到群组"""
    return bot.send_image_to_chat(chat_id, image_key)

# 消息发送工具 - 交互消息
@mcp.tool()
def send_interactive_to_user(user_open_id: str, interactive: Dict) -> Dict:
    """发送交互消息给用户"""
    return bot.send_interactive_to_user(user_open_id, interactive)

@mcp.tool()
def send_interactive_to_chat(chat_id: str, interactive: Dict) -> Dict:
    """发送交互消息到群组"""
    return bot.send_interactive_to_chat(chat_id, interactive)

# 消息发送工具 - 分享消息
@mcp.tool()
def send_shared_chat_to_user(user_open_id: str, shared_chat_id: str) -> Dict:
    """分享群组给用户"""
    return bot.send_shared_chat_to_user(user_open_id, shared_chat_id)

@mcp.tool()
def send_shared_chat_to_chat(chat_id: str, shared_chat_id: str) -> Dict:
    """分享群组到群组"""
    return bot.send_shared_chat_to_chat(chat_id, shared_chat_id)

@mcp.tool()
def send_shared_user_to_user(user_open_id: str, shared_user_id: str) -> Dict:
    """分享用户给用户"""
    return bot.send_shared_user_to_user(user_open_id, shared_user_id)

@mcp.tool()
def send_shared_user_to_chat(chat_id: str, shared_user_id: str) -> Dict:
    """分享用户到群组"""
    return bot.send_shared_user_to_chat(chat_id, shared_user_id)

# 消息发送工具 - 音频消息
@mcp.tool()
def send_audio_to_user(user_open_id: str, file_key: str) -> Dict:
    """发送音频给用户"""
    return bot.send_audio_to_user(user_open_id, file_key)

@mcp.tool()
def send_audio_to_chat(chat_id: str, file_key: str) -> Dict:
    """发送音频到群组"""
    return bot.send_audio_to_chat(chat_id, file_key)

# 消息发送工具 - 媒体消息
@mcp.tool()
def send_media_to_user(user_open_id: str, file_key: str) -> Dict:
    """发送媒体给用户"""
    return bot.send_media_to_user(user_open_id, file_key)

@mcp.tool()
def send_media_to_chat(chat_id: str, file_key: str) -> Dict:
    """发送媒体到群组"""
    return bot.send_media_to_chat(chat_id, file_key)

# 消息发送工具 - 文件消息
@mcp.tool()
def send_file_to_user(user_open_id: str, file_key: str) -> Dict:
    """发送文件给用户"""
    return bot.send_file_to_user(user_open_id, file_key)

@mcp.tool()
def send_file_to_chat(chat_id: str, file_key: str) -> Dict:
    """发送文件到群组"""
    return bot.send_file_to_chat(chat_id, file_key)

# 消息发送工具 - 系统消息
@mcp.tool()
def send_system_msg_to_user(user_open_id: str, system_msg_text: str) -> Dict:
    """发送系统消息给用户"""
    return bot.send_system_msg_to_user(user_open_id, system_msg_text)

# 消息发送工具 - 富文本消息
@mcp.tool()
def send_post_to_user(user_open_id: str, post_content: Dict[str, str]) -> Dict:
    """发送富文本消息给用户"""
    return bot.send_post_to_user(user_open_id, post_content)

@mcp.tool()
def send_post_to_chat(chat_id: str, post_content: Dict[str, dict]) -> Dict:
    """发送富文本消息到群组"""
    return bot.send_post_to_chat(chat_id, post_content)

# 文件操作工具
@mcp.tool()
def upload_image(image_path: str) -> str:
    """上传图片"""
    return bot.upload_image(image_path)

@mcp.tool()
def download_image(image_key: str, image_save_path: str) -> None:
    """下载图片"""
    bot.download_image(image_key, image_save_path)

@mcp.tool()
def upload_file(file_path: str, file_type: str = 'stream') -> str:
    """上传文件"""
    return bot.upload_file(file_path, file_type)

@mcp.tool()
def download_file(file_key: str, file_save_path: str) -> None:
    """下载文件"""
    bot.download_file(file_key, file_save_path)

if __name__ == "__main__":
    mcp.run() 