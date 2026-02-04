from django.contrib import admin
from .models import Assignment, AssignmentSubmission, Term
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
        row = [getattr(obj, field.name) for field in fields]
        writer.writerow(row)
    
    return response

export_to_csv.short_description = "Export selected to CSV"


class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'due_date', 'term_instructor', 'created_at', 'updated_at', 'created_by')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                    "due_date",
                    "term",
                    "created_by",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "title",
                    "description",
                    "due_date",
                    "term",
                    "created_by",
                ),
            },
        ),
    )
    ordering = ('title',)

    def term_instructor(self, obj):
        return obj.term.instructor if obj.term else None
    term_instructor.short_description = "Instructor"
    term_instructor.admin_order_field = "term__instructor"

class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submission_date', 'grade')
    search_fields = ('assignment', 'student')
    readonly_fields = ('submission_date',)
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('assignment', 'student', 'proofs', 'grade')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('assignment', 'student', 'proofs', 'grade')
        }),
    )
    ordering = ('assignment',)

class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'instructor', 'created_by', 'created_at', 'updated_at')
    search_fields = ("name", "instructor")
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ((None, {"fields": ("name", "instructor", "students", "created_by")}),)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("name", "instructor", "students", "created_by"),
            },
        ),
    )
    ordering = ('name',)

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(AssignmentSubmission, AssignmentSubmissionAdmin)
admin.site.register(Term, TermAdmin)
