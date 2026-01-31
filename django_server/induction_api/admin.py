from django.contrib import admin
from .models import InductionProof, InductionProofLine


class InductionProofLineInline(admin.TabularInline):
    model = InductionProofLine
    extra = 0
    fields = ('case', 'side', 'line_number', 'racket', 'rule', 'start_position')
    readonly_fields = ('created_at',)
    ordering = ('case', 'side', 'line_number')


@admin.register(InductionProof)
class InductionProofAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'proof_type', 'induction_variable', 'created_at', 'is_valid')
    list_filter = ('proof_type', 'induction_type', 'is_valid', 'created_at')
    search_fields = ('name', 'tag', 'user__username', 'induction_variable')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [InductionProofLineInline]
    
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
            'fields': ('current_side', 'current_goal', 'is_anchor_case', 'is_valid')
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
    
    def racket_preview(self, obj):
        return obj.racket[:50] + '...' if len(obj.racket) > 50 else obj.racket
    racket_preview.short_description = 'Racket Expression'
