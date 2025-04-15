from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import UserRegisterForm, AdminRegisterForm, ConsultationForm, AdminConsultationForm
from .models import ConsultationSlot
from django.db.models import Q

User = get_user_model()

def home(request):
    return render(request, 'home.html')

def register_user(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '가입이 완료되었습니다!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form, 'user_type': '학생'})

def register_admin(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '관리자 가입이 완료되었습니다!')
            return redirect('home')
    else:
        form = AdminRegisterForm()
    return render(request, 'register.html', {'form': form, 'user_type': '관리자'})

@login_required
def user_schedule(request):
    user = request.user
    # 사용자의 상담 일정만 조회
    consultations = ConsultationSlot.objects.filter(user=user).order_by('start_time')
    
    # 과거 상담과 예정된 상담 분리
    past_consultations = consultations.filter(start_time__lt=timezone.now())
    upcoming_consultations = consultations.filter(start_time__gte=timezone.now())
    
    context = {
        'past_consultations': past_consultations,
        'upcoming_consultations': upcoming_consultations,
    }
    return render(request, 'user_schedule.html', context)

@login_required
def create_consultation(request):
    if request.method == 'POST':
        form = ConsultationForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.user = request.user
            consultation.created_by = request.user
            # 상담 종료 시간 (기본 30분)
            consultation.end_time = form.cleaned_data['start_time'] + timezone.timedelta(minutes=30)
            consultation.save()
            messages.success(request, '상담 신청이 완료되었습니다!')
            return redirect('user_schedule')
    else:
        form = ConsultationForm(initial={'user': request.user})
    
    return render(request, 'create_consultation.html', {'form': form})

@login_required
def admin_schedule(request):
    if not request.user.is_admin:
        messages.error(request, '관리자만 접근할 수 있습니다.')
        return redirect('home')
    
    # 필터링 옵션
    track = request.GET.get('track', request.user.track)  # 기본값은 관리자의 트랙
    cohort = request.GET.get('cohort')
    date = request.GET.get('date')
    
    # 관리자의 트랙에 맞는 학생들의 상담 일정 조회
    consultations = ConsultationSlot.objects.filter(
        Q(user__track=track) | Q(user__isnull=True)
    ).order_by('start_time')
    
    if cohort:
        consultations = consultations.filter(user__cohort=cohort)
    
    if date:
        date_obj = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        consultations = consultations.filter(
            start_time__date=date_obj
        )
    
    # 과거 상담과 예정된 상담 분리
    past_consultations = consultations.filter(start_time__lt=timezone.now())
    upcoming_consultations = consultations.filter(start_time__gte=timezone.now())
    
    # 기수 목록 (필터링용)
    cohorts = User.objects.filter(is_admin=False).values_list('cohort', flat=True).distinct()
    
    context = {
        'past_consultations': past_consultations,
        'upcoming_consultations': upcoming_consultations,
        'selected_track': track,
        'selected_cohort': cohort,
        'selected_date': date,
        'cohorts': cohorts,
    }
    return render(request, 'admin_schedule.html', context)

@login_required
def admin_create_consultation(request):
    if not request.user.is_admin:
        messages.error(request, '관리자만 접근할 수 있습니다.')
        return redirect('home')
    
    if request.method == 'POST':
        form = AdminConsultationForm(request.POST, track=request.user.track)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.created_by = request.user
            # 상담 종료 시간 (기본 30분)
            consultation.end_time = form.cleaned_data['start_time'] + timezone.timedelta(minutes=30)
            consultation.save()
            messages.success(request, '상담 일정이 생성되었습니다!')
            return redirect('admin_schedule')
    else:
        form = AdminConsultationForm(track=request.user.track)
    
    return render(request, 'create_consultation.html', {'form': form, 'is_admin': True})

@login_required
def assign_consultation(request, pk):
    if not request.user.is_admin:
        messages.error(request, '관리자만 접근할 수 있습니다.')
        return redirect('home')
    
    consultation = get_object_or_404(ConsultationSlot, pk=pk)
    
    if request.method == 'POST':
        form = AdminConsultationForm(request.POST, instance=consultation, track=request.user.track)
        if form.is_valid():
            form.save()
            messages.success(request, '상담 일정이 업데이트되었습니다!')
            return redirect('admin_schedule')
    else:
        form = AdminConsultationForm(instance=consultation, track=request.user.track)
    
    return render(request, 'create_consultation.html', {
        'form': form, 
        'is_admin': True,
        'is_update': True
    })

@login_required
def update_consultation_status(request, pk, status):
    if not request.user.is_admin:
        messages.error(request, '관리자만 접근할 수 있습니다.')
        return redirect('home')
    
    consultation = get_object_or_404(ConsultationSlot, pk=pk)
    
    if status not in ['CONFIRMED', 'COMPLETED', 'CANCELLED']:
        messages.error(request, '잘못된 상태값입니다.')
        return redirect('admin_schedule')
    
    consultation.status = status
    consultation.save()
    
    status_messages = {
        'CONFIRMED': '상담이 확정되었습니다.',
        'COMPLETED': '상담이 완료 처리되었습니다.',
        'CANCELLED': '상담이 취소되었습니다.'
    }
    
    messages.success(request, status_messages[status])
    return redirect('admin_schedule')