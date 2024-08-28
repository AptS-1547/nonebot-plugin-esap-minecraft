from pydantic import BaseModel, field_validator

class Config(BaseModel):
    mc_qqgroup_id: list
    mc_global_default_server: str
    mc_global_default_icon: str
    mc_ping_server_interval_second: int = 60
    mc_qqgroup_default_server: dict

    @field_validator("mc_ping_server_interval_second")
    @classmethod
    def _(cls, v: int) -> int:
        if v >= 1:
            return v
        raise ValueError("mc_ping_server_interval_second must greater than 1")

    # @field_validator("mc_global_default_icon")
    # @classmethod
    # def _(cls, v: str) -> str:
    #     if v:
    #         return v
    #     raise ValueError("mc_ping_server_interval_second must greater than 1")
    #TODO:future:加入定义【icon默认图片】错误判断