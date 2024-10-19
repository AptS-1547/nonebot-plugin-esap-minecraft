import yaml, os
from pydantic import BaseModel, field_validator
from pydantic import ValidationError

class Config(BaseModel):
    enable: bool = False
    mc_qqgroup_id: list = []
    mc_global_default_server: str = ""
    mc_global_default_icon: str = ""
    mc_ping_server_interval_second: int = 60
    mc_qqgroup_default_server: dict = {}
    mc_serverscaner_enable: bool = False

    @field_validator("mc_ping_server_interval_second")
    @classmethod
    def _(cls, v: int) -> int:
        if v >= 1:
            return v
        raise ValueError("mc_ping_server_interval_second must greater than 1")

    @field_validator("mc_global_default_icon")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        import base64
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("mc_global_default_icon must be a valid base64 string")

class ConfigHandler():
    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> Config | str :
        try:
            config_dict = {}
            # TODO: 这里的路径应该是相对路径，而不是绝对路径
            with open("***********************") as f:
                docs = yaml.load_all(f, Loader=yaml.FullLoader)
                for doc in docs:
                    for k, v in doc.items():
                        config_dict[k] = v

            config = Config(**config_dict)
            del config_dict
            return config

        except FileNotFoundError as e:
            return "[epmc_minecraft_bot] 配置文件不存在！请检查你的配置并重新启动Nonebot！" #TODO:应该新增命令重载配置文件 ~conf reload
        except ValidationError as e:
            return "[epmc_minecraft_bot] 配置文件出错！请检查你的配置并重新启动Nonebot！"


    def save_config(self):
        pass

