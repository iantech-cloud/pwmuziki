from django.contrib import admin

from .models import Rating, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'client', 'photographer', 'rating', 'title', 'has_response', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('title', 'body', 'photographer_response', 'client__username', 'photographer__username', 'booking__event_type')
    autocomplete_fields = ('booking', 'client', 'photographer')
    readonly_fields = ('created_at',)

    @admin.display(boolean=True, description='Response')
    def has_response(self, obj):
        return bool(obj.photographer_response)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('value',)
    list_filter = ('value',)