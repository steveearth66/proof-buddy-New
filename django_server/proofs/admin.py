from django.contrib import admin
from .models import Proof, Definition, ProofLine
import csv
from django.http import HttpResponse

# Register your models here.


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
        row = []
        for field in fields:
            value = getattr(obj, field.name)
            # Convert value to string, handle None and objects
            if value is None:
                row.append('')
            else:
                row.append(str(value))
        writer.writerow(row)
    
    return response

export_to_csv.short_description = "Export selected to CSV"


class ProofAdmin(admin.ModelAdmin):
    list_display = ("name", "tag", "created_by", "created_at", "isComplete")
    search_fields = ("name", "tag")
    readonly_fields = ("created_at",)
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {"fields": ("name", "tag")}),
        (
            "Proof",
            {
                "fields": (
                    "lhs",
                    "rhs",
                    "definitions",
                    "isComplete",
                )
            },
        ),
        ("User", {"fields": ("created_by",)}),
    )
    ordering = ("name",)


class ProofLineAdmin(admin.ModelAdmin):
    list_display = (
        "proof",
        "get_proof_tag",
        "left_side",
        "racket",
        "rule",
        "start_position",
        "deleted",
        "created_at",
    )
    search_fields = ("proof", "racket")
    readonly_fields = ("created_at",)
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "proof",
                    "left_side",
                    "racket",
                    "rule",
                    "start_position",
                    "errors",
                    "deleted",
                )
            },
        ),
    )
    ordering = ("proof",)

    def get_proof_tag(self, obj):
        return obj.proof.tag

    get_proof_tag.short_description = "TAG"


class DefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "def_type",
        "expression",
        "notes",
        "created_at",
        "created_by",
    )
    search_fields = ("label",)
    readonly_fields = ("created_at",)
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ((None, {"fields": ("label", "def_type", "expression", "notes")}),)
    ordering = ("label",)


admin.site.register(Proof, ProofAdmin)
admin.site.register(ProofLine, ProofLineAdmin)
admin.site.register(Definition, DefinitionAdmin)
