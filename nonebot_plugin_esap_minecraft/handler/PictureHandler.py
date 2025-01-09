"""
Copyright 2022-2024 The ESAP Project. All rights reserved.
Use of this source code is governed by a GPL-3.0 license that can be found in the LICENSE file.

图片处理类 PictureHandler.py 2024-10-21
Author: AptS:1547

LastUpdate: 2025-01-10
LastUpdateBy: LatosProject

PictureHandler类用于处理图片的生成，提供了以下方法：
MakePicture: 生成最终返回的图片
open_base64_image: PIL打开base64图片
round_corner: 给图片加上圆角效果
left_middle_font: 在图片左方模块写字
right_middle_font: 在图片右方模块写字
dealing_motd: 处理MOTD
check_motd_length: 检查MOTD长度
"""

import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mcstatus.motd.components import Formatting, MinecraftColor

from .ParseLayout import ParseLayout
from .PictureDefine import PictureDefine  # pylint: disable=relative-beyond-top-level


class PictureHandler:
    """图片处理类"""

    def __init__(self, information: dict, xml_layout: str) -> None:
        """
        输入格式：
            Information应该包括服务器地址、端口、版本、MOTD、服务器图标以及当前在线玩家数和玩家名称等
            base64image不能有data:image/png;base64,前缀
        """
        self.information = information
        self.parse_layout = ParseLayout(xml_layout, information)
        """背景"""
        self.image = self.open_base64_image(PictureDefine.Background)

    def make_picture(self) -> Image.Image:
        """生成最终返回的图片"""
        # 服务器图标
        self.image = self.draw_icon()
        # 文本组
        self.image = self.draw_text_group(self.parse_layout._parse_text_groups())
        # 文本
        self.image = self.draw_text(self.parse_layout._parse_text(), self.image)
        # Motd
        self.image = self.draw_motd(self.image)[0]
        return self.image

    def open_base64_image(self, base64_str):
        """PIL打开base64图片"""
        try:
            image_data = base64.b64decode(base64_str)
            bytesio_obj = BytesIO(image_data)
            img = Image.open(bytesio_obj)
            return img
        except UnidentifiedImageError:
            image_data = base64.b64decode(PictureDefine.Black)
            bytesio_obj = BytesIO(image_data)
            img = Image.open(bytesio_obj)
            return img

    def round_corner(self, img: Image.Image, rad: int = 0) -> Image.Image:
        """给图片加上圆角效果"""
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', img.size, 255)
        w, h = img.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        img.putalpha(alpha)
        return img

    def draw_text(self, text: list, img: Image.Image, alignment: str = "left") -> Image.Image:
        # 判断 TextGroup 还是 Text
        draw = ImageDraw.Draw(img)
        if isinstance(text, dict) and 'texts' in text:
            for text_line in text['texts']:
                text_content = text_line['content']
                text_color = text_line['color']
                text_size = text_line["font_size"]
                text_position = text_line["text_position"]
                text_font = ImageFont.truetype(text_line["font"], text_size)

                text_bbox = draw.textbbox((0, 0), text_content, font=text_font)
                text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

                # 根据对齐方式调整文本位置
                if alignment == "center":
                    text_position = (text_position[0] - text_width // 2, text_position[1])
                elif alignment == "right":
                    text_position = (text_position[0] - text_width, text_position[1])
                # 默认情况下左对齐

                draw.text(text_position, text_content, font=text_font, fill=text_color)
        else:
            for text_line in text:
                text_content = text_line['content']
                text_color = text_line['color']
                text_size = text_line["font_size"]
                text_position = text_line["text_position"]
                text_font = ImageFont.truetype(text_line["font"], text_size)
                draw.text(text_position, text_content, font=text_font, fill=text_color)
        return img

    def draw_text_group(self, text_group: list) -> Image.Image:
        img = self.image
        for text in text_group:
            img = self.draw_text(text, img, alignment=text["alignment"])
        return img

    def draw_icon(self) -> Image.Image:
        img = self.image
        icon_info = self.parse_layout._parse_icon()
        icon = self.open_base64_image(self.information["Icon"]).resize((icon_info[0], icon_info[1]))
        icon = self.round_corner(icon, icon_info[2])
        icon_alpha_channel = icon.split()[-1]
        self.image.paste(icon, icon_info[3], mask=icon_alpha_channel)
        return img

    def draw_motd(self, img: Image.Image, motd_parsed=None) -> Image.Image:  # 绘制位置（928,180）
        """处理MOTD，暂时不作字体样式的处理"""
        draw = ImageDraw.Draw(img)
        index, motd_style, motd_color = "", "", ""
        motd_str = ""
        motd_str1 = ""
        motd_str2 = ""

        if motd_parsed is None:
            motd_parsed = ["epmcbot提示: 本服务器没有MOTD"]

        if '\n' in motd_parsed:  # 如果有换行符，获取换行符的位置
            index = motd_parsed.index('\n')
        else:
            index = -1

        for item in motd_parsed:  # 获取每一行字符串的长度
            if index == -1 and isinstance(item, str):
                motd_str += item
            if index != -1 and isinstance(item, str):
                if motd_parsed.index(item) < index:
                    motd_str1 += item
                elif motd_parsed.index(item) > index:
                    motd_str2 += item

        if index == -1:
            font_size2 = 80
            text_height2 = 70
            font_size1, text_height1 = self.check_motd_length(motd_str)
        else:
            font_size1, text_height1 = self.check_motd_length(motd_str1)
            font_size2, text_height2 = self.check_motd_length(motd_str2)

        text_height = min(text_height1, text_height2)

        font = ImageFont.truetype(self.parse_layout._parse_motd()[2], font_size1)
        start_text_length = self.parse_layout._parse_motd()[1][0]
        start_text_height = self.parse_layout._parse_motd()[1][1]

        for item in motd_parsed:  # 开始绘制
            if motd_parsed.index(item) == 0:  # 设置初始绘制的样式和颜色
                motd_style = None
                motd_color = (255, 255, 255)
            elif item == "\n":  # 绘制第二行 - 准备工作
                start_text_length = self.parse_layout._parse_motd()[1][0]
                start_text_height += text_height + 50
                font = ImageFont.truetype(self.self.parse_layout._parse_motd()[2], font_size2)
                continue

            if item == Formatting.RESET and motd_str != "":  # 重置字体样式，并绘制先前已经保存的字符串
                motd_style = None
                motd_color = (255, 255, 255)
            elif isinstance(item, Formatting):  # 返回字体样式
                match item:
                    case Formatting.RESET:
                        motd_style = None
                    case Formatting.BOLD:
                        motd_style = "bold"
                    case Formatting.ITALIC:
                        motd_style = "italic"
                    case Formatting.UNDERLINED:
                        motd_style = "underlined"
                    case Formatting.STRIKETHROUGH:
                        motd_style = "strikethrough"
                    case Formatting.OBFUSCATED:
                        motd_style = "obfuscated"
            elif isinstance(item, MinecraftColor):  # 返回字体色号RGB
                match item:
                    case MinecraftColor.BLACK:
                        motd_color = (0, 0, 0)
                    case MinecraftColor.DARK_BLUE:
                        motd_color = (0, 0, 170)
                    case MinecraftColor.DARK_GREEN:
                        motd_color = (0, 170, 0)
                    case MinecraftColor.DARK_AQUA:
                        motd_color = (0, 170, 170)
                    case MinecraftColor.DARK_RED:
                        motd_color = (170, 0, 0)
                    case MinecraftColor.DARK_PURPLE:
                        motd_color = (170, 0, 170)
                    case MinecraftColor.GOLD:
                        motd_color = (255, 170, 0)
                    case MinecraftColor.GRAY:
                        motd_color = (170, 170, 170)
                    case MinecraftColor.DARK_GRAY:
                        motd_color = (85, 85, 85)
                    case MinecraftColor.BLUE:
                        motd_color = (85, 85, 255)
                    case MinecraftColor.GREEN:
                        motd_color = (85, 255, 85)
                    case MinecraftColor.AQUA:
                        motd_color = (85, 255, 255)
                    case MinecraftColor.RED:
                        motd_color = (255, 85, 85)
                    case MinecraftColor.LIGHT_PURPLE:
                        motd_color = (255, 85, 255)
                    case MinecraftColor.YELLOW:
                        motd_color = (255, 255, 85)
                    case MinecraftColor.WHITE:
                        motd_color = (255, 255, 255)
                    case MinecraftColor.MINECOIN_GOLD:
                        motd_color = (221, 214, 5)
                    # 超绝高血压
            elif isinstance(item, str) and item != "":
                (text_width, _), (_, _) = font.font.getsize(item)
                draw.text((start_text_length, start_text_height), item, font=font, fill=motd_color)
                start_text_length += text_width

        return img, self.parse_layout._parse_motd()[1][1] + 100 + text_height * 2

    def check_motd_length(self, motd: str) -> tuple:
        """检查MOTD长度"""
        font_size = 80
        font = ImageFont.truetype(self.parse_layout._parse_motd()[2], font_size)
        (text_width, text_height), (_, _) = font.font.getsize(motd)
        while text_width > 1297:
            font_size -= 1
            font = ImageFont.truetype(self.parse_layout._parse_motd()[2], font_size)
            (text_width, text_height), (_, _) = font.font.getsize(motd)
        return (font_size, text_height)
