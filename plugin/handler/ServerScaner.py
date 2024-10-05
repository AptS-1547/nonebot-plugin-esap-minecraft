from nonebot import require, logger
from nonebot.adapters import Bot

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler as nb_scheduler
from esap_minecraft_bot.plugins.esap_minecraft_bot.config import Config
from esap_minecraft_bot.plugins.esap_minecraft_bot.handler.MinecraftServer import MinecraftServer as mc_MinecraftServer

class ServerScaner:

    def __init__(self, pluginConfig: Config, bot: Bot | None) -> None:
        """
        初始化 ServerScaner 类
        :param pluginConfig: 插件配置对象
        :param bot: 机器人对象
        """
        self.scanServerList = [] # 需要扫描的服务器列表
        self.scanServerNotConnect = [] # 无法连接的服务器列表
        self.pluginConfig = pluginConfig # 插件配置对象
        self.bot = bot # 机器人对象
        # 读取需要扫描的服务器配置，将其加入到扫描列表中
        for groupID, value in pluginConfig.mc_qqgroup_default_server.items():
            if groupID.isdecimal() and value["need_scan"].lower() == "true":
                value["groupID"] = groupID
                self.scanServerList.append(value)

    def boundBot(self, bot: Bot) -> None:
        """
        绑定机器人对象
        :param bot: 机器人对象
        """
        self.bot = bot

    async def run_every_two_minutes(self, arg1: int, arg2: list, arg3: Bot) -> None:
        """
        每两分钟运行一次的任务
        :param arg1: 参数1
        :param arg2: 服务器配置列表
        :param arg3: 机器人对象
        """
        for scan_config in arg2:
            mcServer = mc_MinecraftServer(scan_config["serverAddress"], self.pluginConfig, scan_config["groupID"])
            pingServerReturn = await mcServer.ping_server()
            if isinstance(pingServerReturn, str):                #连接不上的反馈
                if scan_config["groupID"] not in self.scanServerNotConnect:
                    self.scanServerNotConnect.append(scan_config["groupID"])
                    logger.info(f"服务器连接已丢失，错误信息：\n{pingServerReturn}")
                    await arg3.send_group_msg(group_id=scan_config["groupID"], message="⚠️服务器连接已丢失，错误信息：\n" + pingServerReturn)
            else:
                if scan_config["groupID"] in self.scanServerNotConnect:
                    self.scanServerNotConnect.remove(scan_config["groupID"])
                    logger.info("服务器连接已恢复")
                    await arg3.send_group_msg(group_id=scan_config["groupID"], message="✅服务器连接已恢复")

            del mcServer
            

    def startScaner(self) -> bool:
        """
        启动服务器扫描器
        :return: 是否成功启动
        """
        if self.scanServerList == []:
            return(False)

        nb_scheduler.add_job(
            self.run_every_two_minutes, "interval", seconds=2, id="job_scan_server", args=[1], kwargs={"arg2": self.scanServerList, "arg3": self.bot}
        )
        return(True)
    
    def stopScaner(self) -> bool:
        """
        停止服务器扫描器
        :return: 是否成功停止
        """
        nb_scheduler.remove_all_jobs()
        self.bot = None
        return(True)
        