import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mcstatus.motd.components import Formatting, MinecraftColor

from .PictureDefine import PictureDefine

class PictureHandler:
    def __init__(self, information: dict) -> None:
        """
        输入格式：
            Information应该包括服务器地址、端口、版本、MOTD、服务器图标以及当前在线玩家数和玩家名称等
            base64image不能有data:image/png;base64,前缀
        """
        self.information = information
        self.leftFontLocation = PictureDefine.MinecraftFont
        self.rightFontLocation = PictureDefine.MinecraftFont
        self.image = self.open_base64_image(PictureDefine.Background)
        
    # 生成最终返回的图片
    def MakePicture(self) -> Image.Image:
        # 服务器图标
        Icon = self.open_base64_image(self.information["Icon"]).resize((400, 400))
        Icon = self.round_corner(Icon, 22)
        IconAlphaChannel = Icon.split()[-1]
        self.image.paste(Icon, (215, 200), mask=IconAlphaChannel)

        text_list_left = [self.information["serverAddress"], f"{self.information['serverType']} {self.information['version']}"]

        self.image = self.left_middle_font(self.image, text_list_left, (45, 215, 209))

        # TODO:在图片右方模块写字，按理来说应该让这个函数确定绘制高度
        
        text_start_height = 60
        text_right = f"当前在线玩家数：{self.information['onlinePlayers']}/{self.information['maxPlayers']}"
        self.image, text_start_height = self.right_middle_font(self.image, text_right, text_start_height, 80, (45, 215, 209))

        self.image, text_start_height = self.dealing_motd(self.image, text_start_height, self.information["MOTD"])

        text_right = f"服务器Ping请求所用时间：{round(self.information['pingLatency'],2)}ms"
        self.image, _ = self.right_middle_font(self.image, text_right, text_start_height, 80, (45, 215, 209))

        return self.image

    # PIL打开base64图片
    def open_base64_image(self, base64_str):
        try:
            image_data = base64.b64decode(base64_str)
            BytesIO_obj = BytesIO(image_data)
            img = Image.open(BytesIO_obj)
            return img
        except UnidentifiedImageError:
            image_data = base64.b64decode(PictureDefine.Black)
            BytesIO_obj = BytesIO(image_data)
            img = Image.open(BytesIO_obj)
            return img

    #给图片加上圆角效果
    def round_corner(self, img: Image.Image, rad: int = 0) -> Image.Image:         
        # 创建一个半径为给定值的黑色圆形图像
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
    
    # 在图片左方模块写字
    def left_middle_font(self, img: Image.Image, text: list, rgb: tuple = (0,0,0)) -> Image.Image:
        draw = ImageDraw.Draw(img)
        font_size = 80
        text_start_height = 682

        for text_line in text:
            font = ImageFont.truetype(self.leftFontLocation, font_size)
            (text_width, text_height), (_, _) = font.font.getsize(text_line)

            while text_width > 680:
                font = ImageFont.truetype(self.leftFontLocation, font_size)
                (text_width, text_height), (_, _) = font.font.getsize(text_line)
                font_size -= 1
            draw.text(((830 - text_width) // 2, text_start_height), text_line, font=font, fill=rgb)
            text_start_height += text_height + 50
        return img
    
    def right_middle_font(self, img: Image.Image, text: str, height: int, font_size: int = 80, rgb: tuple = (0,0,0)) -> tuple:
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(self.rightFontLocation, font_size)
        (text_width, text_height_right), (_, _) = font.font.getsize(text)

        while text_width > 1297:
            font_size -= 1
            font = ImageFont.truetype(self.rightFontLocation, font_size)
            (text_width, text_height_right), (_, _) = font.font.getsize(text)
        
        draw.text((928, height), text, font=font, fill=rgb)

        height = height + 50 + text_height_right
        return img, height

    def dealing_motd(self, img: Image.Image, height: int, motd_parsed: list = []) -> tuple:     #绘制位置（928,180）
        # 处理MOTD，暂时不作字体样式的处理
        global index, motd_style, motd_color
        motd_str = ""
        motd_str1 = ""
        motd_str2 = ""

        if '\n' in motd_parsed:                # 如果有换行符，获取换行符的位置
            index = motd_parsed.index('\n')
        else:
            index = -1

        for item in motd_parsed:                   # 获取每一行字符串的长度
            if index == -1 and isinstance(item, str):
                motd_str += item
            if index != -1 and isinstance(item, str):
                if motd_parsed.index(item) < index:
                    motd_str1 += item
                elif motd_parsed.index(item) > index:
                    motd_str2 += item
        
        if index == -1 : 
            font_size2 = 80
            text_height2 = 70
            font_size1, text_height1  = self.check_motd_length(motd_str)
        else:
            font_size1, text_height1  = self.check_motd_length(motd_str1)
            font_size2, text_height2 = self.check_motd_length(motd_str2)

        text_height = min(text_height1, text_height2)
        
        font = ImageFont.truetype(self.rightFontLocation, font_size1)
        start_text_length = 928
        start_text_height = height

        for item in motd_parsed:                   # 开始绘制
            if motd_parsed.index(item) == 0:       # 设置初始绘制的样式和颜色
                draw = ImageDraw.Draw(img)
                motd_style = None
                motd_color = (255,255,255)
            elif item == "\n":  # 绘制第二行 - 准备工作
                start_text_length = 928
                start_text_height += text_height + 50
                font = ImageFont.truetype(self.rightFontLocation, font_size2)
                continue

            if item == Formatting.RESET and motd_str != "":  # 重置字体样式，并绘制先前已经保存的字符串
                motd_style = None
                motd_color = (255,255,255)
                
            elif isinstance(item, Formatting):   #返回字体样式
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
            elif isinstance(item, MinecraftColor): #返回字体色号RGB
                match item:
                    case MinecraftColor.BLACK:
                        motd_color = (0,0,0)
                    case MinecraftColor.DARK_BLUE:
                        motd_color = (0,0,170)
                    case MinecraftColor.DARK_GREEN:
                        motd_color = (0,170,0)
                    case MinecraftColor.DARK_AQUA:
                        motd_color = (0,170,170)
                    case MinecraftColor.DARK_RED:
                        motd_color = (170,0,0)
                    case MinecraftColor.DARK_PURPLE:
                        motd_color = (170,0,170)
                    case MinecraftColor.GOLD:
                        motd_color = (255,170,0)
                    case MinecraftColor.GRAY:
                        motd_color = (170,170,170)
                    case MinecraftColor.DARK_GRAY:
                        motd_color = (85,85,85)
                    case MinecraftColor.BLUE:
                        motd_color = (85,85,255)
                    case MinecraftColor.GREEN:
                        motd_color = (85,255,85)
                    case MinecraftColor.AQUA:
                        motd_color = (85,255,255)
                    case MinecraftColor.RED:
                        motd_color = (255,85,85)
                    case MinecraftColor.LIGHT_PURPLE:
                        motd_color = (255,85,255)
                    case MinecraftColor.YELLOW:
                        motd_color = (255,255,85)
                    case MinecraftColor.WHITE:
                        motd_color = (255,255,255)
                    case MinecraftColor.MINECOIN_GOLD:
                        motd_color = (221,214,5)
                    # 超绝高血压
            elif isinstance(item, str) and item != "":
                (text_width, _), (_, _) = font.font.getsize(item)
                draw.text((start_text_length, start_text_height), item, font=font, fill=motd_color)
                start_text_length += text_width

        return img, height + 100 + text_height*2

    def check_motd_length(self, motd: str) -> tuple:
        font_size = 80
        font = ImageFont.truetype(self.rightFontLocation, font_size)
        (text_width, text_height), (_, _) = font.font.getsize(motd)
        while text_width > 1297:
            font_size -= 1
            font = ImageFont.truetype(self.rightFontLocation, font_size)
            (text_width, text_height), (_, _) = font.font.getsize(motd)
        return (font_size, text_height)