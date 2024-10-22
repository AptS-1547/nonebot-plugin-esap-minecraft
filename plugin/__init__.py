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

from .handler.MessageDefine import MessageDefine
from .handler.ConfigHandler import ConfigHandler, Config
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
if pluginConfig.error != "":
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
        if pluginConfig.error != "":
            logger.error(pluginConfig.error)
            [await bot.send_private_msg(user_id=superuser, message=pluginConfig.error) for superuser in nonebot.get_driver().config.superusers]                               #pylint: disable=expression-not-assigned
        elif not pluginConfig.config.mc_serverscaner_enable or not pluginConfig.config.enable:
            pluginConfig.config.mc_serverscaner_status = False
            logger.info(MessageDefine.bot_is_connected_without_scanner)
            [await bot.send_private_msg(user_id=superuser, message=MessageDefine.bot_is_connected_without_scanner) for superuser in nonebot.get_driver().config.superusers]   #pylint: disable=expression-not-assigned
        elif mcServerScaner.start_scaner():
            logger.info(MessageDefine.bot_is_connected_with_scanner)
            pluginConfig.config.mc_serverscaner_status = True
            [await bot.send_private_msg(user_id=superuser, message=MessageDefine.bot_is_connected_with_scanner) for superuser in nonebot.get_driver().config.superusers]      #pylint: disable=expression-not-assigned
        else:
            logger.info(MessageDefine.bot_is_connected_without_server)
            pluginConfig.config.mc_serverscaner_status = False
            [await bot.send_private_msg(user_id=superuser, message=MessageDefine.bot_is_connected_without_server) for superuser in nonebot.get_driver().config.superusers]    #pylint: disable=expression-not-assigned

# Bot断开连接事件，用ServerScaner类的stopScaner方法停止定时任务
@driver.on_bot_disconnect
async def _():
    if mcServerScaner.stop_scaner(deletebot=True):
        pluginConfig.config.mc_serverscaner_status = False
        logger.info(MessageDefine.bot_is_disconnected_with_scanner)
    else:
        logger.warning(MessageDefine.bot_is_disconnected_without_scanner)

# 命令 ~conf 执行配置命令
ConfCommand = on_command(
    "conf", priority=0, block=True, permission=GROUP_OWNER | GROUP_ADMIN | SUPERUSER)

@ConfCommand.handle()
async def _(event: ob_event_GroupMessageEvent | ob_event_PrivateMessageEvent, cmd: Message = CommandArg()):  # Q群消息事件响应
    args = cmd.extract_plain_text().split(" ")  # 分割参数
    return_message = ""
    if isinstance(event, ob_event_GroupMessageEvent) and event.group_id in pluginConfig.config.mc_qqgroup_id:
        return_message = await handle_groupadmin_conf_command(args, pluginConfig)
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
        await HelpCommand.finish(MessageDefine.group_help_message, at_sender=True)

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

async def reload_plugin_config() -> str:
    """重载配置文件"""
    pluginConfig.reload_config()
    mcServerScaner.plugin_config = pluginConfig.config
    if isinstance(pluginConfig, str):
        return_message = pluginConfig.error
    elif mcServerScaner.stop_scaner(deletebot=False):
        mcServerScaner.add_scan_server()
        pluginConfig.config.mc_serverscaner_status = False
        if not pluginConfig.config.enable or not pluginConfig.config.mc_serverscaner_enable:
            logger.warning(MessageDefine.logger_reload_without_scanner)
            return_message = MessageDefine.logger_reload_without_scanner
        elif mcServerScaner.start_scaner():
            pluginConfig.config.mc_serverscaner_status = True
            logger.info(MessageDefine.logger_reload_with_scanner)
            return_message = MessageDefine.logger_reload_with_scanner
        else:
            logger.warning(MessageDefine.logger_reload_without_server)
            return_message = MessageDefine.logger_reload_without_server
    else:
        logger.warning(MessageDefine.logger_reload_sth_wrong)
        return_message = MessageDefine.logger_reload_sth_wrong
    return return_message

# 处理~conf GroupAdmin命令调用
async def handle_groupadmin_conf_command(args: list[str], plugin_config: ConfigHandler) -> str:
    """处理~conf GroupAdmin命令调用"""
    config_list = ["mc_qqgroup_default_server"]
    match args[0]:
        case "status":
            return_message = MessageDefine().command_groupadmin_status_message(plugin_config.config.enable, plugin_config.config.mc_serverscaner_status)
        case "help":
            return_message = MessageDefine.public_groupadmin_command_help

        case "get":
            pass

        case "set":
            pass

        case _:
            return_message = MessageDefine.args_do_not_exist

    return return_message

# 处理~conf Superuser命令调用

async def handle_superuser_conf_command(args: list[str], plugin_config: ConfigHandler) -> str:
    """处理~conf Superuser命令调用"""
    config_list = ["enable", "mc_qqgroup_id", "mc_global_default_server", "mc_global_default_icon", "mc_ping_server_interval_second", "mc_qqgroup_default_server", "mc_serverscaner_enable"]
    match args[0]:
        case "status":
            if plugin_config.config.enable:
                return_message = MessageDefine().command_superuser_status_message(plugin_config.config.enable, plugin_config.config.mc_serverscaner_status, mcServerScaner.scan_server_list)
            else:
                return_message = MessageDefine.plugin_is_not_enable

        case "reload":
            return_message = await reload_plugin_config()

        case "help":
            return_message = MessageDefine.private_superuser_command_help

        case "scan":
            if len(args) != 2 or args[1] not in ["start", "stop"]:
                return_message = MessageDefine.args_error_scan_command
            elif isinstance(plugin_config, str):
                return_message = plugin_config
            elif plugin_config.config.enable is False or plugin_config.config.mc_serverscaner_enable is False:
                return_message = MessageDefine.plugin_is_not_enable
            elif args[1] == "start" and not plugin_config.config.mc_serverscaner_status:
                mcServerScaner.start_scaner()
                plugin_config.config.mc_serverscaner_status = True
                return_message = MessageDefine.scanner_is_running
            elif args[1] == "stop" and plugin_config.config.mc_serverscaner_status:
                mcServerScaner.stop_scaner(deletebot=False)
                plugin_config.config.mc_serverscaner_status = False
                return_message = MessageDefine.scanner_is_stopped
            elif args[1] == "start" and plugin_config.config.mc_serverscaner_status:
                return_message = MessageDefine.scanner_already_running
            elif args[1] == "stop" and not plugin_config.config.mc_serverscaner_status:
                return_message = MessageDefine.scanner_already_stopped
        
        case "get":
            if len(args) != 2 or args[1] not in config_list:
                return_message = MessageDefine.args_error_get_command
            else:
                return_message = str(plugin_config.config.__getattribute__(args[1]))
                if return_message == "":
                    return_message = MessageDefine.conf_is_none

        case "set":
            value = convert_string(args[2])
            if len(args) != 3 or args[1] not in config_list or value == -1:
                return_message = MessageDefine.args_error_set_command
            else:
                plugin_config.config.__setattr__(args[1], value)
                plugin_config.save_config()
                return_message = MessageDefine().command_set_sueccess(args[1], args[2])
                await reload_plugin_config()

        case _:
            return_message = MessageDefine.args_do_not_exist

    return return_message

def convert_string(value: str) -> bool | int | float | str | dict:
    """尝试将字符串转换为对应的类型"""
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return -1