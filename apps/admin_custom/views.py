"""
Admin custom views for E-RECYCLO
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone

from apps.accounts.models import Account, ProfileCompletion
from apps.client.models import PhotoPost
from apps.payments.models import WithdrawalRequest


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_superuser or user.is_admin)


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Admin dashboard with high-fidelity stats"""
    
    # Get stats
    total_users = Account.objects.filter(is_superuser=False).count()
    pending_approvals = ProfileCompletion.objects.filter(
        approval_status='pending',
        profile_submitted=True
    ).count()
    total_uploads = PhotoPost.objects.count()
    pending_withdrawals = WithdrawalRequest.objects.filter(
        status='pending'
    ).count()
    
    # Recent activity
    recent_uploads = PhotoPost.objects.all().order_by('-created_at')[:5]
    recent_users = Account.objects.filter(
        is_superuser=False
    ).order_by('-date_joined')[:5]
    
    # User Breakdown for charts/pills
    user_breakdown = {
        'clients': Account.objects.filter(is_client=True).count(),
        'vendors': Account.objects.filter(is_vendor=True).count(),
        'collectors': Account.objects.filter(is_collector=True).count(),
    }
    
    context = {
        'total_users': total_users,
        'pending_approvals': pending_approvals,
        'total_uploads': total_uploads,
        'pending_withdrawals': pending_withdrawals,
        'recent_uploads': recent_uploads,
        'recent_users': recent_users,
        'user_breakdown': user_breakdown,
    }
    
    return render(request, 'admin_custom/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def pending_approvals(request):
    """View pending profile approvals"""
    
    approvals = ProfileCompletion.objects.filter(
        approval_status='pending',
        profile_submitted=True
    ).select_related('user').order_by('-submitted_at')
    
    context = {
        'approvals': approvals,
    }
    
    return render(request, 'admin_custom/pending_approvals.html', context)


@login_required
@user_passes_test(is_admin)
def approve_profile(request, pk):
    """Approve a profile"""
    
    profile = get_object_or_404(ProfileCompletion, pk=pk)
    
    if request.method == 'POST':
        profile.approval_status = 'approved'
        profile.admin_reviewed = True
        profile.admin_reviewed_by = request.user
        profile.approved_at = timezone.now()
        profile.admin_remarks = request.POST.get('remarks', '')
        profile.save()
        
        # Send approval email
        from apps.notifications.utils import send_profile_approved_email
        send_profile_approved_email(profile.user)
        
        messages.success(request, f'Profile approved for {profile.user.email}')
        return redirect('admin_custom:pending_approvals')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'admin_custom/approve_profile.html', context)


@login_required
@user_passes_test(is_admin)
def reject_profile(request, pk):
    """Reject a profile"""
    
    profile = get_object_or_404(ProfileCompletion, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, 'Please provide a reason for rejection.')
            return redirect('admin_custom:pending_approvals')
        
        profile.approval_status = 'rejected'
        profile.admin_reviewed = True
        profile.admin_reviewed_by = request.user
        profile.admin_remarks = reason
        profile.save()
        
        # Send rejection email
        from apps.notifications.utils import send_profile_rejected_email
        send_profile_rejected_email(profile.user, reason)
        
        messages.success(request, f'Profile rejected for {profile.user.email}')
        return redirect('admin_custom:pending_approvals')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'admin_custom/reject_profile.html', context)


@login_required
@user_passes_test(is_admin)
def users(request):
    """View all users"""
    
    role = request.GET.get('role', '')
    
    users = Account.objects.filter(is_superuser=False)
    
    if role == 'client':
        users = users.filter(is_client=True)
    elif role == 'vendor':
        users = users.filter(is_vendor=True)
    elif role == 'collector':
        users = users.filter(is_collector=True)
    
    users = users.order_by('-date_joined')
    
    # Get counts
    counts = {
        'all': Account.objects.filter(is_superuser=False).count(),
        'clients': Account.objects.filter(is_client=True).count(),
        'vendors': Account.objects.filter(is_vendor=True).count(),
        'collectors': Account.objects.filter(is_collector=True).count(),
    }
    
    context = {
        'users': users,
        'role': role,
        'counts': counts,
    }
    
    return render(request, 'admin_custom/users.html', context)


@login_required
@user_passes_test(is_admin)
def analytics(request):
    """View analytics with user-type switching"""
    import datetime
    
    user_type = request.GET.get('user_type', 'all')
    current_year = timezone.now().year
    
    # Filter users based on type
    user_qs = Account.objects.filter(is_superuser=False)
    if user_type == 'client':
        user_qs = user_qs.filter(is_client=True)
    elif user_type == 'vendor':
        user_qs = user_qs.filter(is_vendor=True)
    elif user_type == 'collector':
        user_qs = user_qs.filter(is_collector=True)

    monthly_uploads = []
    monthly_users = []
    
    for month in range(1, 13):
        uploads = PhotoPost.objects.filter(
            created_at__year=current_year,
            created_at__month=month
        ).count()
        
        new_users = user_qs.filter(
            date_joined__year=current_year,
            date_joined__month=month
        ).count()
        
        # We need a date object for the month filtering in templates usually, 
        # or just the name. Let's pass a dummy date for formatting.
        m_date = datetime.date(current_year, month, 1)
        monthly_uploads.append({'month': m_date, 'count': uploads})
        monthly_users.append({'month': m_date, 'count': new_users})
    
    # Overall statistics
    counts = {
        'all': Account.objects.filter(is_superuser=False).count(),
        'clients': Account.objects.filter(is_client=True).count(),
        'vendors': Account.objects.filter(is_vendor=True).count(),
        'collectors': Account.objects.filter(is_collector=True).count(),
    }
    
    # Fix the Sum aggregation issue (handle None)
    total_val_agg = PhotoPost.objects.filter(status='completed').aggregate(total=Sum('vendor_final_value'))
    total_value = total_val_agg['total'] or 0
    max_uploads = max((m['count'] for m in monthly_uploads), default=0)
    max_users = max((m['count'] for m in monthly_users), default=0)
    
    context = {
        'monthly_uploads': monthly_uploads,
        'monthly_users': monthly_users,
        'total_value': total_value,
        'current_year': current_year,
        'counts': counts,
        'user_type': user_type,
        'max_uploads': max_uploads,
        'max_users': max_users,
    }
    
    return render(request, 'admin_custom/analytics.html', context)


# --- GENERIC CRUD SYSTEM ---

from django.apps import apps
from django.forms import modelform_factory
from django.core.paginator import Paginator

@login_required
@user_passes_test(is_admin)
def model_list(request):
    """List all managed apps and their models"""
    # Filter only relevant apps
    exclude_prefixes = ['django.', 'auth.', 'contenttypes.', 'sessions.', 'admin.']
    all_models = apps.get_models()
    
    apps_dict = {}
    for model in all_models:
        app_label = model._meta.app_label
        # Exclude internal django stuff unless requested? 
        # Let's keep it simple and show everything starting with our apps
        if not any(app_label.startswith(p) for p in ['django', 'sessions', 'contenttypes', 'admin']):
            if app_label not in apps_dict:
                apps_dict[app_label] = []
            apps_dict[app_label].append({
                'name': model._meta.verbose_name.title(),
                'model_name': model._meta.model_name,
                'count': model.objects.count(),
                'url_name': f"{app_label}_{model._meta.model_name}"
            })

    context = {
        'apps': apps_dict,
    }
    return render(request, 'admin_custom/model_list.html', context)


@login_required
@user_passes_test(is_admin)
def model_items(request, app_label, model_name):
    """List instances of a specific model with smart field selection"""
    model = apps.get_model(app_label, model_name)
    
    search_query = request.GET.get('q', '')
    queryset = model.objects.all().order_by('-id')
    
    # Smarter search
    if search_query:
        fields = [f.name for f in model._meta.fields]
        from django.db.models import Q
        q_obj = Q()
        searchable_suffixes = ['name', 'title', 'email', 'username', 'remarks', 'phone', 'address', 'company']
        for field in fields:
            if any(suffix in field.lower() for suffix in searchable_suffixes):
                q_obj |= Q(**{f"{field}__icontains": search_query})
        queryset = queryset.filter(q_obj)

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # SMART FIELD SELECTION for the table columns
    all_fields = model._meta.fields
    # Exclude technical/large fields
    display_fields = []
    excluded_names = ['id', 'password', 'last_login', 'is_superuser', 'created_at', 'updated_at', 'deleted_at']
    
    for f in all_fields:
        if f.name not in excluded_names and len(display_fields) < 5:
            display_fields.append({
                'name': f.name,
                'label': f.verbose_name.title()
            })

    # Prepare data for template
    items_data = []
    for item in page_obj:
        row = {
            'id': item.id,
            'str': str(item),
            'fields': []
        }
        for f in display_fields:
            val = getattr(item, f['name'])
            # Handle special types
            if hasattr(val, 'all'): # ManyToMany (though _meta.fields usually doesn't include it)
                val = ", ".join([str(x) for x in val.all()[:2]])
            elif hasattr(val, 'url'): # File/Image
                val = "File Attached"
            row['fields'].append(val)
        items_data.append(row)

    context = {
        'model_name': model._meta.verbose_name.title(),
        'app_label': app_label,
        'model_meta_name': model_name,
        'page_obj': page_obj,
        'headers': [f['label'] for f in display_fields],
        'items_data': items_data,
        'search_query': search_query,
    }
    return render(request, 'admin_custom/model_items.html', context)


@login_required
@user_passes_test(is_admin)
def model_edit(request, app_label, model_name, pk=None):
    """Create or Edit a model instance"""
    model = apps.get_model(app_label, model_name)
    instance = get_object_or_404(model, pk=pk) if pk else None
    
    # Generic form
    GenericForm = modelform_factory(model, exclude=[])
    
    if request.method == 'POST':
        form = GenericForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{model._meta.verbose_name} saved successfully.")
            return redirect('admin_custom:model_items', app_label=app_label, model_name=model_name)
    else:
        form = GenericForm(instance=instance)

    context = {
        'form': form,
        'model_name': model._meta.verbose_name.title(),
        'instance': instance,
        'app_label': app_label,
        'model_meta_name': model_name,
    }
    return render(request, 'admin_custom/model_form.html', context)


@login_required
@user_passes_test(is_admin)
def model_delete(request, app_label, model_name, pk):
    """Delete a model instance"""
    model = apps.get_model(app_label, model_name)
    instance = get_object_or_404(model, pk=pk)
    
    if request.method == 'POST':
        instance.delete()
        messages.success(request, f"{model._meta.verbose_name} deleted successfully.")
        return redirect('admin_custom:model_items', app_label=app_label, model_name=model_name)
    
    return render(request, 'admin_custom/model_confirm_delete.html', {
        'instance': instance,
        'model_name': model._meta.verbose_name.title(),
        'app_label': app_label,
        'model_meta_name': model_name,
    })