from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)
        
        return self.create_user(email, name, password, **extra_fields)

class User(AbstractUser):
    TRACK_CHOICES = (
        ('FE', 'Frontend'),
        ('BE', 'Backend'),
    )
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    cohort = models.IntegerField(default=0)  # 기수
    track = models.CharField(max_length=2, choices=TRACK_CHOICES)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_track_display()}, {self.cohort}기)"

class ConsultationSlot(models.Model):
    STATUS_CHOICES = (
        ('PENDING', '대기중'),
        ('CONFIRMED', '확정'),
        ('COMPLETED', '완료'),
        ('CANCELLED', '취소'),
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_consultations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
        unique_together = ['start_time', 'user']  # 동일 시간에 동일 유저가 중복 예약 불가능
    
    def __str__(self):
        if self.user:
            return f"{self.user.name}의 상담 - {self.start_time.strftime('%Y-%m-%d %H:%M')} ({self.get_status_display()})"
        return f"빈 상담 슬롯 - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_past(self):
        return self.start_time < timezone.now()