import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from ecommerce.forms import OrderForm
from ecommerce.models import LineOrder

User = get_user_model()


def home(request):
    form = OrderForm()
    return render(request, "home.html", {"form": form})


@require_POST
def purchase(request):
    form = OrderForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        stripe.api_key = settings.STRIPE_SECRET_KEY
        success_url = (
            request.build_absolute_uri(reverse("purchase_success"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = request.build_absolute_uri(reverse("home"))

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_ID,
                    "quantity": quantity,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return HttpResponseClientRedirect(checkout_session.url)
    return render(request, "product.html", {"form": form})


def purchase_success(request):
    session_id = request.GET.get("session_id")
    if session_id is None:
        return redirect("home")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        messages.error(
            request, "There was a problem while buying your product. Please try again."
        )
        return redirect("home")

    return render(request, "purchase_success.html")


@csrf_exempt
def webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    sig_header = request.headers.get("stripe-signature")
    payload = request.body
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event.type == "checkout.session.completed":
        create_line_orders(event.data.object)
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def create_line_orders(session: stripe.checkout.Session):
    line_items = stripe.checkout.Session.list_line_items(session.id)
    for line_item in line_items.data:
        order = LineOrder.objects.create(
            name=session.customer_details.name,
            email=session.customer_details.email,
            shipping_details=session.shipping_details,
            quantity=line_item.quantity,
        )
    mail.send_mail(
        "Your order has been placed",
        f"""
        Hi {session.customer_details.name}, 
        Your order has been placed. Thank you for shopping with us!
        You will receive an email with tracking information shortly.
    
        Best,
        The one product e-commerce Team
        """,
        "from@example.com",
        [session.customer_details.email],
    )
    staff_users = User.objects.filter(is_staff=True)
    mail.send_mail(
        "You have a new order!",
        """
            Hi team! 
            You have a new order in your shop! go to the admin page to see it.
            
            Best,
            The one product e-commerce Team
            """,
        "from@example.com",
        [user.email for user in staff_users],
    )
