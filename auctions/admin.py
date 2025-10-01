from django.contrib import admin

from .models import Category, AuctionListing, Comment, User, Bid

class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username")

class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "date", "category", "starting_bid", "status", "owner", "winner")

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "bid", "auction_listing", "bidder")

class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "comment", "auction_listing")


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(AuctionListing, AuctionListingAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)