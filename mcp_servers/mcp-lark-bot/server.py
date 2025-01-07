from mcp.server.fastmcp import FastMCP
from pywayne.lark_bot import LarkBot, TextContent, PostContent
from typing import Dict, List, Optional, Union
import os
import inspect

# 创建MCP服务器
mcp = FastMCP("飞书机器人服务")

# 全局变量
bot: Optional[LarkBot] = None

@mcp.tool()
def init_feishu_bot(app_id: str, app_secret: str) -> Dict[str, str]:
    """
    初始化飞书机器人
    
    Args:
        app_id: 飞书应用的App ID
        app_secret: 飞书应用的App Secret
        
    Returns:
        初始化结果
    """
    global bot
    try:
        bot = LarkBot(app_id=app_id, app_secret=app_secret)
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
        # 尝试从环境变量初始化
        app_id = os.environ.get("LARK_APP_ID")
        app_secret = os.environ.get("LARK_APP_SECRET")
        if app_id and app_secret:
            result = init_feishu_bot(app_id, app_secret)
            return result["status"] == "success"
        return False
    return True

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
def send_feishu_text_message(
    message: str,
    *,
    to_user_mobile: str = "",
    to_user_email: str = "",
    to_group: str = "",
    at_all: bool = False,
    at_members: List[str] = None,
    is_important: bool = False
) -> Dict:
    """
    发送飞书文本消息的高级功能
    
    Args:
        message: 消息内容
        to_user_mobile: 接收用户的手机号
        to_user_email: 接收用户的邮箱
        to_group: 接收群组的名称
        at_all: 是否@所有人
        at_members: 需要@的群成员名称列表
        is_important: 是否是重要消息（会加粗显示）
        
    Returns:
        发送结果
    """
    # 构建消息文本
    text = ""
    
    # 添加@标记
    if to_group:
        if at_all:
            text += TextContent.make_at_all_pattern() + " "
        if at_members:
            group = find_feishu_group(to_group)
            if group:
                for member in at_members:
                    member_info = find_feishu_group_member(to_group, member)
                    if member_info:
                        text += TextContent.make_at_someone_pattern(
                            member_info["open_id"], 
                            member_info["name"],
                            "open_id"
                        ) + " "
    
    # 添加消息内容
    if is_important:
        text += TextContent.make_bold_pattern(message)
    else:
        text += message
    
    # 发送消息
    if to_user_mobile or to_user_email:
        user = find_feishu_user(to_user_mobile, to_user_email)
        if user:
            return bot.send_text_to_user(user["user_id"], text)
        return {"error": "User not found"}
    
    if to_group:
        group = find_feishu_group(to_group)
        if group:
            return bot.send_text_to_chat(group["chat_id"], text)
        return {"error": "Group not found"}
    
    return {"error": "No valid recipient specified"}

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

# 高级功能 - 示例场景组合
@mcp.tool()
def send_group_notification_with_all_formats(
    group_name: str,
    text_message: str,
    *,
    at_members: List[str] = None,
    at_all: bool = False,
    add_bold: bool = False,
    add_italic: bool = False,
    add_underline: bool = False,
    add_delete_line: bool = False,
    add_link: Optional[Dict[str, str]] = None  # {"text": "显示文本", "url": "链接地址"}
) -> Dict:
    """
    发送一条包含多种格式的群通知，支持sample.py中展示的所有文本格式
    
    Args:
        group_name: 群组名称
        text_message: 主要消息内容
        at_members: 需要@的成员列表
        at_all: 是否@所有人
        add_bold: 是否将消息加粗
        add_italic: 是否将消息改为斜体
        add_underline: 是否添加下划线
        add_delete_line: 是否添加删除线
        add_link: 可选的链接信息
        
    Returns:
        发送结果
    """
    # 查找群组
    group = find_feishu_group(group_name)
    if not group:
        return {"error": "Group not found"}
    
    # 构建消息文本
    text = ""
    
    # 添加@标记
    if at_all:
        text += TextContent.make_at_all_pattern() + "\n"
    
    if at_members:
        for member in at_members:
            member_info = find_feishu_group_member(group_name, member)
            if member_info:
                text += TextContent.make_at_someone_pattern(
                    member_info["open_id"],
                    member_info["name"],
                    "open_id"
                ) + " "
        text += "\n"
    
    # 添加格式化的消息内容
    message = text_message
    if add_bold:
        message = TextContent.make_bold_pattern(message)
    if add_italic:
        message = TextContent.make_italian_pattern(message)
    if add_underline:
        message = TextContent.make_underline_pattern(message)
    if add_delete_line:
        message = TextContent.make_delete_line_pattern(message)
    
    text += message
    
    # 添加链接
    if add_link:
        text += "\n" + TextContent.make_url_pattern(add_link["url"], add_link["text"])
    
    return bot.send_text_to_chat(group["chat_id"], text)

@mcp.tool()
def send_meeting_summary(
    group_name: str,
    title: str,
    attendees: List[str],
    content: str,
    *,
    add_code_block: Optional[Dict[str, str]] = None,  # {"language": "python", "code": "print('hello')"}
    add_markdown: Optional[str] = None,
    add_emoji: Optional[str] = None
) -> Dict:
    """
    发送会议纪要，支持sample.py中展示的富文本格式
    
    Args:
        group_name: 群组名称
        title: 会议标题
        attendees: 参会人员列表（将自动转换为@标记）
        content: 会议内容
        add_code_block: 可选的代码块
        add_markdown: 可选的Markdown内容
        add_emoji: 可选的emoji表情
        
    Returns:
        发送结果
    """
    # 查找群组
    group = find_feishu_group(group_name)
    if not group:
        return {"error": "Group not found"}
    
    # 创建富文本消息
    post = PostContent(title)
    
    # 添加参会人员
    post.add_content_in_new_line(
        post.make_text_content("参会人员：", ["bold"])
    )
    
    # 添加@标记
    for attendee in attendees:
        member_info = find_feishu_group_member(group_name, attendee)
        if member_info:
            post.add_content_in_line(
                post.make_at_content(member_info["open_id"], ["italic"])
            )
    
    # 添加分隔线
    post.add_content_in_new_line(post.make_hr_content())
    
    # 添加会议内容
    if add_markdown:
        post.add_content_in_new_line(
            post.make_markdown_content(add_markdown)
        )
    else:
        post.add_content_in_new_line(
            post.make_text_content(content)
        )
    
    # 添加表情
    if add_emoji:
        post.add_content_in_new_line(
            post.make_emoji_content(add_emoji)
        )
    
    # 添加代码块
    if add_code_block:
        post.add_content_in_new_line(
            post.make_code_block_content(
                add_code_block["language"],
                add_code_block["code"]
            )
        )
    
    return bot.send_post_to_chat(group["chat_id"], post.get_content())

@mcp.tool()
def send_multimedia_message(
    group_name: str,
    *,
    image_path: Optional[str] = None,
    audio_path: Optional[str] = None,
    video_path: Optional[str] = None,
    file_path: Optional[str] = None,
    message: Optional[str] = None
) -> Dict:
    """
    发送多媒体消息，支持sample.py中展示的所有媒体类型
    
    Args:
        group_name: 群组名称
        image_path: 图片路径
        audio_path: 音频路径（opus格式）
        video_path: 视频路径（mp4格式）
        file_path: 普通文件路径
        message: 可选的附加消息
        
    Returns:
        发送结果，包含所有发送操作的结果
    """
    # 查找群组
    group = find_feishu_group(group_name)
    if not group:
        return {"error": "Group not found"}
    
    results = {}
    
    # 发送消息（如果有）
    if message:
        results["message"] = bot.send_text_to_chat(group["chat_id"], message)
    
    # 发送图片
    if image_path:
        image_key = bot.upload_image(image_path)
        if image_key:
            results["image"] = bot.send_image_to_chat(group["chat_id"], image_key)
        else:
            results["image"] = {"error": "Image upload failed"}
    
    # 发送音频
    if audio_path:
        audio_key = bot.upload_file(audio_path, "opus")
        if audio_key:
            results["audio"] = bot.send_audio_to_chat(group["chat_id"], audio_key)
        else:
            results["audio"] = {"error": "Audio upload failed"}
    
    # 发送视频
    if video_path:
        video_key = bot.upload_file(video_path, "mp4")
        if video_key:
            results["video"] = bot.send_media_to_chat(group["chat_id"], video_key)
        else:
            results["video"] = {"error": "Video upload failed"}
    
    # 发送文件
    if file_path:
        file_key = bot.upload_file(file_path, "stream")
        if file_key:
            results["file"] = bot.send_file_to_chat(group["chat_id"], file_key)
        else:
            results["file"] = {"error": "File upload failed"}
    
    return results

@mcp.tool()
def share_group_and_user(
    source_group_name: str,
    target_group_name: str,
    user_mobile: str = "",
    user_email: str = ""
) -> Dict:
    """
    分享群组和用户信息，支持sample.py中展示的分享功能
    
    Args:
        source_group_name: 要分享的源群组名称
        target_group_name: 目标群组名称
        user_mobile: 可选的用户手机号（用于分享用户）
        user_email: 可选的用户邮箱（用于分享用户）
        
    Returns:
        分享结果
    """
    results = {}
    
    # 查找源群组
    source_group = find_feishu_group(source_group_name)
    if not source_group:
        return {"error": "Source group not found"}
    
    # 查找目标群组
    target_group = find_feishu_group(target_group_name)
    if not target_group:
        return {"error": "Target group not found"}
    
    # 分享群组
    results["share_chat"] = bot.send_shared_chat_to_chat(
        target_group["chat_id"],
        source_group["chat_id"]
    )
    
    # 分享用户（如果指定了用户）
    if user_mobile or user_email:
        user = find_feishu_user(user_mobile, user_email)
        if user:
            results["share_user"] = bot.send_shared_user_to_chat(
                target_group["chat_id"],
                user["user_id"]
            )
        else:
            results["share_user"] = {"error": "User not found"}
    
    return results

if __name__ == "__main__":
    mcp.run() 