"""
Copyright 2022-2024 The ESAP Project. All rights reserved.
Use of this source code is governed by a GPL-3.0 license that can be found in the LICENSE file.

Minecraft插件主文件 __init__.py 2024-10-21
Author: AptS:1547

Minecraft插件主文件，用于处理Minecraft服务器的Ping查询等功能
"""

import base64, asyncio, ast                            #pylint: disable=multiple-imports
from io import BytesIO
from pathlib import Path

import nonebot
from nonebot import on_command, get_driver, logger
from nonebot.params import CommandArg, Command
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message, Bot

from nonebot.adapters.onebot.v11.event import GroupMessageEvent as ob_event_GroupMessageEvent
from nonebot.adapters.onebot.v11.event import PrivateMessageEvent as ob_event_PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as ob_message_MessageSegment
from nonebot.adapters.onebot.v11.message import Message as ob_message_Message

from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

from .handler.ConfigHandler import Config, ConfigHandler
from .handler.MinecraftServer import MinecraftServer as mc_MinecraftServer
from .handler.ServerScaner import ServerScaner as mc_ServerScaner
from .handler.PictureHandler import PictureHandler as mc_PictureHandler
from .handler.PictureDefine import PictureDefine

# 加载嵌套插件
sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)


# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="esap_minecraft_bot",
    description="简单的Minecraft插件，支持Ping查询等实用功能",
    usage="",
    supported_adapters={"nonebot.adapters.onebot"},
    config=Config,
)

# 获取全局配置
globalConfig = nonebot.get_driver().config

# 获取config.yml文件设置的参数
pluginConfig = ConfigHandler()
if pluginConfig.error is not None:
    logger.error(pluginConfig.error)
else:
    pluginConfig.config = pluginConfig.config
    logger.info("[epmc_minecraft_bot] 配置文件加载成功")

# Bot连接事件，用ServerScaner类的start_scaner方法启动定时任务
driver = get_driver()
mcServerScaner = mc_ServerScaner(pluginConfig.config)

@driver.on_bot_connect
async def _(bot: Bot):
    mcServerScaner.bound_bot(bot)                         #pylint: disable=expression-not-assigned
    if bot.adapter.get_name() != "OneBot V11":
        logger.error("当前插件仅支持OneBot V11协议")
    else:
        if pluginConfig.error is not None:
            [await bot.send_private_msg(user_id=superuser, message=pluginConfig.error) for superuser in nonebot.get_driver().config.superusers]   #pylint: disable=expression-not-assigned
        elif not pluginConfig.config.mc_serverscaner_enable or not pluginConfig.config.enable:
            pluginConfig.config.mc_serverscaner_enable = False
            [await bot.send_private_msg(user_id=superuser, message="机器人已上线，服务器扫描功能处于关闭状态") for superuser in nonebot.get_driver().config.superusers]   #pylint: disable=expression-not-assigned
        elif mcServerScaner.start_scaner():
            logger.info("机器人已上线，已启动对MC服务器的定时扫描")
            pluginConfig.config.mc_serverscaner_enable = True
            # [await bot.send_private_msg(user_id=superuser, message="机器人已上线，已启动对MC服务器的定时扫描") for superuser in nonebot.get_driver().config.superusers]
        else:
            logger.warning("机器人已上线，没有需要扫描的MC服务器, 请检查配置文件")
            pluginConfig.config.mc_serverscaner_enable = False
            # [await bot.send_private_msg(user_id=superuser, message="机器人已上线，没有需要扫描的MC服务器, 请检查配置文件") for superuser in nonebot.get_driver().config.superusers]

# Bot断开连接事件，用ServerScaner类的stopScaner方法停止定时任务
@driver.on_bot_disconnect
async def _():
    if isinstance(mcServerScaner, str):
        return False
    if mcServerScaner.stop_scaner(deletebot=True):
        pluginConfig.config.mc_serverscaner_enable = False
        logger.info("机器人已下线，已停止对MC服务器的定时扫描")
    else:
        logger.warning("机器人已下线，但是好像出错了，没有停止对MC服务器的定时扫描")

# 命令 ~conf 执行配置命令
ConfCommand = on_command(
    "conf", priority=0, block=True, permission=GROUP_OWNER | GROUP_ADMIN | SUPERUSER)

@ConfCommand.handle()
async def _(event: ob_event_GroupMessageEvent | ob_event_PrivateMessageEvent, cmd: Message = CommandArg()):  # Q群消息事件响应
    args = cmd.extract_plain_text().split(" ")  # 分割参数
    return_message = "未知的参数"
    if pluginConfig.config.enable is False and args[0] not in ["reload", "get", "set"]:
        return False
    elif isinstance(event, ob_event_GroupMessageEvent) and event.group_id in pluginConfig.config.mc_qqgroup_id:
        return_message = "你是那啥，管理员是吧，还没写完，我要咕咕咕，等我写完再来找我吧"
    elif isinstance(event, ob_event_PrivateMessageEvent) and str(event.user_id) in globalConfig.superusers:
        return_message = await handle_superuser_conf_command(args, pluginConfig)
    await asyncio.sleep(0.5)  # 延时0.5s 防止风控
    await ConfCommand.finish(return_message)

# 命令 ~help 展开命令列表
HelpCommand = on_command("help", priority=0, block=True)

@HelpCommand.handle()
async def _(event: ob_event_GroupMessageEvent):  # Q群消息事件响应
    if event.group_id in pluginConfig.config.mc_qqgroup_id and pluginConfig.config.enable:  # 确认Q群在获准名单内
        await asyncio.sleep(0.5)  # 延时0.5s 防止风控
        await HelpCommand.finish("喵喵ap~ 人机菜单\n--------------------\n✅ ~help 展开本菜单\n✅ ~ping <服务器地址> 查询服务器状态\n⚠️ ~vwl 白名单管理\n⚠️ ~conf 机器人设置")

# 命令 ~ping 执行Ping命令
PingCommand = on_command("ping", priority=0, block=True)


@PingCommand.handle()
async def _(event_group: ob_event_GroupMessageEvent, args: Message = CommandArg()):
    if event_group.group_id in pluginConfig.config.mc_qqgroup_id and pluginConfig.config.enable:  # 确认Q群在获准名单内

        mc_server = mc_MinecraftServer(
            args.extract_plain_text(), pluginConfig.config, event_group.group_id)

        ping_server_return = await mc_server.ping_server()
        if isinstance(ping_server_return, str):          # 如果返回的是字符串，说明出现了错误
            await PingCommand.finish(ping_server_return, at_sender=True)

        final_image_byte = BytesIO()
        final_image_image = mc_PictureHandler(
            mc_server.server_information).make_picture()
        final_image_image.save(final_image_byte, format="WEBP")
        final_image_base64str = "base64://" + \
            base64.b64encode(final_image_byte.getvalue()).decode('utf-8')

        return_message = ob_message_Message()
        return_message += ob_message_MessageSegment.image(final_image_base64str)
        del mc_server, final_image_image, final_image_byte, final_image_base64str
        await asyncio.sleep(0.5)
        await PingCommand.finish(message=return_message, at_sender=True)

# 命令 ~about 显示插件信息
AboutCommand = on_command("about", priority=0, block=True)

@AboutCommand.handle()
async def _(event: ob_event_GroupMessageEvent):  # Q群消息事件响应
    if event.group_id in pluginConfig.config.mc_qqgroup_id and pluginConfig.config.enable:  # 确认Q群在获准名单内
        await asyncio.sleep(0.5)  # 延时0.5s 防止风控
        await AboutCommand.finish(ob_message_MessageSegment.image(PictureDefine.about), at_sender=True)

async def reload_plugin_config(plugin_config: ConfigHandler) -> str:
    """重载配置文件"""
    plugin_config.reload_config()
    mcServerScaner.plugin_config = plugin_config.config
    mcServerScaner.add_scan_server()
    if isinstance(plugin_config, str):
        return_message = plugin_config
    elif mcServerScaner.stop_scaner(deletebot=True):
        plugin_config.config.mc_serverscaner_enable = False
        if plugin_config.config.enable is False:
            return_message = "重载配置文件，插件未启用，无法重启对MC服务器的定时扫描"
        elif mcServerScaner.start_scaner():
            plugin_config.config.mc_serverscaner_enable = True
            logger.info("[epmc_minecraft_bot] 重载配置文件，已重启对MC服务器的定时扫描")
            return_message = "重载配置文件，已重启对MC服务器的定时扫描"
        else:
            logger.warning("[epmc_minecraft_bot] 重载配置文件，没有需要扫描的MC服务器, 请检查配置文件")
            return_message = "重载配置文件，没有需要扫描的MC服务器, 请检查配置文件"
    else:
        logger.warning("[epmc_minecraft_bot] 重载配置文件，但是好像出错了，没有停止对MC服务器的定时扫描")
        return_message = "重载配置文件，但是好像出错了，没有停止对MC服务器的定时扫描"
    return return_message

# 处理~conf Superuser命令调用 TODO:放到单独的文件中

async def handle_superuser_conf_command(args: list[str], plugin_config: ConfigHandler) -> str:
    """处理~conf Superuser命令调用"""
    config_list = ["enable", "mc_qqgroup_id", "mc_global_default_server", "mc_global_default_icon", "mc_ping_server_interval_second", "mc_qqgroup_default_server", "mc_serverscaner_enable"]
    match args[0]:
        case "scan":
            if len(args) != 2 or args[1] not in ["start", "stop"]:
                return_message = "参数错误，正确用法：~conf scanner start/stop"
            elif isinstance(plugin_config, str):
                return_message = plugin_config
            elif plugin_config.config.enable is False:
                return_message = "插件未启用，无法操作"
            elif args[1] == "start" and not plugin_config.config.mc_serverscaner_enable:
                mcServerScaner.start_scaner()
                plugin_config.config.mc_serverscaner_enable = True
                return_message = "已启动对MC服务器的定时扫描"
            elif args[1] == "stop" and plugin_config.config.mc_serverscaner_enable:
                mcServerScaner.stop_scaner(deletebot=False)
                plugin_config.config.mc_serverscaner_enable = False
                return_message = "已停止对MC服务器的定时扫描"
            elif args[1] == "start" and plugin_config.config.mc_serverscaner_enable:
                return_message = "Scaner已经在运行了"
            elif args[1] == "stop" and not plugin_config.config.mc_serverscaner_enable:
                return_message = "Scaner已经停止了"
        
        case "get":
            if len(args) != 2 or args[1] not in config_list:
                return_message = "参数错误，正确用法：~conf get 参数名"
            else:
                return_message = str(plugin_config.config.__getattribute__(args[1]))
                if return_message == "":
                    return_message = "参数为空"

        case "set":
            value = convert_string(args[2])
            if len(args) != 3 or args[1] not in config_list or value == -1:
                return_message = "参数错误，正确用法：~conf set 参数名 参数值"
            else:
                plugin_config.config.__setattr__(args[1], value)
                # TODO: 保存配置文件
                return_message = str(type(plugin_config.config.__getattribute__(args[1])))

        case "reload":
            return_message = await reload_plugin_config(pluginConfig)

        case _:
            return_message = "未知的参数"

    return return_message

def convert_string(value: str) -> bool | int | float | str | dict:
    """尝试将字符串转换为对应的类型"""
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return -1