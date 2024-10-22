"""
Copyright 2022-2024 The ESAP Project. All rights reserved.
Use of this source code is governed by a GPL-3.0 license that can be found in the LICENSE file.

Minecraft服务器处理类 MinecraftServer.py 2024-10-21
Author: AptS:1547

MinecraftServer类用于处理Minecraft服务器的Ping请求，提供了以下方法：
ping_server: 发送Ping请求，成功返回True，失败返回失败原因(str)
status: 同时从Java和Bedrock获取信息
handle_java: 从Java获取信息
handle_bedrock: 从Bedrock获取信息
bound_information: 绑定服务器信息
check_java_server: 判断是不是JavaServer，是的话返回JavaStatusResponse，不是返回False（会被ConnectionRefusedError捕捉）
dealing_icon: 处理服务器Icon图标
"""

import base64, asyncio, re, requests      #pylint: disable=multiple-imports

from mcstatus import BedrockServer, JavaServer
from mcstatus.status_response import BedrockStatusResponse, JavaStatusResponse

from .ConfigHandler import Config         #pylint: disable=relative-beyond-top-level
from .PictureDefine import PictureDefine  #pylint: disable=relative-beyond-top-level

class MinecraftServer:
    """Minecraft服务器处理类"""
    def __init__(self, server_address: str, plugin_config: Config, groupid: int = 0) -> None:
        #一些必要的全局变量
        self.server_address = server_address
        self.global_default_server = plugin_config.mc_global_default_server
        self.global_default_icon = plugin_config.mc_global_default_icon
        self.qqgroup_default_server = plugin_config.mc_qqgroup_default_server
        self.groupid = groupid
        self.ping_success = False
        self.server_information = {}

    async def ping_server(self) -> str | bool:
        """发送Ping请求，成功返回True，失败返回失败原因(str)"""
        if self.server_address == '':
            if (self.groupid in self.qqgroup_default_server) and ("serverAddress" in self.qqgroup_default_server[self.groupid]) and self.qqgroup_default_server[self.groupid]["serverAddress"] != "":
                self.server_address = self.qqgroup_default_server[self.groupid]["serverAddress"]
            elif self.global_default_server != '':
                self.server_address = self.global_default_server
            else:
                return("没有具体的服务器地址，无法建立连接")

        try:
            mc_response = await self.status(self.server_address)
            if isinstance(mc_response, BedrockStatusResponse):               #直接使用默认端口会出现此可能：同时开了JE和BE，会先检测出BE，但正常来说应该返回JE的数据，所以这里需要再次检测一下JE
                self.ping_success = True
                mc_response_java = self.check_java_server(self.server_address)       #对JE默认端口Ping，检测JE有无开启，如果没开启扔出ConnectionRefusedError，放到下面解决
                
                if isinstance(mc_response_java, JavaStatusResponse):         #是JE的处理
                    self.bound_information(server_type="Java", version=mc_response_java.version.name, online_players=mc_response_java.players.online, ping_latency=mc_response_java.latency, icon=self.dealing_icon(mc_response_java.icon), motd=mc_response_java.motd.parsed, max_players=mc_response_java.players.max)
                else:                                                        #是BE的处理
                    self.bound_information(server_type="Bedrock", version=mc_response.version.name, online_players=mc_response.players.online, ping_latency=mc_response.latency, icon=self.dealing_icon(), motd=mc_response.motd.parsed, max_players=mc_response.players.max)
            elif isinstance(mc_response, JavaStatusResponse):                                                            #默认端口只有JE的判断以及数据提取
                self.bound_information(server_type="Java", version=mc_response.version.name, online_players=mc_response.players.online, ping_latency=mc_response.latency, icon=self.dealing_icon(mc_response.icon), motd=mc_response.motd.parsed, max_players=mc_response.players.max)
            
            return True

        except ValueError:
            return("没有具体的服务器地址，无法建立连接")

        except ConnectionRefusedError:
            if self.ping_success:
                self.bound_information(server_type="Bedrock", version=mc_response.version.name, online_players=mc_response.players.online, ping_latency=mc_response.latency, icon=self.dealing_icon(), motd=mc_response.motd.parsed, max_players=mc_response.players.max)

                return True
            else:
                return(f"无法连接至服务器：{self.server_address}，服务器可能处于离线状态")

    async def status(self, host: str) -> JavaStatusResponse | BedrockStatusResponse:
        """同时从Java和Bedrock获取信息"""
        success_task = await self.handle_exceptions(
            *(
                await asyncio.wait(
                    {
                        asyncio.create_task(self.handle_bedrock(host), name="Get status as Bedrock"),
                        asyncio.create_task(self.handle_java(host), name="Get status as Java"),
                    },
                    return_when=asyncio.FIRST_COMPLETED,
                )
            )
        )

        if success_task is None:
            raise ConnectionRefusedError("No tasks were successful. Is server offline?")

        return success_task.result()


    async def handle_exceptions(self, done: set[asyncio.Task], pending: set[asyncio.Task]) -> asyncio.Task | None:
        """Handle exceptions from tasks.

        Also, cancel all pending tasks, if found correct one.
        """
        if len(done) == 0:
            raise ValueError("No tasks was given to `done` set.")

        for i, task in enumerate(done):
            if task.exception() is not None:
                if len(pending) == 0:
                    continue

                if i == len(done) - 1:  # firstly check all items from `done` set, and then handle pending set
                    return await self.handle_exceptions(*(await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)))
            else:
                for pending_task in pending:
                    pending_task.cancel()
                return task


    async def handle_java(self, host: str) -> JavaStatusResponse:
        """A wrapper around mcstatus, to compress it in one function."""
        return await (await JavaServer.async_lookup(host)).async_status()

    async def handle_bedrock(self, host: str) -> BedrockStatusResponse:
        """A wrapper around mcstatus, to compress it in one function."""
        # note: `BedrockServer` doesn't have `async_lookup` method, see it's docstring
        return await BedrockServer.lookup(host).async_status()

    def bound_information(self, server_type: str = "", version: str = "", online_players: int = 0, max_players: int = 0, ping_latency: float = 0.0, icon: str = "", motd=None) -> None:
        """绑定服务器信息"""
        if motd is None:
            motd = []
        self.server_information = {"serverAddress": self.server_address, "serverType": server_type, "version": version, "onlinePlayers": online_players, "maxPlayers": max_players, "pingLatency": ping_latency, "Icon": icon, "MOTD": motd}

    def check_java_server(self, host: str) -> bool | JavaStatusResponse:
        """判断是不是JavaServer，是的话返回JavaStatusResponse，不是返回False（会被ConnectionRefusedError捕捉）"""
        try:
            return JavaServer(host).status()
        except Exception as _:                                                #pylint: disable=broad-except
            return False

    def dealing_icon(self, icon: str | None = None) -> str:                   #icon逻辑，如果有Icon先给Icon，没Icon再看自定义Group头像，最后默认黑色
        """TODO:future:可能会加入定义【Q群默认地址】支持自定义图片 正在完成"""
        if icon is not None and icon != "":
            icon_final = re.sub(r'data:image/[^;]+;base64,', '', icon) #获取服务器Icon 并去掉base64图片前缀
        elif self.groupid is not None:
            response = requests.get(f"https://p.qlogo.cn/gh/{self.groupid}/{self.groupid}/640/", timeout=5)
            if response.status_code == 200:
                icon_final = base64.b64encode(response.content).decode('utf-8')        #TODO:这里不应该直接用群头像，建议使用自定义（mc_default_server_group）
            else:
                icon_final = PictureDefine.CouldNotFindQGroupPicture
        elif self.global_default_icon != '':
            icon_final = self.global_default_icon
        else:
            icon_final = PictureDefine.Black

        return icon_final
