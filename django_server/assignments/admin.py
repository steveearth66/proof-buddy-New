from django.contrib import admin
from .models import Assignment, AssignmentSubmission, Term

# Register your models here.

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'due_date', 'term_instructor', 'created_at', 'updated_at', 'created_by')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

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
    list_display = ('assignment', 'student', 'submission_date', 'submission', 'grade', 'created_at', 'updated_at')
    search_fields = ('assignment', 'student')
    readonly_fields = ('submission_date', 'created_at', 'updated_at')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('assignment', 'student', 'submission', 'grade')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('assignment', 'student', 'submission', 'grade')
        }),
    )
    ordering = ('assignment',)

class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'instructor', 'created_by', 'created_at', 'updated_at')
    search_fields = ("name", "instructor")
    readonly_fields = ('created_at', 'updated_at')

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
