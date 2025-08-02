import requests, logging
from config.settings import get_settings

logger = logging.getLogger(__name__)

class DiscordNotifier:
    def __init__(self):
        settings = get_settings()
        self.webhook = settings.discord_webhook_url

    def send(self, message: str):
        if not self.webhook:
            logger.warning("No Discord webhook set")
        payload = {"content": message}
        try:
            resp = requests.post(self.webhook, json=payload, timeout=10)
            if resp.status_code == 204:
                logger.info("🔔 Discord notification sent")
            else:
                logger.error(f"Failed Discord webhook ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")

    def notify_shifts(self, shifts):
        if not shifts:
            return
        msg = "**🔎 Shifts Found:**\n" + "\n".join(
            f"• [{s.job_id}] {s.title} @ {s.location} ({s.schedule})" for s in shifts
        )
        self.send(msg)

    def notify_booking(self, shift):
        self.send(f"✅ **Booked**: [{shift.job_id}] {shift.title} @ {shift.location}")
