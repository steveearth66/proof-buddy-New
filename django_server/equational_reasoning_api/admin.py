from django.contrib import admin
from .models import EquationalProof, EquationalProofLine
import csv
from django.http import HttpResponse


def export_to_csv(modeladmin, request, queryset):
    """Export selected items to CSV"""
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name_plural}.csv'
    
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    
    # Write header
    writer.writerow([field.verbose_name for field in fields])
    
    # Write data rows
    for obj in queryset:
        row = [getattr(obj, field.name) for field in fields]
        writer.writerow(row)
    
    return response

export_to_csv.short_description = "Export selected to CSV"


@admin.register(EquationalProof)
class EquationalProofAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'tag', 'user', 'current_side', 'is_valid', 'is_complete', 'created_at']
    list_filter = ['is_valid', 'is_complete', 'current_side', 'created_at']
    search_fields = ['name', 'tag', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    actions = [export_to_csv]


@admin.register(EquationalProofLine)
class EquationalProofLineAdmin(admin.ModelAdmin):
    list_display = ['id', 'proof', 'side', 'line_number', 'rule', 'created_at']
    list_filter = ['side', 'created_at']
    search_fields = ['racket', 'rule']
    readonly_fields = ['created_at']
    actions = [export_to_csv]

