from firebase_admin import messaging
from api.models import DeviceToken


def send_push_notification(user, title, body, data=None):
    """
    🔥 Production-ready push notification sender

    Features:
    - Supports multiple devices
    - Supports deep-linking (data payload)
    - Handles invalid tokens cleanup
    """

    tokens = list(
        DeviceToken.objects.filter(user=user)
        .values_list("token", flat=True)
    )

    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=tokens,
        data=data or {},  # 🔥 IMPORTANT (for navigation)
    )

    try:
        response = messaging.send_multicast(message)

        print("✅ Push success:", response.success_count)
        print("❌ Push failed:", response.failure_count)

        # 🔥 REMOVE INVALID TOKENS (VERY IMPORTANT)
        if response.failure_count > 0:
            failed_tokens = []

            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(tokens[idx])

            if failed_tokens:
                DeviceToken.objects.filter(token__in=failed_tokens).delete()
                print("🧹 Removed invalid tokens:", len(failed_tokens))

    except Exception as e:
        print("🚨 Push error:", str(e))