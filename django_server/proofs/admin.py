from django.contrib import admin
from .models import Proof, Definition, ProofLine

# Register your models here.


class ProofAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'created_by', 'created_at')
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
                    'rule', 'start_position', 'created_at')
    search_fields = ('proof', 'racket')
    readonly_fields = ('created_at',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('proof', 'left_side',
         'racket', 'rule', 'start_position', 'errors')}),
    )
    ordering = ('proof',)

    def get_proof_tag(self, obj):
        return obj.proof.tag
    get_proof_tag.short_description = 'TAG'


admin.site.register(Proof, ProofAdmin)
admin.site.register(ProofLine, ProofLineAdmin)
admin.site.register(Definition)
