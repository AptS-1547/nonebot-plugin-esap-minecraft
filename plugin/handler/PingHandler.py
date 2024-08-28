import asyncio, re

from mcstatus import BedrockServer, JavaServer
from mcstatus.status_response import BedrockStatusResponse, JavaStatusResponse
from esap_minecraft_bot.plugins.esap_minecraft_bot.config import Config as mcPluginConfig

class PingHandler:

    def __init__(self, serverAddress: str, pluginConfig: mcPluginConfig, groupID: int) -> None:
        #一些必要的全局变量
        self.serverAddress = serverAddress
        self.pluginConfig = pluginConfig
        self.groupID = groupID
        self.serverType = "Java"
        self.version = ""
        self.motdFinal = ""
        self.playerNumber = 0
        self.Icon = ""
        self.pingLatency = 0.0
        self.successBedrock = False

    async def ping_server(self) -> str | bool:
        """发送Ping请求，成功返回True，失败返回失败原因(str)"""
        if self.serverAddress != None and self.serverAddress != '':
            pass
        elif self.pluginConfig.mc_global_default_server != '':
            self.serverAddress = self.pluginConfig.mc_global_default_server
        else:
            return("没有具体的服务器地址，无法建立连接")

        try:
            mc_response = await self.status(self.serverAddress)
            if isinstance(mc_response, BedrockStatusResponse):               #直接使用默认端口会出现此可能：同时开了JE和BE，会先检测出BE，但正常来说应该返回JE
                self.successBedrock = True
                self.serverType = "Bedrock"
                mc_response_java = self.check_java_server(self.serverAddress)       #对JE默认端口Ping，检测JE有无开启，如果没开启扔出ConnectionRefusedError，放到下面解决
                
                if isinstance(mc_response_java, JavaStatusResponse):         #是JE的处理
                    self.serverType = "Java"
                    self.version = mc_response_java.version.name
                    self.playerNumber = mc_response_java.players.online
                    self.pingLatency = mc_response_java.latency
                    self.Icon = self.dealing_icon(mc_response_java.icon)
                    motd = mc_response_java.motd.raw
                    self.motdFinal = self.dealing_motd(motd) # type: ignore
                else:                                                        #是BE的处理
                    motd = mc_response.motd.raw
                    self.version = mc_response.version.name # type: ignore
                    self.playerNumber = mc_response.players.online #type: ignore
                    self.pingLatency = mc_response.latency #type: ignore
                    self.Icon = self.dealing_icon()
                    self.motdFinal = self.dealing_motd(motd) # type: ignore
            elif isinstance(mc_response, JavaStatusResponse):                                                            #默认端口只有JE的判断以及数据提取
                motd = mc_response.motd.raw
                self.version = mc_response.version.name
                self.playerNumber = mc_response.players.online
                self.pingLatency = mc_response.latency
                self.Icon = self.dealing_icon(mc_response.icon)
                self.motdFinal = self.dealing_motd(motd) # type: ignore
            
            return True

        except ValueError:
            return("没有具体的服务器地址，无法建立连接")

        except ConnectionRefusedError:
            if self.successBedrock == True:
                motd = mc_response.motd.raw
                self.version = mc_response.version.name # type: ignore
                self.playerNumber = mc_response.players.online #type: ignore
                self.pingLatency = mc_response.latency #type: ignore
                self.Icon = self.dealing_icon()
                self.motdFinal = self.dealing_motd(motd) # type: ignore

                return True
            else:
                return(f"无法连接至服务器：{self.serverAddress}，服务器可能处于离线状态")

    async def status(self, host: str) -> JavaStatusResponse | BedrockStatusResponse:
        """同时从Java和Bedrock获取信息"""
        success_task = await self.handle_exceptions(
            *(
                await asyncio.wait(
                    {
                        asyncio.create_task(self.handle_java(host), name="Get status as Java"),
                        asyncio.create_task(self.handle_bedrock(host), name="Get status as Bedrock"),
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
            if task.exception() != None:
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

    def check_java_server(self, host: str) -> bool | JavaStatusResponse:
        """判断是不是JavaServer，是的话返回JavaStatusResponse，不是返回False（会被ConnectionRefusedError捕捉）"""
        try:
            mc_status_java = JavaServer(host).status()
            return mc_status_java
        except:
            return False

    def dealing_motd(self, motd: str | list | dict) -> str | list | dict:
        """TODO:处理MOTD，需要重写来支持图片MOTD颜色"""
        if isinstance(motd, str):                      #目前还没有检测到返回值为str的，如果是str先直接发过去
            motd_final = motd
        elif isinstance(motd, list):                   #目前还没有检测到返回值为list的，如果是list先直接发过去
            motd_final = motd
        elif "extra" in motd:                          #就三种类型，list，str，dict，只剩下dict了直接查有没有extra，看看是不是dict套list
            motd_final = ""
            for text in motd["extra"]:
                motd_final += text["text"]
        else:                                          #只剩下最后一个可能，直接就只有dict，取key：text
            motd_final = motd["text"]
        return motd_final

    def dealing_icon(self, icon: str | None = None) -> str:                   #icon逻辑，如果有Icon先给Icon，没Icon再看自定义Group头像，最后默认黑色
        #TODO:future:可能会加入定义【Q群默认地址】支持自定义图片
        if icon != None and icon != "":
            icon_final = re.sub(r'data:image/[^;]+;base64,', 'base64://', icon) #获取服务器Icon Base64编码并转换为CQ格式
        elif self.groupID != None:
            icon_final = f"https://tenapi.cn/v2/groupimg?qun={self.groupID}"        #TODO:这里不应该直接用群头像，建议使用自定义（mc_default_server_group）
        elif self.pluginConfig.mc_global_default_icon != '':
            icon_final = self.pluginConfig.mc_global_default_icon
        else:
            icon_final = "base64://iVBORw0KGgoAAAANSUhEUgAAABQAAAAVCAIAAADJt1n/AAAAKElEQVQ4EWPk5+RmIBcwkasRpG9UM4mhNxpgowFGMARGEwnBIEJVAAAdBgBNAZf+QAAAAABJRU5ErkJggg=="
        return icon_final