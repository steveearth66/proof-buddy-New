from django.contrib import admin
from .models import InductionProof, InductionProofLine
import csv
from django.http import HttpResponse


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


class InductionProofLineInline(admin.TabularInline):
    model = InductionProofLine
    extra = 0
    fields = ('case', 'side', 'line_number', 'racket', 'rule', 'start_position')
    readonly_fields = ('created_at',)
    ordering = ('case', 'side', 'line_number')


@admin.register(InductionProof)
class InductionProofAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'proof_type', 'induction_variable', 'created_at', 'is_active')
    list_filter = ('proof_type', 'induction_type', 'is_active', 'created_at')
    search_fields = ('name', 'tag', 'user__username', 'induction_variable')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [InductionProofLineInline]
    actions = [export_to_csv]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'tag', 'proof_type', 'induction_type')
        }),
        ('Proof Parameters', {
            'fields': ('induction_variable', 'anchor_value', 'leap_variable')
        }),
        ('Goals', {
            'fields': ('lhs_anchor_goal', 'rhs_anchor_goal', 'lhs_leap_goal', 'rhs_leap_goal')
        }),
        ('Inductive Hypothesis', {
            'fields': ('inductive_hypothesis_lhs', 'inductive_hypothesis_rhs')
        }),
        ('Current State', {
            'fields': ('current_side', 'current_goal', 'is_anchor_case', 'is_active')
        }),
        ('Definitions', {
            'fields': ('definition',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InductionProofLine)
class InductionProofLineAdmin(admin.ModelAdmin):
    list_display = ('proof', 'case', 'side', 'line_number', 'rule', 'racket_preview', 'created_at')
    list_filter = ('case', 'side', 'created_at')
    search_fields = ('proof__name', 'racket', 'rule')
    readonly_fields = ('created_at',)
    actions = [export_to_csv]
    
    def racket_preview(self, obj):
        return obj.racket[:50] + '...' if len(obj.racket) > 50 else obj.racket
    racket_preview.short_description = 'Racket Expression'
