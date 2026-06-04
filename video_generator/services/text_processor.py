"""
Xử lý text - validate prompt, optimize prompt, etc.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Các negative prompt phổ biến
DEFAULT_NEGATIVE_PROMPTS = {
    'quality': "low quality, bad quality, blurry, distorted",
    'artifacts': "artifacts, glitches, errors, watermark",
    'unsafe': "NSFW, nude, explicit",
    'common': "low quality, bad anatomy, distorted, blurry, watermark, signature"
}

# Từ khóa được hỗ trợ tốt
SUPPORTED_KEYWORDS = [
    'animation', 'motion', 'moving', 'walking', 'running', 'dancing',
    'flying', 'jumping', 'spinning', 'rotating', 'vibrating',
    'slow motion', 'fast motion', 'smooth', 'dynamic',
    '3d', 'realistic', 'photorealistic', 'cartoon', 'anime',
    'cinematic', 'professional', 'high quality', 'detailed',
]


def validate_prompt(prompt):
    """
    Kiểm tra prompt có hợp lệ không

    Args:
        prompt: Text prompt

    Returns:
        (is_valid, error_message, warning_message)
    """
    if not prompt or not isinstance(prompt, str):
        return False, "Prompt không được trống", ""

    prompt = prompt.strip()

    # Kiểm tra độ dài
    if len(prompt) < 5:
        return False, "Prompt quá ngắn (tối thiểu 5 ký tự)", ""

    if len(prompt) > 500:
        return False, "Prompt quá dài (tối đa 500 ký tự)", ""

    # Kiểm tra ký tự đặc biệt không hợp lệ
    invalid_chars = re.findall(r'[{}\\]', prompt)
    if invalid_chars:
        return False, f"Prompt chứa ký tự không hợp lệ: {invalid_chars}", ""

    # Cảnh báo nếu prompt không có từ khóa chuyển động
    motion_keywords = ['motion', 'moving', 'animation', 'action', 'dance', 'walk', 'run']
    has_motion = any(kw in prompt.lower() for kw in motion_keywords)
    warning = ""
    if not has_motion:
        warning = "Prompt không chứa từ khóa chuyển động. Kết quả video có thể không có chuyển động."

    return True, "", warning


def optimize_prompt(prompt):
    """
    Tối ưu prompt cho AI model

    Args:
        prompt: Text prompt

    Returns:
        Optimized prompt
    """
    prompt = prompt.strip()

    # Xóa các ký tự thừa
    prompt = re.sub(r'\s+', ' ', prompt)  # Xóa multiple spaces
    prompt = re.sub(r'[,;:]+', ',', prompt)  # Normalize punctuation

    # Thêm từ khóa chất lượng nếu chưa có
    if 'quality' not in prompt.lower() and 'high' not in prompt.lower():
        prompt = f"{prompt}, high quality, detailed"

    # Thêm từ khóa motion nếu chưa có
    if not any(kw in prompt.lower() for kw in ['motion', 'moving', 'animation', 'action']):
        prompt = f"{prompt}, smooth motion, dynamic"

    return prompt


def get_negative_prompt(prompt_type='common'):
    """
    Lấy negative prompt phù hợp

    Args:
        prompt_type: 'quality', 'artifacts', 'unsafe', 'common'

    Returns:
        Negative prompt string
    """
    return DEFAULT_NEGATIVE_PROMPTS.get(prompt_type, DEFAULT_NEGATIVE_PROMPTS['common'])


def estimate_processing_time(duration, fps):
    """
    Ước tính thời gian xử lý dựa vào duration và fps

    Args:
        duration: Độ dài video (giây)
        fps: Khung hình trên giây

    Returns:
        Ước tính thời gian (giây)
    """
    # Công thức ước tính (có thể điều chỉnh)
    total_frames = duration * fps

    # Mỗi frame mất ~15-30 giây xử lý tùy model
    estimated_time = total_frames * 20  # Lấy trung bình 20 giây/frame

    return estimated_time


def get_prompt_suggestions(base_prompt):
    """
    Đưa ra gợi ý cải thiện prompt

    Args:
        base_prompt: Prompt hiện tại

    Returns:
        List of suggestions
    """
    suggestions = []
    prompt_lower = base_prompt.lower()

    # Kiểm tra và gợi ý
    if 'animation' not in prompt_lower and 'animate' not in prompt_lower:
        suggestions.append("Thêm 'animation' hoặc 'animate' để chỉ rõ kiểu video")

    if 'smooth' not in prompt_lower and 'motion' not in prompt_lower:
        suggestions.append("Thêm 'smooth motion' để video mượt mà hơn")

    if 'cinematic' not in prompt_lower:
        suggestions.append("Thêm 'cinematic' để video có chất lượng chuyên nghiệp")

    if 'quality' not in prompt_lower and 'detailed' not in prompt_lower:
        suggestions.append("Thêm 'high quality' hoặc 'detailed' để cải thiện chất lượng")

    if len(base_prompt) < 20:
        suggestions.append("Prompt quá ngắn, cố gắng mô tả chi tiết hơn (tối thiểu 20 ký tự)")

    return suggestions


def create_short_description(prompt, max_length=50):
    """
    Tạo mô tả ngắn từ prompt

    Args:
        prompt: Text prompt
        max_length: Độ dài tối đa

    Returns:
        Mô tả ngắn
    """
    # Xóa các từ phổ biến
    common_words = ['quality', 'video', 'animation', 'motion', 'smooth', 'detailed', 'high', 'the', 'a']
    words = [w for w in prompt.split() if w.lower() not in common_words]

    description = ' '.join(words[:10])

    if len(description) > max_length:
        description = description[:max_length].rsplit(' ', 1)[0] + '...'

    return description
