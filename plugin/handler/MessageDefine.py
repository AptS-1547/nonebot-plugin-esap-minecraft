"""
Copyright 2022-2024 The ESAP Project. All rights reserved.
Use of this source code is governed by a GPL-3.0 license that can be found in the LICENSE file.

帮助信息定义类 AdminHelp.py 2024-10-22
Author: AptS:1547

MessageDefine类用于存储命令的帮助信息
"""

class MessageDefine:                                     #pylint: disable=missing-module-docstring, invalid-name, too-few-public-methods
    """定义一些变量，用于存储命令的帮助信息"""
    private_superuser_command_help = "喵喵ap~ SuperUser菜单\n--------------------\n~conf help 展开本菜单\n~conf status 查看插件状态\n~conf reload 重载插件\n~conf scan start/stop 启动/停止服务器扫描\n~conf get 参数名 获取参数值\n~conf set 参数名 参数值 设置参数值\n~conf qqgroup add/del QQ群号\n\n--------------------\n参数名列表：\n   enable\n   mc_qqgroup_id\n   mc_global_default_server\n   mc_global_default_icon\n   mc_ping_server_interval_second\n   mc_qqgroup_default_server\n   mc_serverscaner_enable"
    public_groupadmin_command_help = "喵喵ap~ GroupAdmin菜单\n--------------------\n~conf help 展开本菜单\n~conf status 查看插件状态\n~conf get 参数名 获取参数值\n~conf set 参数名 参数值 设置参数值\n\n--------------------\n参数名列表：\n   default_icon\n   default_icon_type\n   need_scan\n   serverAddress"
    group_help_message = "喵喵ap~ 人机菜单\n--------------------\n✅ ~help 展开本菜单\n✅ ~ping <服务器地址> 查询服务器状态\n⚠️ ~vwl 白名单管理\n⚠️ ~conf 机器人设置"

    bot_is_connected_with_scanner = "[epmc_minecraft_bot] 机器人已上线，已启动对MC服务器的定时扫描"
    bot_is_connected_without_scanner = "[epmc_minecraft_bot] 机器人已上线，插件未启用或者未启用扫描服务器，无法启动对MC服务器的定时扫描"
    bot_is_connected_without_server = "[epmc_minecraft_bot] 机器人已上线，未设置需要扫描的服务器，无法启动对MC服务器的定时扫描"
    bot_is_disconnected_with_scanner = "[epmc_minecraft_bot] 机器人已下线，已停止对MC服务器的定时扫描"
    bot_is_disconnected_without_scanner = "[epmc_minecraft_bot] 机器人已下线，插件未启用或者未启用扫描服务器，无法停止对MC服务器的定时扫描"

    logger_reload_with_scanner = "[epmc_minecraft_bot] 重载配置文件，已重启对MC服务器的定时扫描"
    logger_reload_without_scanner = "[epmc_minecraft_bot] 重载配置文件，插件未启用或者未启用扫描服务器，无法重启对MC服务器的定时扫描"
    logger_reload_without_server = "[epmc_minecraft_bot] 重载配置文件，未设置需要扫描的服务器，无法重启对MC服务器的定时扫描"
    logger_reload_sth_wrong = "[epmc_minecraft_bot] 重载配置文件，发生错误，无法重启对MC服务器的定时扫描"

    args_do_not_exist = "参数不存在，输入~conf help查看帮助信息"
    args_error_scan_command = "服务器扫描命令格式错误，正确用法：~conf scan start/stop"
    args_error_get_command = "获取参数值命令格式错误，正确用法：~conf get 参数名\n输入~conf help查看参数信息"
    args_error_set_command = "设置参数值命令格式错误，正确用法：~conf set 参数名 参数值\n输入~conf help查看参数信息"
    args_error_qqgroup_command = "设置参数值命令格式错误，正确用法：~conf qqgroup add/del 123456789\n输入~conf help查看参数信息"

    command_qqgroup_add_exist = "此QQ群已存在"
    command_qqgroup_del_not_exist = "此QQ群不存在"

    scanner_is_running = "MC服务器扫描器已启动"
    scanner_is_stopped = "MC服务器扫描器已停止"
    scanner_already_running = "MC服务器扫描器已经在运行"
    scanner_already_stopped = "MC服务器扫描器已经停止"

    plugin_is_not_enable = "插件未启用"
    conf_is_none = "此条参数值为None"
    conf_get_args_is_none = "参数不能为空\n输入~conf help查看参数信息"

    def command_set_sueccess(self, key: str = "", value: str = "") -> str:
        """设置参数成功"""
        return f"已写入参数： {key} = {value}。插件重载中……"

    def command_superuser_status_message(self, plugin_enable: bool = False, scaner_enable: bool = False, scan_server_list: list = []) -> str:    #pylint: disable=dangerous-default-value
        """插件状态信息"""
        scan_server = ""
        for server in scan_server_list:
            scan_server += f"\n   {server['groupID']}: {server['serverAddress']} "
        return f"插件状态：{plugin_enable}\n服务器扫描器状态：{scaner_enable}\n服务器扫描列表：{scan_server}"
    
    def command_groupadmin_status_message(self, plugin_enable: bool = False, scaner_enable: bool = False) -> str:
        """插件状态信息"""
        return f"插件状态：{plugin_enable}\n服务器扫描器状态：{scaner_enable}"
    
    def command_qqgroup_success(self, action: str = "", groupid: int = 0) -> str:
        """QQgroup命令执行成功"""
        return f"已{action}QQ群：{groupid}"
