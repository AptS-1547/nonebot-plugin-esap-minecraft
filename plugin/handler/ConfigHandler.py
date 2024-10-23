"""
Copyright 2022-2024 The ESAP Project. All rights reserved.
Use of this source code is governed by a GPL-3.0 license that can be found in the LICENSE file.

配置文件处理类 ConfigHandler.py 2024-10-21
Author: AptS:1547

ConfigHandler类用于处理配置文件的加载和保存，提供了三个方法：
load_config: 加载配置文件，返回Config对象，无参数
save_config: 保存更改的配置文件，返回bool，无参数
reload_config: 重载配置文件，无参数

"""

import base64, yaml                          #pylint: disable=multiple-imports
from pydantic import BaseModel, field_validator
from pydantic import ValidationError


class Config(BaseModel):
    """
    配置文件模型
    enable: 是否启用插件
    mc_qqgroup_id: 监听的QQ群号
    mc_global_default_server: 默认服务器
    mc_global_default_icon: 默认服务器图标
    mc_ping_server_interval_second: 服务器ping间隔
    mc_qqgroup_default_server: QQ群默认服务器
    mc_serverscaner_enable: 是否启用服务器扫描
    """
    enable: bool = False
    mc_qqgroup_id: list = []
    mc_global_default_server: str = ""
    mc_global_default_icon: str = ""
    mc_ping_server_interval_second: int = 60
    mc_qqgroup_default_server: dict = {}
    mc_serverscaner_enable: bool = False
    mc_serverscaner_status: bool = False

    @field_validator("mc_ping_server_interval_second")
    @classmethod
    def _(cls, v: int) -> int:
        """验证是否大于1"""
        if v >= 1:
            return v
        raise ValueError("mc_ping_server_interval_second must greater than 1")

    @field_validator("mc_global_default_icon")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """验证是否为base64字符串"""
        try:
            base64.b64decode(v)
            return v
        except Exception as e:
            raise ValueError("mc_global_default_icon must be a valid base64 string") from e


class ConfigHandler:
    """
    配置文件处理类
    load_config: 加载配置文件，返回Config对象，无参数
    save_config: 保存更改的配置文件，返回bool，无参数
    """

    def __init__(self):
        """初始化配置信息"""
        self.error = ""
        self.config = self.load_config()

    def load_config(self) -> Config:
        """加载配置文件"""
        try:
            self.error = ""
            # TODO: 这里的路径应该是相对路径，而不是绝对路径
            with open("", encoding="utf-8", mode="r") as f:
                docs = yaml.safe_load(f)
                f.close()

            config = Config(**docs)
            return config

        except FileNotFoundError:
            self.error =  "[epmc_minecraft_bot] 配置文件不存在！请检查你的配置并重载配置文件！"
            return Config()
        except ValidationError:
            self.error = "[epmc_minecraft_bot] 配置文件出错！请检查你的配置并重载配置文件！"
            return Config()
        except:      #pylint: disable=bare-except
            self.error = "[epmc_minecraft_bot] 配置文件格式错误！请检查你的配置并重载配置文件！"
            return Config()

    def save_config(self) -> bool:
        """保存更改的配置文件"""
        try:
            with open("****************************", encoding="utf-8", mode="w") as f:
                config_dict = {"enable": self.config.enable, "mc_qqgroup_id":self.config.mc_qqgroup_id, "mc_global_default_server": self.config.mc_global_default_server, "mc_global_default_icon": self.config.mc_global_default_icon, "mc_ping_server_interval_second": self.config.mc_ping_server_interval_second, "mc_qqgroup_default_server": self.config.mc_qqgroup_default_server, "mc_serverscaner_enable": self.config.mc_serverscaner_enable}
                yaml.dump(config_dict, f)
                del config_dict
                f.close()
            return True
        except:       #pylint: disable=bare-except
            return False

    def reload_config(self) -> None:
        """重载配置文件"""
        self.config = self.load_config()