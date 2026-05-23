from django.contrib import admin
from .models import Assignment, Course, AssignmentProof, StudentProofMapping, CourseInvitation
import csv
from django.http import HttpResponse

# --- Custom Global Admin Actions ---

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
                if value is None:
                    row.append('')
                else:
                    row.append(str(value))
            except Exception:
                row.append('')
        writer.writerow(row)
    
    return response

export_to_csv.short_description = "Export selected to CSV"

# --- Inline Models ---

class AssignmentProofInline(admin.TabularInline):
    model = AssignmentProof
    extra = 1

# --- Model Admins ---

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date', 'course_instructor', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'course__name')
    list_filter = ('course', 'due_date')
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_to_csv]
    inlines = [AssignmentProofInline]

    fieldsets = (
        (None, {"fields": ("title", "description", "due_date", "course", "created_by")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("title", "description", "due_date", "course", "created_by")}),
    )
    ordering = ('title',)

    def course_instructor(self, obj):
        return obj.course.instructor if obj.course else None
    course_instructor.short_description = "Instructor"
    course_instructor.admin_order_field = "course__instructor"


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'term', 'instructor', 'is_active', 'created_by', 'created_at')
    search_fields = ("name", "instructor__username", "instructor__email")
    list_filter = ('is_active', 'term') 
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('students',)
    actions = [export_to_csv]
    
    fieldsets = (
        (None, {"fields": ("name", "term", "is_active", "instructor", "students", "join_code_hash", "join_code_expires_at", "created_by")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("name", "term", "is_active", "instructor", "students", "join_code_hash", "join_code_expires_at", "created_by")}),
    )
    ordering = ('name',)


class StudentProofMappingAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'template_proof_id', 'get_started_at', 'completed_at', 'is_late_submission')
    search_fields = ('student__username', 'student__email', 'assignment__title')
    list_filter = ('assignment', 'completed_at')
    readonly_fields = ('get_started_at',)
    actions = [export_to_csv]

    fieldsets = (
        (None, {"fields": ("student", "assignment", "template_proof_id", "content_type", "object_id", "get_started_at", "completed_at")}),
    )

    def get_started_at(self, obj):
        """ Pulls created_at from generic relation """
        if obj.student_proof and hasattr(obj.student_proof, 'created_at'):
            return obj.student_proof.created_at
        return "-"
    get_started_at.short_description = "Started At"

    def is_late_submission(self, obj):
        return obj.is_late
    is_late_submission.boolean = True
    is_late_submission.short_description = "Late?"


class CourseInvitationAdmin(admin.ModelAdmin):
    """ ADDED: Managing user course invitation logs directly """
    list_display = ('course', 'student', 'status', 'sent_at', 'updated_at')
    search_fields = ('course__name', 'student__username', 'student__email')
    list_filter = ('status', 'course')
    readonly_fields = ('sent_at', 'updated_at')
    actions = [export_to_csv]

    fieldsets = (
        (None, {"fields": ("course", "student", "status")}),
    )
    ordering = ('-sent_at',)


# --- Registration ---

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(StudentProofMapping, StudentProofMappingAdmin)
admin.site.register(CourseInvitation, CourseInvitationAdmin) # Registered new mapping