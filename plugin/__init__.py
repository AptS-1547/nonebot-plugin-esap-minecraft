from queue import Full
from nonebot import get_plugin_config, on_command
from nonebot.plugin import PluginMetadata

from nonebot.params import CommandArg
from nonebot.adapters import Message

from .config import Config

from nonebot.adapters.onebot.v11.event import GroupMessageEvent as ob_event_GroupMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as ob_message_MessageSegment
from nonebot.adapters.onebot.v11.message import Message as ob_message_Message

from esap_minecraft_bot.plugins.esap_minecraft_bot.handler.PingHandler import PingHandler as mc_PingHandler

import asyncio

__plugin_meta__ = PluginMetadata(
    name="esap_minecraft_bot",
    description="",
    usage="",
    config=Config,
)

pluginConfig = get_plugin_config(Config)

mc_list_command = on_command("list", priority=0, block=True)           #命令 ~list 展开命令列表

@mc_list_command.handle()
async def _(event: ob_event_GroupMessageEvent):      #Q群消息事件响应
    if event.group_id in pluginConfig.mc_qqgroup_id:                  #确认Q群在获准名单内
        await asyncio.sleep(0.5)                                       #延时0.5s 防止风控
        await mc_list_command.finish("喵喵ap~ 人机菜单\n--------------------\n✅ ~list 展开本菜单\n⚠️ ~ping <服务器地址> 查询服务器状态\n❌ ~vwl 白名单管理")

mc_ping_command = on_command("ping", priority=0, block=True)

@mc_ping_command.handle()
async def _(event_group: ob_event_GroupMessageEvent, args: Message = CommandArg()):
    if event_group.group_id in pluginConfig.mc_qqgroup_id:

        PingHandler = mc_PingHandler(args.extract_plain_text(), pluginConfig, event_group.group_id)

        pingServerReturn = await PingHandler.ping_server()
        if isinstance(pingServerReturn, str):
            await mc_ping_command.finish(pingServerReturn, at_sender=True)
        
        returnMessage = ob_message_Message()
        returnMessage += ob_message_MessageSegment.image(PingHandler.Icon)
        returnMessage += (f"服务器地址：{PingHandler.serverAddress}，版本为 {PingHandler.serverType} {PingHandler.version}\nMOTD：{PingHandler.motdFinal}\n\n当前有{PingHandler.playerNumber}名玩家在线\nPing请求所用时间为 {round(PingHandler.pingLatency,2)}ms")
        await asyncio.sleep(1)
        await mc_ping_command.finish(message=returnMessage, at_sender=True)
