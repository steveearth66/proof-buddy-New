from django.contrib import admin
from .models import Proof, Definition, ProofLine

# Register your models here.


class ProofAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'created_by', 'created_at', 'isComplete')
    search_fields = ('name', 'tag')
    readonly_fields = ('created_at',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('name', 'tag')}),
        ('Proof', {'fields': ('lsh', 'rsh', 'isComplete',)}),
        ('User', {'fields': ('created_by',)}),
    )
    ordering = ('name',)


class ProofLineAdmin(admin.ModelAdmin):
    list_display = ('proof', 'get_proof_tag', 'left_side', 'racket',
                    'rule', 'start_position', 'deleted', 'created_at')
    search_fields = ('proof', 'racket')
    readonly_fields = ('created_at',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('proof', 'left_side',
         'racket', 'rule', 'start_position', 'errors', 'deleted',)}),
    )
    ordering = ('proof',)

    def get_proof_tag(self, obj):
        return obj.proof.tag
    get_proof_tag.short_description = 'TAG'


class DefinitionAdmin(admin.ModelAdmin):
    list_display = ('proof', 'get_tag', 'label', 'def_type', 'expression',
                    'notes', 'created_at', 'created_by')
    search_fields = ('label',)
    readonly_fields = ('created_at',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('label', 'def_type', 'expression', 'notes')}),
    )
    ordering = ('label',)

    def get_tag(self, obj):
        return obj.proof.tag

    get_tag.short_description = 'TAG'


admin.site.register(Proof, ProofAdmin)
admin.site.register(ProofLine, ProofLineAdmin)
admin.site.register(Definition, DefinitionAdmin)
