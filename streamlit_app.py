import streamlit as st
from datetime import date
from jinja2 import Template
import base64
import tempfile
import requests
import smtplib
from email.message import EmailMessage

# --- Load Secrets ---
EMAIL_USER = st.secrets["EMAIL_USER"]
EMAIL_PASS = st.secrets["EMAIL_PASS"]
PDFSHIFT_API_KEY = st.secrets["PDFSHIFT_API_KEY"]

# --- Page Config ---
st.set_page_config(page_title="Creator Invoice Generator", page_icon="💼")
st.title("💼 Invoice Generator for Coaches & Creators")
st.markdown("Generate and email a beautiful, client-ready invoice in seconds.")

# --- FORM ---
with st.form("invoice_form"):
    st.markdown("### 🧾 Your Info")
    your_name = st.text_input("Your Name or Brand", "Fabrizio Fonseca")

    st.markdown("### 👤 Client Info")
    client_name = st.text_input("Client’s Name or Business")
    send_to = st.text_input("Client’s Email Address")

    st.markdown("### 📌 Service Details")
    project_title = st.text_input("What is this invoice for?", placeholder="e.g. Instagram Content for June")
    service_type = st.selectbox("Type of Service", [
        "1:1 Coaching", "Strategy Session", "Instagram Reels",
        "TikTok Batch", "Content Planning", "Consulting Call", "Other"
    ])
    session_date = st.date_input("Service or Delivery Date", value=date.today())

    st.markdown("### 💰 Payment Info")
    amount = st.number_input("Total Amount (USD)", min_value=0.0, format="%.2f")
    payment_method = st.selectbox("Preferred Payment Method", ["PayPal", "Stripe", "Bank Transfer"])
    notes = st.text_area("Notes (optional)", placeholder="e.g. Payment due within 7 days. Thanks again!")

    submitted = st.form_submit_button("📤 Generate Invoice & Send")


# --- PDF + EMAIL ---
if submitted:
    with open("invoice_template.html", "r") as f:
        template = Template(f.read())

    html_out = template.render(
        your_name=your_name,
        client_name=client_name,
        project_title=project_title,
        service_type=service_type,
        session_date=session_date.strftime("%B %d, %Y"),
        amount=amount,
        payment_method=payment_method,
        notes=notes,
        invoice_id=f"{date.today().strftime('%Y%m%d')}-{client_name[:3].upper()}"
    )

    def html_to_pdf_via_pdfshift(html):
        response = requests.post(
            "https://api.pdfshift.io/v3/convert/pdf",
            headers={"X-API-Key": PDFSHIFT_API_KEY},
            json={"source": html}
        )
        if not response.ok:
            raise Exception(f"PDFShift failed: {response.text}")
        return response.content

    try:
        pdf_bytes = html_to_pdf_via_pdfshift(html_out)
    except Exception as e:
        st.error(f"❌ Failed to generate PDF:\n\n{e}")
        st.stop()

    # Save to temp for download
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(pdf_bytes)
        tmp_pdf.seek(0)
        b64 = base64.b64encode(tmp_pdf.read()).decode()

    # Send email
    msg = EmailMessage()
    msg["Subject"] = f"Invoice for {project_title}"
    msg["From"] = EMAIL_USER
    msg["To"] = send_to
    msg.set_content(f"""Hi {client_name},

Please find attached your invoice for the project: {project_title}.

Thanks,
{your_name}
""")
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="invoice.pdf")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        st.success(f"✅ Invoice sent to {send_to}")
    except Exception as e:
        st.error(f"❌ Failed to send email:\n\n{e}")

    st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="invoice.pdf">📄 Download Your Invoice</a>', unsafe_allow_html=True)
