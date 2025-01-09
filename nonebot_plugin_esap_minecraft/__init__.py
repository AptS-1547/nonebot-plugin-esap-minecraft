"""
Copyright 2022-2024 The ESAP Project. All rights reserved.
Use of this source code is governed by a GPL-3.0 license that can be found in the LICENSE file.

Minecraft插件主文件 __init__.py 2024-10-21
Author: AptS:1547

Minecraft插件主文件，用于处理Minecraft服务器的Ping查询等功能
"""

import base64
import asyncio
from io import BytesIO
from pathlib import Path

import nonebot
from nonebot import on_command, on_message, get_driver, logger
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message, Bot
from nonebot.rule import to_me


from nonebot.adapters.onebot.v11.event import GroupMessageEvent as ob_event_GroupMessageEvent
from nonebot.adapters.onebot.v11.event import PrivateMessageEvent as ob_event_PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as ob_message_MessageSegment
from nonebot.adapters.onebot.v11.message import Message as ob_message_Message

from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

from .handler.MessageDefine import MessageDefine
from .handler.ConfigHandler import ConfigHandler, Config, convert_string
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
ConfigHandler.initialize()
if ConfigHandler.error != "":
    logger.error(ConfigHandler.error)
else:
    ConfigHandler.config = ConfigHandler.config
    logger.info("[epmc_minecraft_bot] 配置文件加载成功")


# 参数分割函数
def split_args(args: str) -> list[str]:
    """参数分割函数"""
    return_list = []
    if globalConfig.command_sep is not None:
        str_args = ""
        for i in globalConfig.command_sep:
            str_args += args.replace(i, " ")
        return_list = args.split(" ")
    else:
        return_list = args.split(" " and ".")
    return return_list

# 回复前先发送一个贴纸


async def before_handle_message(bot: Bot, message_id: str):
    """发送一个贴纸"""
    await asyncio.sleep(0.5)
    await bot.call_api("set_msg_emoji_like", message_id=message_id, emoji_id=181, set=True)


# Bot连接事件，用ServerScaner类的start_scaner方法启动定时任务
driver = get_driver()
mcServerScaner = mc_ServerScaner(ConfigHandler.config)


@driver.on_bot_connect
async def _(bot: Bot):
    mcServerScaner.bound_bot(bot)  # pylint: disable=expression-not-assigned
    if bot.adapter.get_name() != "OneBot V11":
        logger.info("当前插件仅支持OneBot V11协议")
    else:
        if ConfigHandler.error != "":
            logger.error(ConfigHandler.error)
            [await bot.send_private_msg(user_id=superuser, message=ConfigHandler.error) for superuser in nonebot.get_driver().config.superusers]  # pylint: disable=expression-not-assigned
        elif not ConfigHandler.config.mc_serverscaner_enable or not ConfigHandler.config.enable:
            ConfigHandler.config.mc_serverscaner_status = False
            logger.info(MessageDefine.bot_is_connected_without_scanner)
            [await bot.send_private_msg(user_id=superuser, message=MessageDefine.bot_is_connected_without_scanner) for superuser in nonebot.get_driver().config.superusers]  # pylint: disable=expression-not-assigned
        elif mcServerScaner.start_scaner():
            logger.info(MessageDefine.bot_is_connected_with_scanner)
            ConfigHandler.config.mc_serverscaner_status = True
            # [await bot.send_private_msg(user_id=superuser, message=MessageDefine.bot_is_connected_with_scanner) for superuser in nonebot.get_driver().config.superusers]  # pylint: disable=expression-not-assigned
        else:
            logger.info(MessageDefine.bot_is_connected_without_server)
            ConfigHandler.config.mc_serverscaner_status = False
            # [await bot.send_private_msg(user_id=superuser, message=MessageDefine.bot_is_connected_without_server) for superuser in nonebot.get_driver().config.superusers]  # pylint: disable=expression-not-assigned

# Bot断开连接事件，用ServerScaner类的stopScaner方法停止定时任务


@driver.on_bot_disconnect
async def _():
    if mcServerScaner.stop_scaner(deletebot=True):
        ConfigHandler.config.mc_serverscaner_status = False
        logger.info(MessageDefine.bot_is_disconnected_with_scanner)
    else:
        logger.warning(MessageDefine.bot_is_disconnected_without_scanner)


# 命令 ~help 展开命令列表
HelpCommand = on_command("help", priority=0, block=True)


@HelpCommand.handle()
async def _(event: ob_event_GroupMessageEvent, bot: Bot):  # Q群消息事件响应
    if event.group_id in ConfigHandler.config.mc_qqgroup_id and ConfigHandler.config.enable:  # 确认Q群在获准名单内
        await before_handle_message(bot, str(event.message_id))
        await asyncio.sleep(0.5)  # 延时0.5s 防止风控
        await HelpCommand.finish(MessageDefine.group_help_message, at_sender=True)

# 对只@机器人的消息进行回复
AtBotCommand = on_message(rule=to_me(), priority=50, block=True)


@AtBotCommand.handle()
async def _(event: ob_event_GroupMessageEvent, bot: Bot):  # Q群消息事件响应
    if event.group_id in ConfigHandler.config.mc_qqgroup_id and ConfigHandler.config.enable:  # 确认Q群在获准名单内
        await before_handle_message(bot, str(event.message_id))
        await asyncio.sleep(0.5)  # 延时0.5s 防止风控
        await HelpCommand.finish(MessageDefine.group_help_message, at_sender=True)

# 命令 ~ping 执行Ping命令
PingCommand = on_command("ping", priority=0, block=True)


@PingCommand.handle()
async def _(event: ob_event_GroupMessageEvent, bot: Bot, args: Message = CommandArg()):
    if event.group_id in ConfigHandler.config.mc_qqgroup_id and ConfigHandler.config.enable:  # 确认Q群在获准名单内
        await before_handle_message(bot, str(event.message_id))

        mc_server = mc_MinecraftServer(
            args.extract_plain_text(), ConfigHandler.config, event.group_id)

        ping_server_return = await mc_server.ping_server()
        if isinstance(ping_server_return, str):          # 如果返回的是字符串，说明出现了错误
            await PingCommand.finish(ping_server_return, at_sender=True)

        final_image_byte = BytesIO()
        final_image_image = mc_PictureHandler(
            mc_server.server_information).make_picture()
        final_image_image.save(final_image_byte, format="JPEG")
        final_image_base64str = "base64://" + \
            base64.b64encode(final_image_byte.getvalue()).decode('utf-8')

        return_message = ob_message_Message()
        return_message += ob_message_MessageSegment.image(
            final_image_base64str)
        del mc_server, final_image_image, final_image_byte, final_image_base64str
        await asyncio.sleep(0.5)
        await PingCommand.finish(message=return_message, at_sender=True)

# 命令 ~vwl 执行VelocityWhiteList命令
VwlCommand = on_command("vwl", priority=0, block=True)

# TODO: 应该设计为私聊/群聊可以使用这个命令，但是私聊需要保存服务器管理员的QQ号才能确定在修改哪个服务器的白名单


@VwlCommand.handle()
async def _(event: ob_event_GroupMessageEvent, cmd: Message = CommandArg()):
    args = split_args(cmd.extract_plain_text())  # 分割参数
    if event.group_id in ConfigHandler.config.mc_qqgroup_id:
        return_message = await handle_vwl_command(args, event.group_id)
        await asyncio.sleep(0.5)  # 延时0.5s 防止风控
        await VwlCommand.finish(return_message)
    return False


# 命令 ~conf 执行配置命令
ConfCommand = on_command(
    "conf", priority=0, block=True, permission=GROUP_OWNER | GROUP_ADMIN | SUPERUSER)


@ConfCommand.handle()
async def _(event: ob_event_GroupMessageEvent | ob_event_PrivateMessageEvent, bot: Bot, cmd: Message = CommandArg()):  # Q群消息事件响应
    args = cmd.extract_plain_text().split(" ")  # 分割参数
    return_message = ""
    if isinstance(event, ob_event_GroupMessageEvent) and event.group_id in ConfigHandler.config.mc_qqgroup_id:
        await before_handle_message(bot, str(event.message_id))
        return_message = await handle_groupadmin_conf_command(args, event.group_id)
    elif isinstance(event, ob_event_PrivateMessageEvent) and str(event.user_id) in globalConfig.superusers:
        await before_handle_message(bot, str(event.message_id))
        return_message = await handle_superuser_conf_command(args)
    else:
        return False
    await asyncio.sleep(0.5)  # 延时0.5s 防止风控
    await ConfCommand.finish(return_message)

# 命令 ~about 显示插件信息
AboutCommand = on_command("about", priority=0, block=True)


@AboutCommand.handle()
async def _(event: ob_event_GroupMessageEvent, bot: Bot):  # Q群消息事件响应
    if event.group_id in ConfigHandler.config.mc_qqgroup_id and ConfigHandler.config.enable:  # 确认Q群在获准名单内
        await before_handle_message(bot, str(event.message_id))
        await asyncio.sleep(0.5)  # 延时0.5s 防止风控
        await AboutCommand.finish(ob_message_MessageSegment.image(PictureDefine.about), at_sender=True)


async def reload_plugin_config() -> str:
    """重载配置文件"""
    ConfigHandler.reload_config()
    mcServerScaner.plugin_config = ConfigHandler.config
    if isinstance(ConfigHandler, str):
        return_message = ConfigHandler.error
    elif mcServerScaner.stop_scaner(deletebot=False):
        mcServerScaner.add_scan_server()
        ConfigHandler.config.mc_serverscaner_status = False
        if not ConfigHandler.config.enable or not ConfigHandler.config.mc_serverscaner_enable:
            logger.warning(MessageDefine.logger_reload_without_scanner)
            return_message = MessageDefine.logger_reload_without_scanner
        elif mcServerScaner.start_scaner():
            ConfigHandler.config.mc_serverscaner_status = True
            logger.info(MessageDefine.logger_reload_with_scanner)
            return_message = MessageDefine.logger_reload_with_scanner
        else:
            logger.warning(MessageDefine.logger_reload_without_server)
            return_message = MessageDefine.logger_reload_without_server
    else:
        logger.warning(MessageDefine.logger_reload_sth_wrong)
        return_message = MessageDefine.logger_reload_sth_wrong
    return return_message


# 处理~vwl命令调用


async def handle_vwl_command(args: list[str], groupid: int = 0) -> str:
    """处理~vwl命令调用"""
    match args[0]:
        case "help":
            return_message = MessageDefine.public_vwl_command_help + "\n Under Construction"

        case "add":
            pass

        case "del":
            pass

        case "list":
            pass

        case _:
            return_message = MessageDefine.args_do_not_exist

    return return_message

# 处理~conf GroupAdmin命令调用


async def handle_groupadmin_conf_command(args: list[str], groupid: int = 0) -> str:
    """处理~conf GroupAdmin命令调用"""

    match args[0]:
        case "status":
            return_message = MessageDefine.command_groupadmin_status_message(
                ConfigHandler.config.enable, ConfigHandler.config.mc_serverscaner_status)
        case "help":
            return_message = MessageDefine.public_groupadmin_command_help

        case "get":
            return_message = ConfigHandler.get_config(args, groupid)

        case "set":
            return_message = ConfigHandler.set_config(args, groupid)
            await reload_plugin_config()

        case _:
            return_message = MessageDefine.args_do_not_exist

    return return_message

# 处理~conf Superuser命令调用


async def handle_superuser_conf_command(args: list[str]) -> str:
    """处理~conf Superuser命令调用"""
    match args[0]:
        case "qqgroup":
            try:
                value = convert_string(args[2])
                if len(args) != 3 or args[1] not in ["add", "del"] or not isinstance(value, int):
                    return_message = MessageDefine.args_error_qqgroup_command
                elif args[1] == "add":
                    if value in ConfigHandler.config.mc_qqgroup_id and value in ConfigHandler.config.mc_qqgroup_default_server:
                        return_message = MessageDefine.command_qqgroup_add_exist
                    else:
                        if value not in ConfigHandler.config.mc_qqgroup_id:
                            # TODO:这什么鬼变量啊，为什么下标是群号dict里面也放一个群号？你tm当时脑残了啊？
                            ConfigHandler.config.mc_qqgroup_id.append(value)
                        if value not in ConfigHandler.config.mc_qqgroup_default_server:
                            server_config = {'server_address': None, 'default_icon_type': 'Server Icon',
                                             'default_icon': '', 'need_scan': False, 'groupID': value}
                            ConfigHandler.config.mc_qqgroup_default_server[value] = server_config
                            del server_config
                        ConfigHandler.save_config()
                        await reload_plugin_config()
                        return_message = MessageDefine.command_qqgroup_success("添加", value)
                elif args[1] == "del":
                    if value in ConfigHandler.config.mc_qqgroup_id or value in ConfigHandler.config.mc_qqgroup_default_server:
                        if value in ConfigHandler.config.mc_qqgroup_id:
                            ConfigHandler.config.mc_qqgroup_id.remove(value)
                        if value in ConfigHandler.config.mc_qqgroup_default_server:
                            del ConfigHandler.config.mc_qqgroup_default_server[value]
                        ConfigHandler.save_config()
                        await reload_plugin_config()
                        return_message = MessageDefine.command_qqgroup_success("删除", value)
                    else:
                        return_message = MessageDefine.command_qqgroup_del_not_exist
            except IndexError:
                return_message = MessageDefine.conf_get_args_is_none
            except (ValueError, SyntaxError):
                return_message = MessageDefine.args_error_qqgroup_command

        case "status":
            if ConfigHandler.config.enable:
                return_message = MessageDefine.command_superuser_status_message(ConfigHandler.config.enable,
                                                                                  ConfigHandler.config.mc_serverscaner_status, mcServerScaner.scan_server_list)
            else:
                return_message = MessageDefine.plugin_is_not_enable

        case "reload":
            return_message = await reload_plugin_config()

        case "help":
            return_message = MessageDefine.private_superuser_command_help

        case "scan":
            if len(args) != 2 or args[1] not in ["start", "stop"]:
                return_message = MessageDefine.args_error_scan_command
            elif isinstance(ConfigHandler, str):
                return_message = ConfigHandler
            elif ConfigHandler.config.enable is False or ConfigHandler.config.mc_serverscaner_enable is False:
                return_message = MessageDefine.plugin_is_not_enable
            elif args[1] == "start" and not ConfigHandler.config.mc_serverscaner_status:
                mcServerScaner.start_scaner()
                ConfigHandler.config.mc_serverscaner_status = True
                return_message = MessageDefine.scanner_is_running
            elif args[1] == "stop" and ConfigHandler.config.mc_serverscaner_status:
                mcServerScaner.stop_scaner(deletebot=False)
                ConfigHandler.config.mc_serverscaner_status = False
                return_message = MessageDefine.scanner_is_stopped
            elif args[1] == "start" and ConfigHandler.config.mc_serverscaner_status:
                return_message = MessageDefine.scanner_already_running
            elif args[1] == "stop" and not ConfigHandler.config.mc_serverscaner_status:
                return_message = MessageDefine.scanner_already_stopped

        case "get":
            return_message = ConfigHandler.get_config(args, 0)

        case "set":
            return_message = ConfigHandler.set_config(args, 0)
            await reload_plugin_config()

        case _:
            return_message = MessageDefine.args_do_not_exist

    return return_message
