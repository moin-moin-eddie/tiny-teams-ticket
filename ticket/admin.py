from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from mptt.admin import MPTTModelAdmin

from .models import Attachment, Comment, Ticket, ProblemSource, TicketEvent, Analytics


class TicketCommentInline(admin.TabularInline):
    model = Comment


class TicketAttachmentInline(admin.TabularInline):
    model = Attachment


class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "created_by", "assigned_to", "problem_source", "completed", "priority", "created_date"
    )
    list_filter = ("completed",)
    ordering = ("priority",)
    search_fields = ("title",)
    inlines = [TicketCommentInline, TicketAttachmentInline]
    filter_horizontal = ['followers']


class TicketEventAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "timestamp", "ticket", "user_to_notify", "seen")
    # ordering = ("timestamp",)


class SubProblemInline(admin.TabularInline):
    model = ProblemSource


class ProblemSourceAdmin(MPTTModelAdmin):
    mptt_indent_field = "name"
    ordering = ("id", "name")
    list_display = ["id", "name", "breadcrumb", "view_sub_problems"]
    list_filter = ["name", "parent"]
    search_fields = ["name"]
    inlines = [SubProblemInline]

    def get_sub_problems(self, obj):
        return obj.get_children()

    def view_sub_problems(self, obj):
        count = self.get_sub_problems(obj).count()
        url = (
                reverse("admin:ticket_problemsource_changelist")
                + "?"
                + urlencode({"parent_id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} Subproblems</a>', url, count)

    get_sub_problems.admin_order_field = 'name'


class ReplyInline(admin.TabularInline):
    model = Comment


class CommentAdmin(MPTTModelAdmin):
    mptt_indent_field = "author"
    ordering = ["created_date"]
    list_display = ["id", "author", "ticket", "created_date"]
    list_filter = ["parent"]
    search_fields = ["text"]
    inlines = [ReplyInline]


admin.site.register(ProblemSource, ProblemSourceAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Attachment)
admin.site.register(TicketEvent, TicketEventAdmin)
admin.site.register(Analytics)

admin.site.site_header = 'Ticket Verwaltung'
