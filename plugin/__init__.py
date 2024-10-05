import asyncio, base64
from io import BytesIO
from typing import Tuple

import nonebot
from nonebot import get_plugin_config, on_command, get_driver, logger
from nonebot.params import CommandArg, Command
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message, Bot

from nonebot.adapters.onebot.v11.event import GroupMessageEvent as ob_event_GroupMessageEvent
from nonebot.adapters.onebot.v11.event import PrivateMessageEvent as ob_event_PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as ob_message_MessageSegment
from nonebot.adapters.onebot.v11.message import Message as ob_message_Message

from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

from .config import Config
from .handler.MinecraftServer import MinecraftServer as mc_MinecraftServer
from .handler.ServerScaner import ServerScaner as mc_ServerScaner
from .handler.PictureHandler import PictureHandler as mc_PictureHandler
from .handler.PictureDefine import PictureDefine


#插件元数据
__plugin_meta__ = PluginMetadata(
    name="esap_minecraft_bot",
    description="简单的Minecraft插件，支持Ping查询等实用功能",
    usage="",
    config=Config,
)

#获取.env文件设置的参数
pluginConfig = get_plugin_config(Config)

#Bot连接事件，用ServerScaner类的startScaner方法启动定时任务
driver = get_driver()
mcServerScaner = mc_ServerScaner(pluginConfig, None)

@driver.on_bot_connect
async def _(bot: Bot):
    if bot.adapter.get_name() != "OneBot V11": return False #定时扫描只支持OneBot V11
    if not pluginConfig.mc_serverScaner_enable: return False #如果配置文件中没有启用定时扫描则不启动
    mcServerScaner.boundBot(bot)
    if mcServerScaner.startScaner():
        logger.info("机器人已上线，已启动对MC服务器的定时扫描")
        pluginConfig.mc_serverScaner_enable = True
        [await bot.send_private_msg(user_id=superuser, message="机器人已上线，已启动对MC服务器的定时扫描") for superuser in nonebot.get_driver().config.superusers]
    else:
        logger.warning("机器人已上线，没有需要扫描的MC服务器, 请检查配置文件")
        pluginConfig.mc_serverScaner_enable = True
        [await bot.send_private_msg(user_id=superuser, message="机器人已上线，没有需要扫描的MC服务器, 请检查配置文件") for superuser in nonebot.get_driver().config.superusers]

#Bot断开连接事件，用ServerScaner类的stopScaner方法停止定时任务
@driver.on_bot_disconnect
async def _():
    if mcServerScaner.stopScaner(deletebot = True):
        pluginConfig.mc_serverScaner_enable = False
        logger.info("机器人已下线，已停止对MC服务器的定时扫描")

#命令 ~conf scan start/stop 启动/停止定时扫描
manage_mcServerScaner = on_command(("conf", "scan", "start"),priority=0,block=True,aliases={("conf", "scan", "stop")},permission=SUPERUSER)

@manage_mcServerScaner.handle()
async def _(event: ob_event_PrivateMessageEvent, cmd: Tuple[str, ...] = Command()):
    _, _, action = cmd
    if action == "start" and not pluginConfig.mc_serverScaner_enable:
        mcServerScaner.startScaner()
        pluginConfig.mc_serverScaner_enable = True
        return_message = "已启动对MC服务器的定时扫描"
    elif action == "stop" and pluginConfig.mc_serverScaner_enable:
        mcServerScaner.stopScaner(deletebot = False)
        pluginConfig.mc_serverScaner_enable = False
        return_message = "已停止对MC服务器的定时扫描"
    elif action == "start" and pluginConfig.mc_serverScaner_enable:
        return_message = "Scaner已经在运行了"
    elif action == "stop" and not pluginConfig.mc_serverScaner_enable:
        return_message = "Scaner已经停止了"

    await asyncio.sleep(0.5)
    await manage_mcServerScaner.finish(return_message)


#命令 ~list 展开命令列表
mc_list_command = on_command("help", priority=0, block=True)

@mc_list_command.handle()
async def _(event: ob_event_GroupMessageEvent):      #Q群消息事件响应
    if event.group_id in pluginConfig.mc_qqgroup_id:                  #确认Q群在获准名单内
        await asyncio.sleep(0.5)                                       #延时0.5s 防止风控
        await mc_list_command.finish("喵喵ap~ 人机菜单\n--------------------\n✅ ~help 展开本菜单\n✅ ~ping <服务器地址> 查询服务器状态\n⚠️ ~vwl 白名单管理\n⚠️ ~conf 机器人设置")

#命令 ~ping 执行Ping命令
mc_ping_command = on_command("ping", priority=0, block=True)

@mc_ping_command.handle()
async def _(event_group: ob_event_GroupMessageEvent, args: Message = CommandArg()):
    if event_group.group_id in pluginConfig.mc_qqgroup_id: #确认Q群在获准名单内

        mcServer = mc_MinecraftServer(args.extract_plain_text(), pluginConfig, event_group.group_id)

        pingServerReturn = await mcServer.ping_server()
        if isinstance(pingServerReturn, str):          # 如果返回的是字符串，说明出现了错误
            await mc_ping_command.finish(pingServerReturn, at_sender=True)
        
        FinalImage_byte = BytesIO()
        FinalImage_Image = mc_PictureHandler(mcServer.serverInformation).MakePicture()
        FinalImage_Image.save(FinalImage_byte, format="WEBP")
        FinalImage_base64str = "base64://" + base64.b64encode(FinalImage_byte.getvalue()).decode('utf-8')

        returnMessage = ob_message_Message()
        returnMessage += ob_message_MessageSegment.image(FinalImage_base64str)
        del mcServer, FinalImage_Image, FinalImage_byte, FinalImage_base64str
        await asyncio.sleep(0.5)
        await mc_ping_command.finish(message=returnMessage, at_sender=True)

#命令 ~conf 执行conf命令
mc_conf_command = on_command("conf", priority=0, block=True, permission=GROUP_OWNER | GROUP_ADMIN | SUPERUSER)

@mc_conf_command.handle()
async def _(event_group: ob_event_GroupMessageEvent, args: Message = CommandArg()):
    if event_group.group_id in pluginConfig.mc_qqgroup_id:
        returnMessage = "未完成，你是那啥对吧，管理员对吧，先爬开，我要咕咕咕"
        await asyncio.sleep(0.5)
        await mc_ping_command.finish(message=returnMessage, at_sender=False)


#命令 ~about 显示插件信息
mc_about = on_command("about", priority=0, block=True)

@mc_about.handle()
async def _(event: ob_event_GroupMessageEvent):      #Q群消息事件响应
    if event.group_id in pluginConfig.mc_qqgroup_id:                  #确认Q群在获准名单内
        await asyncio.sleep(0.5)                                       #延时0.5s 防止风控
        await mc_about.finish(ob_message_MessageSegment.image(PictureDefine.about), at_sender=True)
