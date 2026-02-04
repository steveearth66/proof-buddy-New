from django.contrib import admin
from .models import Account, ActivateAccount, ResetPassword
from django.contrib.auth.admin import UserAdmin
import csv
from django.http import HttpResponse

# Register your models here.


def export_to_csv(modeladmin, request, queryset):
    """Export selected items to CSV"""
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name_plural}.csv'
    
    writer = csv.writer(response)
    
    # Get only concrete fields (exclude auto-created reverse relations)
    fields = [
        field for field in opts.get_fields() 
        if not field.many_to_many 
        and not field.one_to_many
        and (field.concrete or field.name == 'id')
    ]
    
    # Write header
    writer.writerow([field.name for field in fields])
    
    # Write data rows
    for obj in queryset:
        row = []
        for field in fields:
            try:
                value = getattr(obj, field.name, None)
                # Convert value to string, handle None and objects
                if value is None:
                    row.append('')
                else:
                    row.append(str(value))
            except Exception:
                row.append('')
        writer.writerow(row)
    
    return response

export_to_csv.short_description = "Export selected to CSV"


class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'date_joined', 'last_login',
                    'is_admin', 'is_staff', 'is_active', 'is_superuser', 'is_instructor')
    search_fields = ('email', 'username')
    readonly_fields = ('date_joined', 'last_login')
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('email', 'username')}),
        ('Permissions', {'fields': ('is_admin', 'is_staff',
         'is_active', 'is_superuser', 'is_instructor')}),
        ('Personal', {'fields': ('first_name', 'last_name')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2')
        }),
    )
    ordering = ('username',)


admin.site.register(Account, AccountAdmin)
admin.site.register(ActivateAccount)
admin.site.register(ResetPassword)
