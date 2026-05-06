"""
Email notifications via SendGrid.
All email sending is non-blocking — a failure never breaks the order flow.
"""
import logging
from typing import List
from core.config import settings

logger = logging.getLogger(__name__)


def _send(to_emails: List[str], subject: str, html_body: str) -> bool:
    if not settings.SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set — email skipped.")
        return False
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, To
        msg = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=[To(e) for e in to_emails],
            subject=subject,
            html_content=html_body,
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(msg)
        logger.info(f"Email sent to {to_emails} — status {response.status_code}")
        return True
    except Exception as exc:
        logger.error(f"SendGrid error: {exc}")
        return False


def _base_template(content: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/>
    <style>
      body{{font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:0}}
      .wrapper{{max-width:600px;margin:30px auto;background:#fff;border-radius:6px;overflow:hidden}}
      .header{{background:#0d1f3c;padding:24px 30px;text-align:center}}
      .header h1{{color:#f5c400;font-size:22px;margin:0}}
      .header p{{color:#c8d0df;font-size:13px;margin:6px 0 0}}
      .body{{padding:28px 30px;color:#333;line-height:1.7}}
      .body h2{{color:#0d1f3c;font-size:18px;margin-top:0}}
      table.items{{width:100%;border-collapse:collapse;margin:16px 0}}
      table.items th{{background:#0d1f3c;color:#f5c400;padding:10px 12px;text-align:left;font-size:13px}}
      table.items td{{padding:9px 12px;border-bottom:1px solid #eee;font-size:13px}}
      .total-row td{{font-weight:bold;color:#0d1f3c;background:#fffbe6}}
      .badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:bold}}
      .badge-pending{{background:#fff3cd;color:#856404}}
      .badge-confirmed{{background:#d1e7dd;color:#0f5132}}
      .badge-shipped{{background:#cfe2ff;color:#084298}}
      .badge-delivered{{background:#d1e7dd;color:#0f5132}}
      .badge-cancelled{{background:#f8d7da;color:#842029}}
      .btn{{display:inline-block;padding:11px 24px;background:#f5c400;color:#0d1f3c;
            text-decoration:none;font-weight:bold;border-radius:4px;margin-top:16px}}
      .footer{{background:#0d1f3c;padding:16px 30px;text-align:center;color:#6c8ebf;font-size:12px}}
    </style></head><body>
    <div class="wrapper">
      <div class="header"><h1>Enactus New Beni Suef</h1><p>ChitoShell — Chitin &amp; Chitosan Products</p></div>
      <div class="body">{content}</div>
      <div class="footer">© 2026 Enactus New Beni Suef · Beni Suef, Egypt</div>
    </div></body></html>"""


def _items_table(items) -> str:
    rows = ""
    total = 0
    for i in items:
        try:
            pname = i.variant.product.name
            plabel = i.variant.label
        except Exception:
            pname, plabel = "Product", ""
        sub = i.unit_price * i.quantity
        total += sub
        rows += f"<tr><td>{pname}</td><td>{plabel}</td><td>{i.quantity}</td><td>EGP {i.unit_price:,.0f}</td><td>EGP {sub:,.0f}</td></tr>"
    return f"""<table class="items">
      <thead><tr><th>Product</th><th>Size</th><th>Qty</th><th>Unit Price</th><th>Subtotal</th></tr></thead>
      <tbody>{rows}</tbody>
      <tfoot><tr class="total-row"><td colspan="4">Total</td><td>EGP {total:,.0f}</td></tr></tfoot>
    </table>"""


def notify_admin_new_order(order) -> None:
    items_html = _items_table(order.items)
    content = f"""
    <h2>New Order Received — #{order.id}</h2>
    <p>A new order has just been placed on the ChitoShell website.</p>
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr><td style="padding:6px 0;color:#666;width:140px;">Customer</td><td><strong>{order.customer_name}</strong></td></tr>
      <tr><td style="padding:6px 0;color:#666;">Email</td><td><a href="mailto:{order.customer_email}">{order.customer_email}</a></td></tr>
      <tr><td style="padding:6px 0;color:#666;">Phone</td><td>{order.customer_phone or "—"}</td></tr>
      <tr><td style="padding:6px 0;color:#666;">Address</td><td>{order.address or "—"}</td></tr>
      <tr><td style="padding:6px 0;color:#666;">Notes</td><td>{order.notes or "—"}</td></tr>
      <tr><td style="padding:6px 0;color:#666;">Status</td><td><span class="badge badge-pending">PENDING</span></td></tr>
    </table>
    <h3>Items Ordered</h3>{items_html}
    <a href="http://localhost:8000/admin" class="btn">Open Admin Dashboard</a>"""
    _send([settings.ADMIN_NOTIFY_EMAIL], f"[ChitoShell] New Order #{order.id} — {order.customer_name}", _base_template(content))


def notify_customer_order_received(order) -> None:
    items_html = _items_table(order.items)
    content = f"""
    <h2>Thank you, {order.customer_name}!</h2>
    <p>We have received your order and will contact you shortly to confirm delivery details.</p>
    <p><strong>Order #{order.id}</strong></p>{items_html}
    <p style="color:#666;font-size:13px;">Questions? Reply to this email and we will get back to you.</p>"""
    _send([order.customer_email], f"Order Received — #{order.id} | Enactus New Beni Suef", _base_template(content))


def notify_customer_status_update(order) -> None:
    messages = {
        "confirmed": ("Order Confirmed!", "Great news — your order has been confirmed and is being prepared."),
        "shipped":   ("Order Shipped!", "Your order is on its way to you."),
        "delivered": ("Order Delivered!", "Your order has been delivered. We hope you love it!"),
        "cancelled": ("Order Cancelled", "Your order has been cancelled. Contact us if you have questions."),
    }
    status = str(order.status.value if hasattr(order.status, "value") else order.status)
    title, message = messages.get(status, ("Order Update", "Your order status has been updated."))
    items_html = _items_table(order.items)
    content = f"""
    <h2>{title}</h2>
    <p>Hi {order.customer_name}, {message}</p>
    <p><strong>Order #{order.id}</strong> &nbsp; <span class="badge badge-{status}">{status.upper()}</span></p>
    {items_html}"""
    _send([order.customer_email], f"[ChitoShell] {title} — Order #{order.id}", _base_template(content))
