import streamlit as st
from datetime import date
from jinja2 import Template
from weasyprint import HTML
import base64
import tempfile
import smtplib
from email.message import EmailMessage
import traceback


st.set_page_config(page_title="Invoice Generator", page_icon="💸")

st.title("💸 Invoice Generator for Creators")
st.write("Generate a clean, professional invoice and download it as a PDF instantly.")

# --- FORM INPUTS ---
with st.form("invoice_form"):
    st.subheader("📝 Fill in your invoice details")
    creator_name = st.text_input("Your Name or Brand", "Fabrizio Fonseca")
    client_name = st.text_input("Client or Brand Name")
    project_name = st.text_input("Project Name (e.g. February Instagram Content)")
    deliverables = st.text_area("Deliverables (e.g. 5 Reels, 3 Carousels)", height=100)
    total_amount = st.number_input("Total Amount (USD)", min_value=0.0, format="%.2f")
    payment_method = st.selectbox("Preferred Payment Method", ["PayPal", "Stripe", "Bank Transfer"])
    invoice_date = st.date_input("Invoice Date", value=date.today())
    due_date = st.date_input("Payment Due Date")
    notes = st.text_area("Notes (Optional)", placeholder="e.g. Payment due within 7 days")
    email_to_receive = st.text_input("Email that will receive the invoice")

    submit = st.form_submit_button("Generate Invoice")


# --- GENERATE PDF ---
if submit:
    # Load and render template
    with open("invoice_template.html", "r") as f:
        template = Template(f.read())

    html_out = template.render(
        creator_name=creator_name,
        client_name=client_name,
        project_name=project_name,
        deliverables=deliverables,
        total_amount=total_amount,
        payment_method=payment_method,
        invoice_date=invoice_date.strftime("%B %d, %Y"),
        due_date=due_date.strftime("%B %d, %Y"),
        notes=notes,
        invoice_id=f"{date.today().strftime('%Y%m%d')}-{client_name[:3].upper()}"
    )

    # ✅ Create temp file and generate PDF FIRST
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        HTML(string=html_out).write_pdf(tmp_pdf.name)
        tmp_pdf.seek(0)
        b64 = base64.b64encode(tmp_pdf.read()).decode()

    # ✅ THEN prepare the email and attach PDF
    sender_email = "fabriziofonsari@gmail.com"
    sender_password = "gfds myqn aumo vusl"  # App password

    msg = EmailMessage()
    msg['Subject'] = f"Invoice for {project_name}"
    msg['From'] = sender_email
    msg['To'] = email_to_receive
    msg.set_content(f"Hi {client_name},\n\nPlease find attached your invoice for the project: {project_name}.\n\nThanks,\n{creator_name}")
    msg.add_attachment(base64.b64decode(b64), maintype='application', subtype='pdf', filename="invoice.pdf")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        st.success(f"✅ Invoice sent to {email_to_receive}")
    except Exception as e:
        st.error("❌ Failed to send email:")
        st.text(traceback.format_exc())

    # ✅ Finally, offer download
    href = f'<a href="data:application/pdf;base64,{b64}" download="invoice.pdf">📄 Download Your Invoice</a>'
    st.markdown(href, unsafe_allow_html=True)
