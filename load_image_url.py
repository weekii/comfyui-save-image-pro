"""
ComfyUI Save Image Pro - Load Image from URL Node

从URL加载图像的节点，支持批量加载多个URL。
基于 comfyui-easyapi-nodes 的 LoadImageFromURL 实现。

@version: latest
@author: weekii
"""

import io
import logging
import numpy as np
import torch
import requests
from PIL import Image, ImageOps
from typing import Tuple, List

# 设置日志
logger = logging.getLogger(__name__)


def read_image_from_url(image_url: str, timeout: int = 30, verify_ssl: bool = True) -> Image.Image:
    """
    从URL读取图像
    
    Args:
        image_url: 图像URL地址
        
    Returns:
        PIL Image对象，如果失败返回None
    """
    try:
        timeout = max(1, int(timeout))
        headers = {"User-Agent": "ComfyUI-Save-Image-Pro/1.0"}

        # 创建会话并确保请求完成后释放连接
        with requests.Session() as session:
            session.keep_alive = False
            response = session.get(
                image_url,
                stream=True,
                verify=verify_ssl,
                timeout=timeout,
                headers=headers,
            )
            response.raise_for_status()  # 确保获得有效响应
            image_bytes = io.BytesIO(response.content)

        # 使用PIL打开图像并强制加载图像数据
        img = Image.open(image_bytes)
        img.load()  # 确保图像完全加载
        
        logger.info(f"Successfully loaded image from URL: {image_url}")
        return img
    except Exception as e:
        logger.error(f"Error reading image from URL {image_url}: {e}")
        return None


class LoadImageFromURLPro:
    """
    从远程URL地址加载图像 (Pro版本)
    
    支持批量加载多个URL，每行一个URL地址。
    返回图像张量和对应的遮罩。
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "urls": ("STRING", {
                    "multiline": True, 
                    "default": "", 
                    "dynamicPrompts": False,
                    "tooltip": "图像URL地址，每行一个URL"
                }),
                "timeout": ("INT", {
                    "default": 30,
                    "min": 1,
                    "max": 300,
                    "step": 1,
                    "tooltip": "单个URL请求超时时间（秒）"
                }),
                "verify_ssl": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "校验 HTTPS 证书；如遇自签名证书可关闭"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "masks")
    FUNCTION = "load_images"
    CATEGORY = "image"
    OUTPUT_IS_LIST = (True, True,)
    
    DESCRIPTION = """
### Load Image from URL

从远程URL地址加载图像。

**功能特点:**
- 支持批量加载多个URL
- 自动处理EXIF旋转
- 自动提取Alpha通道作为遮罩
- 支持多种图像格式

**使用方法:**
在文本框中输入图像URL，每行一个URL。
空行会被自动忽略。

**示例:**
```
https://example.com/image1.png
https://example.com/image2.jpg
https://example.com/image3.webp
```
"""

    def load_images(self, urls: str, timeout: int = 30, verify_ssl: bool = True) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        """
        从URL加载图像
        
        Args:
            urls: URL字符串，每行一个URL
            
        Returns:
            (images, masks) 元组，包含图像列表和遮罩列表
        """
        # 分割URL并过滤空行
        url_list = [url.strip() for url in urls.splitlines() if url.strip()]
        
        images = []
        masks = []
        
        for url in url_list:
            try:
                # 从URL读取图像
                img = read_image_from_url(url, timeout=timeout, verify_ssl=verify_ssl)
                
                if img is None:
                    logger.warning(f"Skipping failed URL: {url}")
                    continue
                
                # 处理EXIF旋转
                img = ImageOps.exif_transpose(img)
                
                # 处理特殊模式
                if img.mode == 'I':
                    img = img.point(lambda i: i * (1 / 255))
                
                # 转换为RGB
                image = img.convert("RGB")
                
                # 转换为张量 (H, W, C) -> (1, H, W, C)
                image_np = np.array(image).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image_np).unsqueeze(0)
                images.append(image_tensor)
                
                # 处理Alpha通道作为遮罩
                if 'A' in img.getbands():
                    mask = np.array(img.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    # 创建默认遮罩
                    mask = torch.zeros((image_np.shape[0], image_np.shape[1]), 
                                     dtype=torch.float32, device="cpu")
                
                masks.append(mask.unsqueeze(0))
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                continue
        
        if not images:
            logger.warning("No images were successfully loaded")
            # 返回空的默认图像和遮罩
            default_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            default_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
            return ([default_image], [default_mask])
        
        logger.info(f"Successfully loaded {len(images)} images from URLs")
        return (images, masks)


class LoadMaskFromURLPro:
    """
    从远程URL地址加载遮罩图像 (Pro版本)
    
    支持批量加载多个URL，并从指定的颜色通道提取遮罩。
    """
    
    _color_channels = ["red", "green", "blue", "alpha"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "urls": ("STRING", {
                    "multiline": True, 
                    "default": "", 
                    "dynamicPrompts": False,
                    "tooltip": "图像URL地址，每行一个URL"
                }),
                "timeout": ("INT", {
                    "default": 30,
                    "min": 1,
                    "max": 300,
                    "step": 1,
                    "tooltip": "单个URL请求超时时间（秒）"
                }),
                "verify_ssl": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "校验 HTTPS 证书；如遇自签名证书可关闭"
                }),
                "channel": (cls._color_channels, {
                    "default": cls._color_channels[0],
                    "tooltip": "用于提取遮罩的颜色通道"
                }),
            },
        }

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("masks",)
    FUNCTION = "load_masks"
    CATEGORY = "image"
    OUTPUT_IS_LIST = (True,)
    
    DESCRIPTION = """
### Load Mask from URL

从远程URL地址加载遮罩图像。

**功能特点:**
- 支持批量加载多个URL
- 可选择颜色通道提取遮罩
- 自动处理EXIF旋转
- Alpha通道自动反转

**通道说明:**
- red/green/blue: 从对应颜色通道提取
- alpha: 从透明通道提取（自动反转）
"""

    def load_masks(self, urls: str, timeout: int = 30, verify_ssl: bool = True, channel: str = "red") -> Tuple[List[torch.Tensor]]:
        """
        从URL加载遮罩
        
        Args:
            urls: URL字符串，每行一个URL
            channel: 颜色通道名称
            
        Returns:
            (masks,) 元组，包含遮罩列表
        """
        # 分割URL并过滤空行
        url_list = [url.strip() for url in urls.splitlines() if url.strip()]
        
        masks = []
        
        for url in url_list:
            try:
                # 从URL读取图像
                img = read_image_from_url(url, timeout=timeout, verify_ssl=verify_ssl)
                
                if img is None:
                    logger.warning(f"Skipping failed URL: {url}")
                    continue
                
                # 处理EXIF旋转
                img = ImageOps.exif_transpose(img)
                
                # 转换为RGBA
                if img.getbands() != ("R", "G", "B", "A"):
                    img = img.convert("RGBA")
                
                # 提取指定通道
                c = channel[0].upper()
                if c in img.getbands():
                    mask = np.array(img.getchannel(c)).astype(np.float32) / 255.0
                    mask = torch.from_numpy(mask)
                    # Alpha通道需要反转
                    if c == 'A':
                        mask = 1. - mask
                else:
                    # 创建默认遮罩
                    mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
                
                masks.append(mask.unsqueeze(0))
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                continue
        
        if not masks:
            logger.warning("No masks were successfully loaded")
            # 返回默认遮罩
            default_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
            return ([default_mask],)
        
        logger.info(f"Successfully loaded {len(masks)} masks from URLs")
        return (masks,)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "LoadImageFromURLPro": LoadImageFromURLPro,
    "LoadMaskFromURLPro": LoadMaskFromURLPro,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromURLPro": "Load Image from URL (Pro)",
    "LoadMaskFromURLPro": "Load Mask from URL (Pro)",
}
