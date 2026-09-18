import os
from datetime import datetime

import requests

TEAMS_WEBHOOK_URL = (
    "
)


def send_teams_message(title, text, success=True, plain_text=None):
    webhook = os.environ.get("TEAMS_WEBHOOK_URL", TEAMS_WEBHOOK_URL).strip()
    if not webhook:
        print("⚠️ TEAMS_WEBHOOK_URL не задан — уведомление в Teams пропущено")
        return False

    # Формат для Power Automate: триггер «Когда получен HTTP-запрос» + поле text
    icon = "✅" if success else "❌"
    payload = {
        "text": plain_text if plain_text is not None else (
            f"{icon} {title}\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{text}"
        )
    }

    response = requests.post(webhook, json=payload, timeout=30)
    if response.status_code not in (200, 202):
        print(f"⚠️ Teams webhook ошибка: {response.status_code} {response.text}")
        return False

    print(f"✅ Уведомление отправлено в Teams: {title}")
    return True


def notify_lead_success(lead_id, status="165"):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return send_teams_message(
        title="Заявка создана успешно",
        text="",
        success=True,
        plain_text=f"Заявка создана успешно\n{created_at}",
    )


def notify_lead_failure(lead_id=None, reason="Заявка не создана"):
    lead_part = f"leadId: {lead_id}\n" if lead_id else ""
    return send_teams_message(
        title="Заявка не создана",
        text=f"{lead_part}Причина: {reason}\nАвтотест lead_create завершился с ошибкой.",
        success=False,
    )
