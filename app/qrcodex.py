# coding: utf-8
import os
import base64
from io import BytesIO
try:
    from urllib import urlopen  # py2
except:
    from urllib.request import urlopen  # py3
from PIL import Image
import qrcode as qrc
from flask_qrcode import QRcode


class QRcodeEx(QRcode):
    """Generate QR Code image"""
    color = ['red', 'maroon', 'olive', 'yellow', 'lime', 'green',
             'aqua', 'teal', 'blue', 'navy', 'fuchsia', 'purple',
             'white', 'silver', 'gray', 'black']

    correction_levels = {
        'L': qrc.constants.ERROR_CORRECT_L,
        'M': qrc.constants.ERROR_CORRECT_M,
        'Q': qrc.constants.ERROR_CORRECT_Q,
        'H': qrc.constants.ERROR_CORRECT_H
    }

    def __init__(self, app=None, config_jinja=True, **kwargs):
        super(QRcodeEx, self).__init__(app, **kwargs)
        self.app = app
        self._config_jinja = config_jinja

        if app:
            self.init_app(app)

    def __call__(self, *args, **kwargs):
        if self.app:
            return self.qrcode(
                static_dir=self.app.static_folder, *args, **kwargs)
        return self.qrcode(*args, **kwargs)

    def init_app(self, app):
        self.app = app
        self.register_blueprint(app)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['qrcode'] = self

        if self._config_jinja:
            self._qrcode = self.__call__
            app.add_template_filter(self._qrcode, 'qrcode')
            app.add_template_global(self._qrcode, 'qrcode')

    @classmethod
    def qrcode(cls, data, mode="base64", version=None, error_correction="L", box_size=10,
               border=0, fit=True, fill_color="black", back_color="white", **kwargs):
        """
        Makes qr image using qrcode as qrc. See documentation
        for qrcode package for info.

        :param data: String data.
        :param mode: Output mode, [base64|raw].
        :param version: The size of the QR Code (1-40).
        :param error_correction: The error correction used for the QR Code.
        :param box_size: How many pixels each "box" of the QR code.
        :param border: The number of box for border.
        :param fit: If `True`, find the best fit for the data.
        :param fill_color: Frontend color.
        :param back_color: Background color.

        :param icon_img: Small icon image name or url.
        :param factor: Resize for icon image (default: 4, one-fourth of QRCode)
        :param icon_box: Icon image position [left, top] (default: image center)
        """
        qr = qrc.QRCode(
            version=version,
            error_correction=cls.correction_levels[error_correction],
            box_size=box_size,
            border=border
        )
        qr.add_data(data)
        qr.make(fit=fit)

        fcolor = fill_color if fill_color.lower() in cls.color or \
            fill_color.startswith('#') else "#"+fill_color
        bcolor = back_color if back_color.lower() in cls.color or \
            back_color.startswith('#') else "#"+back_color

        # creates qrcode base64
        out = BytesIO()
        img = qr.make_image(back_color=fcolor, fill_color=bcolor)
        img = img.convert('RGBA')
        img = cls._insert_img(img, **kwargs)
        img.save(out, 'PNG')
        out.seek(0)

        if mode == 'base64':
            return u"data:image/png;base64," + base64.b64encode(out.getvalue()).decode('ascii')
        elif mode == 'raw':
            return out

    @staticmethod
    def _insert_img(qr_img, icon_img=None, factor=4, icon_box=None, static_dir=None):
        """Insert small icon to QR Code image"""
        img_w, img_h = qr_img.size  # 二维码大小
        size_w = int(img_w) / int(factor)
        size_h = int(img_h) / int(factor)

        try:
            # load icon from current dir
            icon_fp = os.path.join(icon_img)  # 当前目录图片
            if static_dir:
                # load icon from app's static dir
                icon_fp = os.path.join(static_dir, icon_img)  # 本地图片
            if icon_img.split('://')[0] in ['http', 'https', 'ftp']:  # 网络图片
                icon_fp = BytesIO(urlopen(icon_img).read())
            icon = Image.open(icon_fp)
        except:
            return qr_img

        icon_w, icon_h = icon.size  # 小图标大小
        icon_w = size_w if icon_w > size_w else icon_w
        icon_h = size_h if icon_h > size_h else icon_h
        icon = icon.resize((int(icon_w), int(icon_h)), Image.ANTIALIAS)  # 调整小图标
        icon = icon.convert('RGBA')  # 一些图片不具备 alpha 通道, 需要转换

        left = int((img_w - icon_w) / 2)
        top = int((img_h - icon_h) / 2)
        icon_box = (int(icon_box[0]), int(icon_box[1])) if icon_box else (left, top)
        qr_img.paste(im=icon, box=icon_box, mask=icon)  # 插入小图标
        return qr_img
