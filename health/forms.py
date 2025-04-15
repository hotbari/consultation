from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import ConsultationSlot
from django.utils import timezone
import json

User = get_user_model()

class CustomDateTimeWidget(forms.DateTimeInput):
    def __init__(self, attrs=None):
        default_attrs = {'type': 'datetime-local', 'class': 'form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Add data attributes for JavaScript to use
        context['widget']['attrs'].update({
            'data-time-options': json.dumps(['00', '30']),  # Only allow 00 and 30 minutes
        })
        return context

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'name', 'cohort', 'track', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cohort'].label = '기수'
        self.fields['track'].label = '트랙'

class AdminRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'name', 'track', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['track'].label = '트랙'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_admin = True
        user.is_staff = True
        if commit:
            user.save()
        return user

class ConsultationForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=CustomDateTimeWidget(),
        label='상담 시작 시간'
    )
    
    class Meta:
        model = ConsultationSlot
        fields = ['start_time']
        
    def clean_start_time(self):
        start_time = self.cleaned_data['start_time']
        if start_time < timezone.now():
            raise forms.ValidationError('과거 시간은 선택할 수 없습니다.')
        
        # 시간 제한 검사
        if start_time.hour < 10 or start_time.hour >= 19:
            raise forms.ValidationError('상담은 오전 10시부터 오후 7시까지만 가능합니다.')
        
        # 30분 단위 검사
        if start_time.minute not in [0, 30]:
            raise forms.ValidationError('상담은 정각 또는 30분에만 예약할 수 있습니다.')
        
        # 기본 상담 시간은 30분으로 설정
        end_time = start_time + timezone.timedelta(minutes=30)
        
        # 중복 예약 확인
        if 'user' in self.initial:
            user = self.initial['user']
            overlapping_slots = ConsultationSlot.objects.filter(
                user=user,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if overlapping_slots.exists():
                raise forms.ValidationError('선택한 시간에 이미 예약된 상담이 있습니다.')
        
        return start_time

class AdminConsultationForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=CustomDateTimeWidget(),
        label='상담 시작 시간'
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_admin=False),
        label='사용자',
        required=False
    )
    
    class Meta:
        model = ConsultationSlot
        fields = ['start_time', 'user']
    
    def __init__(self, *args, **kwargs):
        track = kwargs.pop('track', None)
        super().__init__(*args, **kwargs)
        
        if track:
            self.fields['user'].queryset = User.objects.filter(is_admin=False, track=track)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        user = cleaned_data.get('user')
        
        if start_time:
            # 시간 제한 검사
            if start_time.hour < 10 or start_time.hour >= 19:
                raise forms.ValidationError('상담은 오전 10시부터 오후 7시까지만 가능합니다.')
            
            # 30분 단위 검사
            if start_time.minute not in [0, 30]:
                raise forms.ValidationError('상담은 정각 또는 30분에만 예약할 수 있습니다.')
            
            # 기본 상담 시간은 30분으로 설정
            end_time = start_time + timezone.timedelta(minutes=30)
            
            if user:
                # 중복 예약 확인
                overlapping_slots = ConsultationSlot.objects.filter(
                    user=user,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )
                if self.instance.pk:
                    overlapping_slots = overlapping_slots.exclude(pk=self.instance.pk)
                
                if overlapping_slots.exists():
                    raise forms.ValidationError('선택한 사용자는 이 시간에 이미 다른 상담이 예약되어 있습니다.')
        
        return cleaned_data