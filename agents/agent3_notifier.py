"""Agent 3: Notifier Agent

Receives NotifyMessage from the Coordinator Agent and sends an SMS via Twilio
when a CRITICAL (ER_DISPATCH) event is triggered.

Start:  python agents/agent3_notifier.py
"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from uagents import Agent, Context, Model

from agents.message_types import NotifyMessage
from db.db import DEMO_PATIENTS

_PATIENT_NAMES = {p["patient_id"]: p["name"] for p in DEMO_PATIENTS}
_last_sms: dict[str, float] = {}
SMS_COOLDOWN_SECONDS = 60


class NotifyRequest(Model):
    patient_id: str
    risk_score: float
    doctor_note: str
    severity_level: str = ""
    action_tier: str = ""
    patient_name: str = ""

class NotifyResponse(Model):
    ok: bool

AGENT_NOTIFIER_SEED_PHRASE = os.getenv("AGENT_NOTIFIER_SEED_PHRASE", "your-notifier-seed-phrase-here")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
_raw_to = os.getenv("TWILIO_TO_NUMBERS", os.getenv("TWILIO_TO_NUMBER", ""))
TWILIO_TO_NUMBERS: list[str] = [n.strip() for n in _raw_to.split(",") if n.strip()]

notifier_agent = Agent(
    name="CareFlow-Notifier",
    seed=AGENT_NOTIFIER_SEED_PHRASE,
    port=8003,
    endpoint=["http://localhost:8003/submit"],
    publish_agent_details=True,
)


WHATSAPP_SANDBOX_NUMBER = "whatsapp:+14155238886"


def _send_whatsapp(patient_id: str, risk_score: float, doctor_note: str, patient_name: str = "") -> bool:
    try:
        from twilio.rest import Client
        name = patient_name or _PATIENT_NAMES.get(patient_id, patient_id)
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        body = (
            f"[CareFlow CRITICAL ALERT]\n"
            f"Patient: {name} ({patient_id})\n"
            f"Risk Score: {round(risk_score * 100)}%\n"
            f"Action: {doctor_note}"
        )
        success = False
        for number in TWILIO_TO_NUMBERS:
            try:
                client.messages.create(
                    body=body,
                    from_=WHATSAPP_SANDBOX_NUMBER,
                    to=f"whatsapp:{number}",
                )
                success = True
            except Exception as exc:
                print(f"[Notifier] WhatsApp send failed for {number}: {exc}")
        return success
    except Exception as exc:
        print(f"[Notifier] WhatsApp send failed: {exc}")
        return False


@notifier_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"[Notifier] Agent address: {notifier_agent.address}")
    ctx.logger.info("[Notifier] Ready to send WhatsApp alerts for CRITICAL events")
    if not TWILIO_ACCOUNT_SID or TWILIO_ACCOUNT_SID == "your_twilio_account_sid_here":
        ctx.logger.warning("[Notifier] Twilio credentials not configured — WhatsApp will be skipped")


@notifier_agent.on_rest_post("/notify", NotifyRequest, NotifyResponse)
async def handle_notify_rest(ctx: Context, req: NotifyRequest) -> NotifyResponse:
    import time
    now = time.time()
    last = _last_sms.get(req.patient_id, 0)
    if now - last < SMS_COOLDOWN_SECONDS:
        remaining = int(SMS_COOLDOWN_SECONDS - (now - last))
        ctx.logger.info(f"[Notifier] SMS cooldown active for {req.patient_id} — {remaining}s remaining")
        return NotifyResponse(ok=False)

    ctx.logger.info(
        f"[Notifier] REST alert for {req.patient_id} "
        f"(score={req.risk_score:.2f}, tier={req.action_tier})"
    )
    if not TWILIO_ACCOUNT_SID or TWILIO_ACCOUNT_SID == "your_twilio_account_sid_here":
        ctx.logger.warning("[Notifier] Twilio not configured — skipping WhatsApp")
        return NotifyResponse(ok=False)
    sent = _send_whatsapp(req.patient_id, req.risk_score, req.doctor_note, req.patient_name)
    if sent:
        _last_sms[req.patient_id] = now
        ctx.logger.info(f"[Notifier] WhatsApp sent to {TWILIO_TO_NUMBERS}")
    return NotifyResponse(ok=sent)


@notifier_agent.on_message(model=NotifyMessage)
async def handle_notify(ctx: Context, sender: str, msg: NotifyMessage):
    ctx.logger.info(
        f"[Notifier] MSG alert for {msg.patient_id} "
        f"(score={msg.risk_score:.2f}, severity={msg.severity_level})"
    )
    if not TWILIO_ACCOUNT_SID or TWILIO_ACCOUNT_SID == "your_twilio_account_sid_here":
        ctx.logger.warning("[Notifier] Twilio not configured — skipping WhatsApp")
        return
    sent = _send_whatsapp(msg.patient_id, msg.risk_score, msg.doctor_note)
    if sent:
        ctx.logger.info(f"[Notifier] WhatsApp sent to {TWILIO_TO_NUMBERS}")


if __name__ == "__main__":
    notifier_agent.run()
