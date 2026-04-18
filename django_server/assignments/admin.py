from django.contrib import admin
from .models import Assignment, Course, AssignmentProof
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

class AssignmentProofInline(admin.TabularInline):
    model = AssignmentProof
    extra = 1

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'due_date', 'course_instructor', 'created_at', 'updated_at', 'created_by')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_to_csv]
    inlines = [AssignmentProofInline]

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
                    "course",
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
                    "course",
                    "created_by",
                ),
            },
        ),
    )
    ordering = ('title',)

    def course_instructor(self, obj):
        return obj.course.instructor if obj.course else None
    course_instructor.short_description = "Instructor"
    course_instructor.admin_order_field = "course__instructor"

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'instructor', 'is_active', 'created_by', 'created_at', 'updated_at')
    search_fields = ("name", "instructor")
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_to_csv]

    filter_horizontal = ()
    list_filter = ('is_active',) 
    
    fieldsets = (
        (None, {"fields": ("name", "is_active", "instructor", "students", "join_code_hash", "join_code_expires_at", "created_by")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("name", "is_active", "instructor", "students", "join_code_hash", "join_code_expires_at", "created_by"),
            },
        ),
    )
    ordering = ('name',)

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Course, CourseAdmin)
