import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from .PictureDefine import PictureDefine

class PictureHandler:
    def __init__(self, information: dict) -> None:
        """
        输入格式：
            Information应该包括服务器地址、端口、版本、MOTD、服务器图标以及当前在线玩家数和玩家名称等
            base64image不能有data:image/png;base64,前缀
        """
        self.information = information
        self.leftFontLocation = PictureDefine.ChineseFont
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

        # 在图片右方模块写字
        # 服务器在线玩家数
        text_list_right = [f"当前在线玩家数：{self.information['onlinePlayers']}/{self.information['maxPlayers']}"]

        # 服务器MOTD
        text_list_right += self.information["MOTD"].split("\n")

        # 服务器Ping请求所用时间
        text_list_right += [f"服务器Ping请求所用时间：{round(self.information['pingLatency'],2)}ms"]

        self.image = self.right_middle_font(self.image, text_list_right, 80, (45, 215, 209))

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
    
    # 在图片右方模块写字
    def right_middle_font(self, img: Image.Image, text: list, font_size: int = 80, rgb: tuple = (0,0,0)) -> Image.Image:
        draw = ImageDraw.Draw(img)
        text_start_height = 60

        for text_line in text:
            font = ImageFont.truetype(self.rightFontLocation, font_size)
            (text_width, text_height), (_, _) = font.font.getsize(text_line)

            while text_width > 1297:
                font = ImageFont.truetype(self.rightFontLocation, font_size)
                (text_width, text_height), (_, _) = font.font.getsize(text_line)
                font_size -= 1
            draw.text((928, text_start_height), text_line, font=font, fill=rgb)
            text_start_height += text_height + 50
        return img