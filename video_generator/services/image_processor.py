"""
Xử lý image - tạo thumbnail, optimize, etc.
"""

import os
import logging
from PIL import Image
from django.core.files.base import ContentFile
from ..models import VideoRequest

logger = logging.getLogger(__name__)


def create_thumbnail(video_request_id, width=320, height=180):
    """
    Tạo thumbnail từ image upload

    Args:
        video_request_id: ID của VideoRequest
        width: Chiều rộng thumbnail
        height: Chiều cao thumbnail
    """
    try:
        video_request = VideoRequest.objects.get(id=video_request_id)

        # Mở image
        image = Image.open(video_request.image.path)

        # Resize thumbnail
        image.thumbnail((width, height), Image.Resampling.LANCZOS)

        # Lưu thumbnail
        thumb_filename = f'thumb_{video_request_id}.jpg'
        thumb_path = os.path.join('thumbnails', thumb_filename)

        # Chuyển thành RGB nếu cần (ví dụ RGBA -> RGB)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Tạo background trắng
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background

        # Lưu file
        image_io = image.tobytes()
        img_temp = Image.new('RGB', image.size)
        img_temp.frombytes(image_io)

        from io import BytesIO
        thumb_io = BytesIO()
        image.save(thumb_io, format='JPEG', quality=85)
        thumb_io.seek(0)

        video_request.thumbnail.save(
            thumb_filename,
            ContentFile(thumb_io.read()),
            save=True
        )

        logger.info(f"✅ Thumbnail tạo thành công cho video {video_request_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Lỗi tạo thumbnail: {str(e)}")
        return False


def optimize_image(image_path, max_width=1024, max_height=1024):
    """
    Optimize image trước khi gửi lên Replicate

    Args:
        image_path: Đường dẫn file image
        max_width: Chiều rộng tối đa
        max_height: Chiều cao tối đa

    Returns:
        Đường dẫn file đã optimize
    """
    try:
        image = Image.open(image_path)

        # Resize nếu quá lớn
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Lưu tạm
        from io import BytesIO
        optimized = BytesIO()
        image.save(optimized, format='JPEG', quality=90)
        optimized.seek(0)

        return optimized

    except Exception as e:
        logger.error(f"❌ Lỗi optimize image: {str(e)}")
        return None


def validate_image(image_path):
    """
    Kiểm tra image có hợp lệ không

    Returns:
        (is_valid, error_message)
    """
    try:
        if not os.path.exists(image_path):
            return False, "File không tồn tại"

        image = Image.open(image_path)
        image.verify()

        # Kiểm tra format
        if image.format not in ['JPEG', 'PNG', 'JPG']:
            return False, f"Format không được hỗ trợ: {image.format}"

        # Kiểm tra kích thước
        width, height = image.size
        if width < 256 or height < 256:
            return False, f"Image quá nhỏ: {width}x{height} (tối thiểu 256x256)"

        if width > 4096 or height > 4096:
            return False, f"Image quá lớn: {width}x{height} (tối đa 4096x4096)"

        return True, ""

    except Exception as e:
        return False, str(e)
