"""
Slack-Notifier fuer CallDoc-SQLHK Sync Ergebnisse.

Sendet Sync-Statistiken an einen Slack-Channel via Bot Token.

Autor: Claude Code
Version: 2.1
Datum: 12.01.2026
"""

import json
import logging
import requests
from typing import Dict, Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Slack Bot Token - wird aus Umgebungsvariable oder Config geladen
import os
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

# Config-Datei
CONFIG_FILE = "slack_config.json"

# Default Channel
DEFAULT_CHANNEL = "#ti-status"

# Lookup-Tabellen fuer SQLHK IDs
STANDORT_NAMEN = {
    1: "Rummelsberg 1",
    2: "Rummelsberg 2",
    3: "Offenbach",
    6: "Braunschweig",
}

UNTERSUCHER_NAMEN = {
    1: "Dr. Sandrock",
    2: "Dr. Papageorgiou",
    3: "Dr. Deubner",
    4: "Dr. Gasplmayr",
    5: "Dr. Klopf",
    6: "Dr. Weichsel",
    7: "Dr. Gawehn",
    8: "Dr. Duckheim",
    9: "Dr. Doschat",
    10: "Dr. Lindemann",
    11: "Dr. Neumann",
    12: "Dr. Koch",
    13: "Dr. Pannu",
    19: "Dr. Schaeffer",
}


class SlackNotifier:
    """
    Sendet Sync-Ergebnisse an Slack via Bot API.
    """

    def __init__(self, bot_token: Optional[str] = None, channel: Optional[str] = None):
        """
        Initialisiert den SlackNotifier.

        Args:
            bot_token: Slack Bot Token (optional, aus Env oder Config)
            channel: Slack Channel (optional, aus Config oder Default)
        """
        self.bot_token = bot_token or SLACK_BOT_TOKEN or self._load_token_from_config()
        self.channel = channel or self._load_channel_from_config() or DEFAULT_CHANNEL
        self.enabled = self._load_enabled_from_config()

    def _load_token_from_config(self) -> str:
        """Laedt Bot Token aus Config-Datei."""
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("bot_token", "")
        except:
            return ""

    def _load_channel_from_config(self) -> Optional[str]:
        """Laedt Channel aus Config-Datei."""
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("channel")
        except:
            return None

    def _load_enabled_from_config(self) -> bool:
        """Laedt Aktivierungsstatus aus Config-Datei."""
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("enabled", True)
        except:
            return True

    def save_config(self, channel: Optional[str] = None, enabled: Optional[bool] = None):
        """Speichert Config in Datei."""
        try:
            config = {}
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
            except:
                pass

            if channel is not None:
                config["channel"] = channel
                self.channel = channel
            if enabled is not None:
                config["enabled"] = enabled
                self.enabled = enabled

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Slack-Config gespeichert: channel={self.channel}, enabled={self.enabled}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Slack-Config: {e}")

    def is_configured(self) -> bool:
        """Prueft ob Slack konfiguriert und aktiviert ist."""
        return bool(self.bot_token) and self.enabled

    def get_channels(self) -> List[Dict]:
        """
        Holt Liste der verfuegbaren Channels.

        Returns:
            Liste von Channel-Dicts mit 'id' und 'name'
        """
        try:
            response = requests.get(
                "https://slack.com/api/conversations.list",
                headers={"Authorization": f"Bearer {self.bot_token}"},
                params={"types": "public_channel,private_channel", "limit": 100},
                timeout=10
            )
            data = response.json()

            if data.get("ok"):
                return [{"id": c["id"], "name": c["name"]} for c in data.get("channels", [])]
            else:
                logger.error(f"Slack API Fehler: {data.get('error')}")
                return []

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Channels: {e}")
            return []

    def _format_patient_detail(self, detail: Dict[str, Any]) -> str:
        """
        Formatiert ein Patient-Detail fuer die Slack-Nachricht.

        Args:
            detail: Dict mit name, dob, m1ziffer, untersucher_id, standort_id

        Returns:
            Formatierter String
        """
        name = detail.get("name", "Unbekannt")
        dob = detail.get("dob", "")
        m1ziffer = detail.get("m1ziffer", "")
        untersucher_id = detail.get("untersucher_id")
        standort_id = detail.get("standort_id")

        # Untersucher und Standort Namen nachschlagen
        untersucher = UNTERSUCHER_NAMEN.get(untersucher_id, f"ID {untersucher_id}") if untersucher_id else ""
        standort = STANDORT_NAMEN.get(standort_id, f"ID {standort_id}") if standort_id else ""

        # Formatieren: [M1Ziffer] Name (*DOB) - Untersucher @ Standort
        parts = []
        if m1ziffer:
            parts.append(f"`{m1ziffer}`")
        parts.append(f"*{name}*")
        if dob:
            parts.append(f"({dob})")
        if untersucher or standort:
            location_parts = []
            if untersucher:
                location_parts.append(untersucher)
            if standort:
                location_parts.append(f"@ {standort}")
            parts.append(f"- {' '.join(location_parts)}")

        return " ".join(parts)

    def send_sync_result(
        self,
        date_str: str,
        inserted: int = 0,
        updated: int = 0,
        deleted: int = 0,
        errors: int = 0,
        patient_details: Optional[Dict[str, List[Any]]] = None
    ) -> bool:
        """
        Sendet Sync-Ergebnis an Slack.

        Args:
            date_str: Sync-Datum
            inserted: Anzahl eingefuegter Untersuchungen
            updated: Anzahl aktualisierter Untersuchungen
            deleted: Anzahl geloeschter Untersuchungen
            errors: Anzahl Fehler
            patient_details: Optional Dict mit Listen von Patienten-Details
                             Format: {"inserted": [...], "updated": [...], "deleted": [...]}
                             Jedes Element: {"name": str, "dob": str, "untersucher_id": int, "standort_id": int}

        Returns:
            True wenn erfolgreich, False sonst
        """
        if not self.is_configured():
            logger.debug("Slack nicht konfiguriert oder deaktiviert")
            return False

        try:
            # Emoji basierend auf Ergebnis
            if errors > 0:
                status_emoji = ":warning:"
                status_text = "mit Fehlern"
            elif inserted > 0 or deleted > 0:
                status_emoji = ":arrows_counterclockwise:"
                status_text = "Aenderungen"
            else:
                status_emoji = ":white_check_mark:"
                status_text = "erfolgreich"

            # Nachricht zusammenstellen
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{status_emoji} CallDoc-SQLHK Sync {status_text}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Datum:*\n{date_str}"},
                        {"type": "mrkdwn", "text": f"*Zeit:*\n{datetime.now().strftime('%H:%M:%S')}"}
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Eingefuegt:*\n{inserted}"},
                        {"type": "mrkdwn", "text": f"*Aktualisiert:*\n{updated}"},
                        {"type": "mrkdwn", "text": f"*Geloescht:*\n{deleted}"},
                        {"type": "mrkdwn", "text": f"*Fehler:*\n{errors}"}
                    ]
                }
            ]

            # Patienten-Details hinzufuegen wenn vorhanden
            if patient_details:
                # Eingefuegte Patienten
                if patient_details.get("inserted"):
                    details_list = patient_details["inserted"][:5]
                    formatted = [self._format_patient_detail(d) if isinstance(d, dict) else str(d) for d in details_list]
                    text = "*Neu eingefuegt:*\n" + "\n".join(formatted)
                    if len(patient_details["inserted"]) > 5:
                        text += f"\n_...und {len(patient_details['inserted']) - 5} weitere_"
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": text}
                    })

                # Aktualisierte Patienten
                if patient_details.get("updated"):
                    details_list = patient_details["updated"][:5]
                    formatted = [self._format_patient_detail(d) if isinstance(d, dict) else str(d) for d in details_list]
                    text = "*Aktualisiert:*\n" + "\n".join(formatted)
                    if len(patient_details["updated"]) > 5:
                        text += f"\n_...und {len(patient_details['updated']) - 5} weitere_"
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": text}
                    })

                # Geloeschte Patienten
                if patient_details.get("deleted"):
                    details_list = patient_details["deleted"][:5]
                    formatted = [self._format_patient_detail(d) if isinstance(d, dict) else str(d) for d in details_list]
                    text = "*Geloescht:*\n" + "\n".join(formatted)
                    if len(patient_details["deleted"]) > 5:
                        text += f"\n_...und {len(patient_details['deleted']) - 5} weitere_"
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": text}
                    })

            blocks.append({"type": "divider"})

            # Nachricht via Bot API senden
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": self.channel,
                    "blocks": blocks,
                    "text": f"CallDoc-SQLHK Sync {status_text} fuer {date_str}"  # Fallback
                },
                timeout=10
            )

            data = response.json()

            if data.get("ok"):
                logger.info(f"Slack-Benachrichtigung gesendet an {self.channel} fuer {date_str}")
                return True
            else:
                logger.error(f"Slack API Fehler: {data.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Fehler beim Senden an Slack: {e}")
            return False

    def send_simple_message(self, message: str) -> bool:
        """
        Sendet eine einfache Textnachricht an Slack.
        """
        if not self.is_configured():
            return False

        try:
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": self.channel,
                    "text": message
                },
                timeout=10
            )
            return response.json().get("ok", False)

        except Exception as e:
            logger.error(f"Slack-Fehler: {e}")
            return False


# Singleton-Instanz
_notifier = None


def get_slack_notifier() -> SlackNotifier:
    """Gibt die Singleton-Instanz des SlackNotifiers zurueck."""
    global _notifier
    if _notifier is None:
        _notifier = SlackNotifier()
    return _notifier


def send_sync_to_slack(
    date_str: str,
    inserted: int = 0,
    updated: int = 0,
    deleted: int = 0,
    errors: int = 0,
    patient_details: Optional[Dict[str, List[Any]]] = None
) -> bool:
    """Convenience-Funktion zum Senden von Sync-Ergebnissen."""
    notifier = get_slack_notifier()
    return notifier.send_sync_result(
        date_str=date_str,
        inserted=inserted,
        updated=updated,
        deleted=deleted,
        errors=errors,
        patient_details=patient_details
    )


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    notifier = SlackNotifier()

    # Channels auflisten
    print("Verfuegbare Channels:")
    for ch in notifier.get_channels():
        print(f"  - #{ch['name']}")

    # Test senden mit neuen Detail-Format inkl. M1Ziffer
    print(f"\nSende Test an {notifier.channel}...")
    success = notifier.send_sync_result(
        date_str="13.01.2026",
        inserted=3,
        updated=2,
        deleted=1,
        errors=0,
        patient_details={
            "inserted": [
                {"name": "Mueller, Hans", "dob": "15.03.1965", "m1ziffer": "1698369", "untersucher_id": 1, "standort_id": 1},
                {"name": "Schmidt, Anna", "dob": "22.07.1978", "m1ziffer": "1712456", "untersucher_id": 2, "standort_id": 3},
                {"name": "Weber, Peter", "dob": "08.11.1952", "m1ziffer": "1653518", "untersucher_id": 1, "standort_id": 2}
            ],
            "updated": [
                {"name": "Meier, Klaus", "dob": "30.01.1970", "m1ziffer": "1711929", "untersucher_id": 12, "standort_id": 1},
                {"name": "Schulz, Maria", "dob": "14.09.1983", "m1ziffer": "1713657", "untersucher_id": 2, "standort_id": 6}
            ],
            "deleted": [
                {"name": "Hofmann, Fritz", "dob": "25.12.1945", "m1ziffer": "1234567", "untersucher_id": 1, "standort_id": 1}
            ]
        }
    )
    print(f"Ergebnis: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
