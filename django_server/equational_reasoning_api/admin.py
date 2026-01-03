from django.contrib import admin
from .models import EquationalProof, EquationalProofLine


@admin.register(EquationalProof)
class EquationalProofAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'tag', 'user', 'current_side', 'is_valid', 'is_complete', 'created_at']
    list_filter = ['is_valid', 'is_complete', 'current_side', 'created_at']
    search_fields = ['name', 'tag', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EquationalProofLine)
class EquationalProofLineAdmin(admin.ModelAdmin):
    list_display = ['id', 'proof', 'side', 'line_number', 'rule', 'created_at']
    list_filter = ['side', 'created_at']
    search_fields = ['racket', 'rule']
    readonly_fields = ['created_at']

