import uuid
from django.db import models

class PipelineRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=32, default="pending", 
                             choices=[('pending', 'Pending'), ('computing', 'Computing'), 
                                      ('exporting', 'Exporting'), ('publishing', 'Publishing'), 
                                      ('done', 'Done'), ('failed', 'Failed')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parameters = models.JSONField(default=dict)
    
    asset_raster_path = models.TextField(blank=True, null=True)
    asset_vector_path = models.TextField(blank=True, null=True)
    geoserver_layer = models.TextField(blank=True, null=True)
    
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.id} ({self.state})"


class GEEExportJob(models.Model):
    run = models.ForeignKey(PipelineRun, on_delete=models.CASCADE, related_name='gee_exports')
    export_type = models.CharField(max_length=32, choices=[('raster', 'Raster'), ('vector', 'Vector')])
    gee_task_id = models.TextField()
    status = models.CharField(max_length=32, default='submitted')
    asset_path = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'gee_task_id']),
        ]
        unique_together = ('run', 'export_type')

    def __str__(self):
        return f"Task {self.gee_task_id} - {self.status}"


class GeoServerSyncLog(models.Model):
    run = models.ForeignKey(PipelineRun, on_delete=models.CASCADE, related_name='gs_logs')
    layer_name = models.TextField()
    sync_time = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Sync {self.layer_name}: {'Success' if self.success else 'Failed'}"
