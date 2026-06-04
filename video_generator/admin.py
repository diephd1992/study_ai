from django.contrib import admin
from .models import VideoRequest, ProcessingLog


@admin.register(VideoRequest)
class VideoRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'user',
        'status',
        'created_at',
        'processing_time'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = [
        'status',
        'video_file',
        'error_message',
        'processing_time',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'description', 'user')
        }),
        ('Input', {
            'fields': ('image', 'text_prompt')
        }),
        ('Cấu hình', {
            'fields': ('duration', 'fps')
        }),
        ('Output & Status', {
            'fields': ('status', 'video_file', 'thumbnail', 'error_message')
        }),
        ('Thời gian', {
            'fields': ('processing_time', 'started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'video_request', 'log_type', 'message', 'created_at']
    list_filter = ['log_type', 'created_at']
    search_fields = ['message', 'video_request__title']
    readonly_fields = ['created_at']
