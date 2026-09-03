from django.contrib import admin

from .models import Album, Category, Photo


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ('image', 'caption', 'is_preview', 'watermark_text', 'licensing_info', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'album_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Albums')
    def album_count(self, obj):
        return obj.albums.count()


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'photographer', 'category', 'is_public', 'photo_count', 'created_at')
    list_filter = ('is_public', 'category', 'created_at')
    search_fields = ('title', 'description', 'photographer__username', 'photographer__email')
    autocomplete_fields = ('photographer', 'category')
    list_editable = ('is_public',)
    readonly_fields = ('created_at',)
    inlines = (PhotoInline,)

    @admin.display(description='Photos')
    def photo_count(self, obj):
        return obj.photos.count()


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_name', 'album', 'is_preview', 'uploaded_at')
    list_filter = ('is_preview', 'uploaded_at', 'album__is_public')
    search_fields = ('caption', 'watermark_text', 'licensing_info', 'album__title', 'album__photographer__username')
    autocomplete_fields = ('album',)
    readonly_fields = ('uploaded_at',)

    @admin.display(description='Photo')
    def thumbnail_name(self, obj):
        return obj.caption or obj.image.name.rsplit('/', 1)[-1]