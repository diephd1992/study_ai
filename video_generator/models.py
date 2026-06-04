from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class VideoRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Thông tin cơ bản
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Input
    image = models.ImageField(upload_to='uploads/images/')
    text_prompt = models.TextField(help_text='Mô tả video bạn muốn tạo')

    # Configuration
    duration = models.IntegerField(default=5, help_text='Độ dài video (giây)')
    fps = models.IntegerField(default=8, help_text='Khung hình trên giây')

    # Output & Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    video_file = models.FileField(upload_to='videos/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)

    # Error tracking
    error_message = models.TextField(null=True, blank=True)

    # Metadata
    replicate_prediction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='ID từ Replicate API'
    )
    processing_time = models.FloatField(null=True, blank=True, help_text='Thời gian xử lý (giây)')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def mark_processing(self):
        """Đánh dấu video đang xử lý"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def mark_completed(self):
        """Đánh dấu video hoàn thành"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
        self.save(update_fields=['status', 'completed_at', 'processing_time'])

    def mark_failed(self, error_message):
        """Đánh dấu video thất bại"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
        self.save(update_fields=['status', 'error_message', 'completed_at', 'processing_time'])


class ProcessingLog(models.Model):
    """Ghi lại quá trình xử lý"""
    video_request = models.ForeignKey(VideoRequest, on_delete=models.CASCADE, related_name='logs')
    message = models.TextField()
    log_type = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('debug', 'Debug'),
        ],
        default='info'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.video_request.id} - {self.log_type}"
