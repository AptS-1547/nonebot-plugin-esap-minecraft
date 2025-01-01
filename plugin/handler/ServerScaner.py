"""
Copyright 2022-2024 The ESAP Project. All rights reserved.
Use of this source code is governed by a GPL-3.0 license that can be found in the LICENSE file.

服务器扫描器类 ServerScaner.py 2024-10-21
Author: AptS:1547

ServerScaner类用于处理Minecraft服务器的定时扫描，提供了以下方法：
__init__: 初始化
bound_bot: 绑定机器人对象
run_every_two_minutes: 每两分钟运行一次扫描任务
start_scaner: 启动服务器扫描器
stop_scaner: 停止服务器扫描器
"""

from nonebot import require, logger                                           #pylint: disable=missing-module-docstring, invalid-name
from nonebot.adapters import Bot
from nonebot_plugin_apscheduler import scheduler as nb_scheduler
from .ConfigHandler import Config                                             #pylint: disable=relative-beyond-top-level
from .MinecraftServer import MinecraftServer as mc_MinecraftServer            #pylint: disable=relative-beyond-top-level

require("nonebot_plugin_apscheduler")

class ServerScaner:
    """服务器扫描器类"""
    def __init__(self, plugin_config: Config, bot: Bot | None = None) -> None:
        """
        初始化 ServerScaner 类
        :param pluginConfig: 插件配置对象
        :param bot: 机器人对象
        """
        self.scan_server_not_connect = []  # TODO:这里不应该存储群号，应该存储服务器地址
        self.plugin_config = plugin_config  # 插件配置对象
        self.bot = bot  # 机器人对象

        self.add_scan_server()

    def add_scan_server(self) -> None:
        """ 读取需要扫描的服务器配置，将其加入到扫描列表中"""
        self.scan_server_list = []
        for groupid, value in self.plugin_config.mc_qqgroup_default_server.items():                     # TODO:这什么鬼变量啊，为什么下标是群号dict里面也放一个群号？你tm当时脑残了啊？
            if isinstance(groupid, int) and value["need_scan"] and value["server_address"]:
                value["groupID"] = str(groupid)
                self.scan_server_list.append(value)

    def bound_bot(self, bot: Bot) -> None:
        """
        绑定机器人对象
        :param bot: 机器人对象
        """
        self.bot = bot

    async def run_every_two_minutes(self, _: int, arg2: list, arg3: Bot) -> None:
        """
        每两分钟运行一次的任务
        :param arg1: 参数1
        :param arg2: 服务器配置列表
        :param arg3: 机器人对象
        """
        for scan_config in arg2:
            mc_server = mc_MinecraftServer(scan_config["server_address"], self.plugin_config, scan_config["groupID"])
            ping_server_return = await mc_server.ping_server()
            if isinstance(ping_server_return, str):  # 连接不上的反馈
                if scan_config["groupID"] not in self.scan_server_not_connect:
                    self.scan_server_not_connect.append(scan_config["groupID"])
                    logger.info(f"服务器连接已丢失，错误信息：\n{ping_server_return}")
                    await arg3.send_group_msg(group_id=scan_config["groupID"], message=f"⚠️服务器{scan_config["server_address"]}连接已丢失")
            else:
                if scan_config["groupID"] in self.scan_server_not_connect:
                    self.scan_server_not_connect.remove(scan_config["groupID"])
                    logger.info("服务器连接已恢复")
                    await arg3.send_group_msg(group_id=scan_config["groupID"], message=f"✅服务器{scan_config["server_address"]}连接已恢复")

            del mc_server

    def start_scaner(self) -> bool:
        """
        启动服务器扫描器
        :return: 是否成功启动
        """
        if not self.scan_server_list:
            return False

        nb_scheduler.add_job(
            self.run_every_two_minutes, "interval", minutes=self.plugin_config.mc_ping_server_interval_second, id="job_scan_server", args=[1], kwargs={"arg2": self.scan_server_list, "arg3": self.bot}
        )
        return True

    def stop_scaner(self, deletebot: bool) -> bool:
        """
        停止服务器扫描器
        :return: 是否成功停止
        """
        nb_scheduler.remove_all_jobs()
        if deletebot:
            self.bot = None
        return True
