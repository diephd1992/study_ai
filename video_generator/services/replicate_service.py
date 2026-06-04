"""
Replicate AI Service - Tạo video từ image và text
"""

import os
import logging
import replicate
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from urllib.request import urlopen
from ..models import VideoRequest, ProcessingLog

logger = logging.getLogger(__name__)

# Các model có sẵn trên Replicate
REPLICATE_MODELS = {
    'stable-video-diffusion': 'stability-ai/stable-video-diffusion:725b4268b87c3e3a4a4b7c1e10e0e8e8',
    'animatediff': 'deforum-art/animatediff-text2video:d402edfa90fef0c7d9cc2d5f01c3c59e11aacf10',
    'damo-vilab-text2video': 'damo-vilab/text-to-video-ms:70577b2b65908111cc4de4e83014ff66a28c910fe669ebbb4751dbc51b678e62',
}


def add_log(video_request, message, log_type='info'):
    """Ghi log xử lý"""
    ProcessingLog.objects.create(
        video_request=video_request,
        message=message,
        log_type=log_type
    )
    logger.log(
        level=getattr(logging, log_type.upper()),
        msg=f"Video {video_request.id}: {message}"
    )


def generate_video_with_replicate(video_request_id, model='stable-video-diffusion'):
    """
    Tạo video bằng Replicate API

    Args:
        video_request_id: ID của VideoRequest
        model: Tên model ('stable-video-diffusion', 'animatediff', etc.)

    Returns:
        True nếu thành công, False nếu thất bại
    """
    try:
        # Lấy video request
        video_request = VideoRequest.objects.get(id=video_request_id)
        add_log(video_request, f"Bắt đầu xử lý với model: {model}")

        # Đánh dấu đang xử lý
        video_request.mark_processing()

        # Lấy API token
        api_token = os.getenv('REPLICATE_API_TOKEN')
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN không được cấu hình")

        # Khởi tạo Replicate client
        client = replicate.Client(api_token=api_token)

        # Đọc image file
        image_path = video_request.image.path
        add_log(video_request, f"Đang đọc image từ: {image_path}")

        # Chọn model dựa trên yêu cầu
        model_version = REPLICATE_MODELS.get(model, REPLICATE_MODELS['stable-video-diffusion'])
        add_log(video_request, f"Sử dụng model version: {model_version}")

        # Chuẩn bị input tùy theo model
        if model == 'stable-video-diffusion':
            # Stable Video Diffusion - tạo video từ image
            with open(image_path, 'rb') as f:
                input_data = {
                    "image": f,
                    "seed": 42,
                    "steps": 25,
                    "cfg": 7.0,
                    "motion_bucket_id": 127,
                    "fps": video_request.fps,
                }
            add_log(video_request, "Khởi chạy Stable Video Diffusion...")

        elif model == 'animatediff':
            # AnimateDiff - tạo video từ text
            input_data = {
                "prompt": video_request.text_prompt,
                "negative_prompt": "low quality, bad quality",
                "num_frames": video_request.duration * video_request.fps,
                "guidance_scale": 7.5,
                "seed": 42,
            }
            add_log(video_request, f"Khởi chạy AnimateDiff với prompt: {video_request.text_prompt}")

        elif model == 'damo-vilab-text2video':
            # DAMO-VILAB Text-to-Video
            input_data = {
                "text": video_request.text_prompt,
                "negative_prompt": "low quality, bad quality",
                "num_frames": video_request.duration * video_request.fps,
                "guidance_scale": 7.5,
            }
            add_log(video_request, f"Khởi chạy DAMO-VILAB với prompt: {video_request.text_prompt}")

        else:
            raise ValueError(f"Model không được hỗ trợ: {model}")

        # Gọi Replicate API
        output = client.run(
            model_version,
            input=input_data
        )

        add_log(video_request, f"Replicate API trả về kết quả")

        if not output:
            raise ValueError("Replicate không trả về output")

        # Output có thể là URL hoặc list URLs
        if isinstance(output, list) and len(output) > 0:
            video_url = output[0] if isinstance(output[0], str) else output
        else:
            video_url = output

        add_log(video_request, f"Video URL: {video_url}")

        # Download video từ Replicate
        add_log(video_request, "Đang download video...")
        response = urlopen(video_url)
        video_content = response.read()

        # Lưu video file
        filename = f'video_{video_request_id}.mp4'
        video_request.video_file.save(
            filename,
            ContentFile(video_content),
            save=True
        )
        add_log(video_request, f"Video đã lưu: {filename}")

        # Đánh dấu hoàn thành
        video_request.mark_completed()
        add_log(video_request, "Xử lý hoàn thành!")

        logger.info(f"✅ Video {video_request_id} tạo thành công")
        return True

    except VideoRequest.DoesNotExist:
        logger.error(f"❌ VideoRequest {video_request_id} không tồn tại")
        return False

    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo video {video_request_id}: {str(e)}")
        try:
            video_request = VideoRequest.objects.get(id=video_request_id)
            video_request.mark_failed(str(e))
            add_log(video_request, f"Lỗi: {str(e)}", log_type='error')
        except:
            pass
        return False


def get_video_status(video_request_id):
    """Lấy status của video"""
    try:
        video_request = VideoRequest.objects.get(id=video_request_id)
        return {
            'id': video_request.id,
            'status': video_request.status,
            'title': video_request.title,
            'video_url': video_request.video_file.url if video_request.video_file else None,
            'error_message': video_request.error_message,
            'processing_time': video_request.processing_time,
            'created_at': video_request.created_at,
            'completed_at': video_request.completed_at,
        }
    except VideoRequest.DoesNotExist:
        return None
