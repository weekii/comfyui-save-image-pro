"""
图像保存策略模块

使用策略模式处理不同格式的图像保存逻辑。
"""

from .format_strategy import FormatStrategy
from .png_strategy import PNGStrategy
from .webp_strategy import WebPStrategy
from .avif_strategy import AVIFStrategy
from .jpeg_strategy import JPEGStrategy
from .jxl_strategy import JXLStrategy
from .tiff_strategy import TIFFStrategy
from .gif_strategy import GIFStrategy
from .bmp_strategy import BMPStrategy

__all__ = [
    'FormatStrategy',
    'PNGStrategy',
    'WebPStrategy', 
    'AVIFStrategy',
    'JPEGStrategy',
    'JXLStrategy',
    'TIFFStrategy',
    'GIFStrategy',
    'BMPStrategy'
]
