from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from django import forms

from .models import User, AuctionListing, Bid, Comment, Category


class AuctionListingForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        fields = ['title', 'description', 'image', 'category', 'starting_bid']

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid']
        widgets = {
            'bid': forms.NumberInput(attrs={'step': 1.0, 'placeholder': 'Bid'})
        }
        labels = {'bid': ''}

    def __init__(self, *args, **kwargs):
        min_bid = kwargs.pop('min_bid', None)  
        super().__init__(*args, **kwargs)
        if min_bid is not None:
            self.fields['bid'].widget.attrs['min'] = min_bid + 1 # min_bit (exclusive) + step -> min_bit (inclusive)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']
        widgets = {
            'comment': forms.TextInput(attrs={'placeholder': 'Write a comment...'})
        }
        labels = {'comment': ''}


def index(request):
    return render(request, "auctions/index.html", {
        "listings": AuctionListing.objects.filter(),
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AuctionListingForm(request.POST)
        if form.is_valid():
            listing : AuctionListing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            return HttpResponseRedirect(reverse("auctions:listing", args=(listing.id,)))

    return render(request, "auctions/create.html", {
        "form": AuctionListingForm(),
    })


def listing(request: HttpRequest, listing_id) -> HttpResponse:
    try:
        listing = AuctionListing.objects.get(pk=listing_id) 
    except AuctionListing.DoesNotExist:
        raise Http404("Listing not found!")
    
    authenticated = request.user.is_authenticated

    on_watchlist = False
    if authenticated:
        on_watchlist = request.user.watchlist.filter(pk=listing.id).exists()

    highest = listing.highest_bid()
    min_bid = highest.bid if highest else listing.starting_bid
    
    if request.method == "POST" and not authenticated:
        messages.error(request, "You must log in first to submit this form.")
        return HttpResponseRedirect(reverse("auctions:listing", args=(listing_id,)))
    
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "bid_form":
            form = BidForm(request.POST, instance=Bid(auction_listing=listing, bidder=request.user))
            if form.is_valid():
                form.save(commit=True)
                messages.success(request, "Your bid was placed.")
                return HttpResponseRedirect(reverse("auctions:listing", args=(listing_id,)))
            
        elif form_type == "comment_form":
            form = CommentForm(request.POST, instance=Comment(auction_listing=listing, author=request.user))
            if form.is_valid():
                form.save(commit=True)
                messages.success(request, "Your comment was added.")
                return HttpResponseRedirect(reverse("auctions:listing", args=(listing_id,)))

        elif form_type == "watchlist_form":
            if on_watchlist:
                request.user.watchlist.remove(listing)
                messages.success(request, "Removed from your watchlist.")
            else:
                request.user.watchlist.add(listing)
                messages.success(request, "Added to your watchlist.")
            return HttpResponseRedirect(reverse("auctions:listing", args=(listing_id,)))
        
        elif form_type == "close_bid_form":
            if listing.owner == request.user:
                listing.status = "CLOSED"
                if highest is not None:
                    listing.winner = highest.bidder
                    messages.success(request, "Bid closed and a winner has been declared.")
                else:
                    messages.success(request, "Bid closed and no winner.")
                listing.save()
            else:
                messages.error(request, "User has no right to close this bid.")

        messages.error(request, "Invalid form submission.")    

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid_form": BidForm(min_bid=min_bid),
        "comment_form": CommentForm(),
        "authenticated": authenticated,
        "on_watchlist": on_watchlist,
    })


def choose_categories(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all()
    })

def category(request: HttpRequest, category_id=None) -> HttpResponse:
    categories = Category.objects.all()
    if category_id is None:
        listings = AuctionListing.objects.all()
        selected_category = None
    else:
        try:
            selected_category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            raise Http404("Listing not found!")

        listings = AuctionListing.objects.filter(category=selected_category)

    return render(request, "auctions/categories.html", {
        "categories": categories,
        "listings": listings,
        "selected_category": selected_category,
    })


def watchlist(request: HttpRequest) -> HttpResponse:
    return render(request, "auctions/watchlist.html", {
        "listings": request.user.watchlist.all(),
    })