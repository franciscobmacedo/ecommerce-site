from unittest.mock import ANY, Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from stripe._error import InvalidRequestError, SignatureVerificationError

from ecommerce.forms import OrderForm
from ecommerce.models import LineOrder
from ecommerce.views import create_line_orders

User = get_user_model()


@override_settings(
    STRIPE_SECRET_KEY="test",
    STRIPE_PUBLISHABLE_KEY="test",
)
class BuyProductTestCase(TestCase):
    @patch("ecommerce.views.stripe")
    def test_successful_purchase(self, stripe_mock):
        class SessionMock(Mock):
            url = "http://test.com"

        stripe_mock.checkout.Session.create.return_value = SessionMock()
        response = self.client.post(reverse("purchase"), data={"quantity": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Redirect"], "http://test.com")

    def test_invalid_form(self):
        response = self.client.post(reverse("purchase"), data={})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], OrderForm)
        self.assertFormError(
            form=response.context["form"],
            field="quantity",
            errors=["This field is required."],
        )


@override_settings(
    STRIPE_SECRET_KEY="test",
    STRIPE_PUBLISHABLE_KEY="test",
    STRIPE_WEBHOOK_SECRET="test",
)
class WebhookTestCase(TestCase):
    @patch("ecommerce.views.stripe.Webhook.construct_event")
    @patch("ecommerce.views.create_line_orders")
    def test_webhook_valid_signature(
        self, create_line_orders_mock, construct_event_mock
    ):
        event_mock = construct_event_mock.return_value
        event_mock.type = "checkout.session.completed"
        event_mock.data.object = Mock()
        create_line_orders_mock.return_value = None

        response = self.client.post(
            reverse("webhook"),
            data="payload",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )
        construct_event_mock.assert_called_once_with(
            b"payload", "valid_signature", "test"
        )
        self.assertEqual(response.status_code, 200)

        create_line_orders_mock.assert_called_once_with(event_mock.data.object)

    @patch("ecommerce.views.stripe.Webhook.construct_event")
    def test_webhook_invalid_signature(self, construct_event_mock):
        # raise exception when the signature is invalid
        construct_event_mock.side_effect = SignatureVerificationError(
            "error", "invalid_signature"
        )
        response = self.client.post(
            reverse("webhook"),
            data="payload",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid_signature",
        )
        # Assert that the response status code is 400
        self.assertEqual(response.status_code, 400)


@override_settings(
    STRIPE_SECRET_KEY="test",
    STRIPE_PUBLISHABLE_KEY="test",
)
class BuyProductSuccessTestCase(TestCase):
    def test_purchase_success(self):
        session_id = "test_session_id"
        url = reverse("purchase_success")
        with patch("ecommerce.views.stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_retrieve.return_value = None
            response = self.client.get(url, {"session_id": session_id})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "purchase_success.html")

    def test_purchase_fails(self):
        session_id = "test_session_id"
        url = reverse("purchase_success")
        with patch("ecommerce.views.stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_retrieve.side_effect = InvalidRequestError("Test error", "Test error")
            response = self.client.get(url, {"session_id": session_id})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "There was a problem while buying your product. Please try again.",
        )


@override_settings(
    EMAIL_HOST_USER="from@example.com",
)
class CreateLineOrdersTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="staff_user", email="staff_user@example.com", is_staff=True
        )

    @patch("stripe.checkout.Session.list_line_items")
    @patch("django.core.mail.send_mail")
    def test_create_line_orders(self, mock_send_mail, mock_list_line_items):
        # Mock the necessary objects and methods
        mock_list_line_items.return_value = Mock(
            data=[Mock(quantity=2), Mock(quantity=3)]
        )
        customer_details_mock = Mock()
        customer_details_mock.name = "John Doe"
        customer_details_mock.email = "john.doe@example.com"

        session_mock = Mock(
            id="test_session_id",
            customer_details=customer_details_mock,
            shipping_details="123 Main St\nSpringfield\nIL\n62701",
        )

        # Call the function under test
        create_line_orders(session_mock)

        # Assert that the expected methods were called with the correct arguments
        self.assertEqual(mock_send_mail.call_count, 2)
        self.assertEqual(LineOrder.objects.count(), 2)
        line_order = LineOrder.objects.get(quantity=2)
        self.assertEqual(line_order.name, "John Doe")
        self.assertEqual(line_order.email, "john.doe@example.com")
        self.assertEqual(
            line_order.shipping_details, "123 Main St\nSpringfield\nIL\n62701"
        )
        mock_send_mail.assert_any_call(
            "Your order has been placed",
            ANY,
            "from@example.com",
            ["john.doe@example.com"],
        )
        mock_send_mail.assert_any_call(
            "You have a new order!", ANY, "from@example.com", ["staff_user@example.com"]
        )
