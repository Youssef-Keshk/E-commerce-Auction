from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    watchlist = models.ManyToManyField("AuctionListing", blank=True, related_name="watchers")

class Category(models.Model):
    name = models.CharField(max_length=32, verbose_name="Category Name")
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class AuctionListing(models.Model):
    title = models.CharField(max_length=64, verbose_name="Title")
    description = models.CharField(max_length=128, blank=True, verbose_name="Description")
    date = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        Category, 
        blank=True, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="listings", 
        verbose_name="Category"
    )
    image = models.URLField(
        blank=True,
        null=True,
        verbose_name="Image URL",
    )
    starting_bid = models.FloatField(
        validators=[MinValueValidator(0.01)], 
        verbose_name="Starting Bid"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        on_delete=models.CASCADE,
        related_name="listings",
        verbose_name="Owner"
    )

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]
    status = models.CharField(
        max_length=6,
        choices=STATUS_CHOICES,
        default="OPEN",
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="won_listing",
    )

    def highest_bid(self):
        return self.bids.order_by("-bid").first() 

    class Meta:
        verbose_name = "Auction Listing"
        verbose_name_plural = "Auction Listings"

    def __str__(self):
        return f"{self.id}. {self.title}"

class Bid(models.Model):
    bid = models.FloatField(
        validators=[MinValueValidator(0.01)],
        verbose_name="Bid"
    )
    auction_listing = models.ForeignKey(
        AuctionListing,
        blank=False,
        on_delete=models.CASCADE,
        related_name="bids",
        verbose_name="Auction Listing",
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        on_delete=models.CASCADE,
        related_name="bids",
        verbose_name="Bidder",
    )

    def __str__(self):
        return f"{self.id}. {self.bid}$ for {self.auction_listing.title}"

    def clean(self):
        super().clean() 

        highest = self.auction_listing.highest_bid()
        if highest is not None and self.bid <= highest.bid:
            raise ValidationError({
                "bid": f"The bid must be greater than the current highest bid ({highest.bid})"
            })
        
        if self.bid < self.auction_listing.starting_bid:
            raise ValidationError({
                "bid": f"The bid must be at least the starting bid ({self.auction_listing.starting_bid})"
            })


class Comment(models.Model):
    comment = models.CharField(max_length=128, verbose_name="Comment")
    auction_listing = models.ForeignKey(
        AuctionListing,
        blank=False,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Auction Listing",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Author",
    )

    def __str__(self):
        return f"{self.id}. Comment on {self.auction_listing.title}: {self.comment}"
