# video_generator/services/ai_video_generator.py

import replicate
import os
from django.core.files.base import ContentFile
from ..models import VideoRequest


def generate_video_with_replicate(image_path, text_prompt):
    """Dùng Replicate API để tạo video"""
    client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

    # Ví dụ: dùng model Runway Gen3
    output = client.run(
        "stability-ai/stable-video-diffusion:725b4268b87c3e3a4a4b7c1e10e0e8e8",
        input={
            "image": open(image_path, "rb"),
            "motion": text_prompt,
        }
    )

    return output


def generate_video_with_stable_diffusion(image_path, text_prompt):
    """Dùng Stable Diffusion local"""
    from diffusers import StableDiffusionPipeline
    import torch

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16
    ).to("cuda")

    # Tạo video từ image + text
    # Logic tùy chỉnh

    return video_path


def save_video_to_model(video_request_id, video_url):
    """Lưu video vào database"""
    video_request = VideoRequest.objects.get(id=video_request_id)

    # Download video và lưu
    import requests
    response = requests.get(video_url)
    video_request.video_file.save(
        f'video_{video_request_id}.mp4',
        ContentFile(response.content)
    )
    video_request.status = 'completed'
    video_request.save()