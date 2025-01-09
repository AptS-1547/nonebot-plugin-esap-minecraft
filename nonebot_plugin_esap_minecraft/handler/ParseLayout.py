"""
布局处理类 ParseLayout.py 2025-01-09
Author: LatosProject

ParseLayout类用于照片的布局解析，提供了以下方法：
_parse_icon: 解析icon图标
_parse_text: 解析文本
_parse_text_groups: 解析文本组
_parse_motd: 解析motd
"""

import xml.etree.ElementTree as ET


class ParseLayout:
    """布局处理类"""

    def __init__(self, xml_layout: str, information: dict) -> None:
        """
        初始化 ParseLayout 类，解析传入的 XML 布局文件并获取根元素。

        参数:
            xml_layout: XML 文件路径
        """
        self.xml_layout = xml_layout
        self.tree = ET.parse(xml_layout)
        self.root = self.tree.getroot()
        self.information = information

    def _parse_icon(self) -> tuple | ValueError:
        """
        解析 XML 中的 Icon 元素，提取图标的宽度、高度、圆角信息和位置。

        返回:
            - (width, height, round_corner, position): 返回图标宽度、高度、圆角和位置元组。
            如果找不到 Icon 元素，则抛出 ValueError。

        异常:
            - 如果没有找到 Icon 元素，抛出 ValueError 异常。
        """
        icon = self.root.find('Icon')
        if icon is not None:
            # source = icon.get('source')
            width = icon.get('width')
            height = icon.get('height')
            round_corner = icon.get('round_corner')
            position = tuple(map(int, icon.get('position').split(',')))
            return width, height, round_corner, position
        else:
            return ValueError("Icon element not found")

    def _parse_text(self) -> list:
        """
        解析给定元素中的所有 Text 子元素，返回每个文本元素的内容、字体、字体大小、颜色和位置。

        参数:
            root: XML 元素（可以是根元素或其他子元素）

        返回:
            - texts: 一个包含每个文本信息的字典列表。每部字典包含：
                - 'content': 文本内容
                - 'font': 字体
                - 'font_size': 字体大小
                - 'color': 文本颜色（以元组形式表示 RGB）
                - 'text_position': 文本位置（以元组形式表示）

        异常:
            - 无
        """
        texts = []
        for text in self.root.findall('Text'):
            content = text.get('content')

            replacements = {
                "{onlinePlayers}": str(self.information['onlinePlayers']),
                "{maxPlayers}": str(self.information['maxPlayers']),
                "{pingLatency}": str(self.information['pingLatency']),
                "{serverAddress}": str(self.information['serverAddress']),
                "{serverType}": str(self.information['serverType']),
                "{version}": str(self.information['version'])
            }

            for placeholder, value in replacements.items():
                content = content.replace(placeholder, value)

            font = text.get('font')
            font_size = text.get('font_size')
            color = tuple(map(int, text.get('color').split(',')))
            text_position = tuple(map(int, text.get('text_position').split(',')))
            texts.append({
                'content': content,
                'font': font,
                'font_size': font_size,
                'color': color,
                'text_position': text_position,
            })
        return texts

    def _parse_text_groups(self) -> list:
        """
        解析 XML 中的所有 TextGroup 元素，每个 TextGroup 包含一个对齐方式和多个 Text 元素。

        返回:
            - text_groups: 一个字典列表，每个字典包含：
                - 'alignment': 对齐方式
                - 'texts': 包含该组所有文本元素的列表

        异常:
            - 无
        """
        text_groups = []
        for group in self.root.findall('TextGroup'):
            alignment = group.get('alignment')
            texts = self._parse_text()
            text_groups.append({'alignment': alignment, 'texts': texts})
        return text_groups

    def _parse_motd(self) -> tuple | ValueError:
        """
        解析 XML 中的 Motd 元素，提取其位置、字体大小、字体、颜色等信息。

        返回:
            - (content, position, font, font_size, color): 返回 MOTD 的信息、位置元组、字体、字体大小和颜色元组。
            如果找不到 Motd 元素，则抛出 ValueError。

        异常:
            - 如果没有找到 Motd 元素，抛出 ValueError 异常。
        """
        motd = self.root.find('MOTD')
        if motd is not None:
            content = motd.get('content')
            content = content.replace("{motd_str}", str(self.information['MOTD']))
            position = tuple(map(int, motd.get('position').split(',')))
            font_size = motd.get('font_size')
            font = motd.get('font')
            color = tuple(map(int, motd.get('color').split(',')))
            return content, position, font, font_size, color
        else:
            return ValueError("MOTD element not found")
