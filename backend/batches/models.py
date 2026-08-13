from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q

class Batch(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    sample_id = models.CharField(max_length=100, unique=True)
    batch_type = models.CharField(max_length=50)
    submitted_by = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    result = models.JSONField(null=True, blank=True)
    partner_webhook = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['batch_type']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['sample_id'], name='unique_sample_id')
        ]
    
    def __str__(self):
        return f"Batch {self.sample_id} - {self.status}"
    
    def can_transition_to(self, new_status):
        valid_transitions = {
            'queued': ['processing'],
            'processing': ['completed', 'failed'],
            'completed': [],
            'failed': ['processing'],  # Allow retry from failed
        }
        return new_status in valid_transitions.get(self.status, [])
    
    def update_status(self, new_status, user=None):
        """Thread-safe status update with locking"""
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])
        return self