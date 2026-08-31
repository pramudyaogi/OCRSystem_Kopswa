import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from app.config import UPLOAD_DIR

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Ambil konfigurasi SMTP dari environment
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_PENGIRIM = os.getenv("EMAIL_PENGIRIM", "guinnessyogi2@gmail.com")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "ahtxhqjgojmpqxme")

FIELD_LABELS = {
    "nik": "NIK",
    "nama": "NAMA",
    "tempat_tgl_lahir": "TEMPAT / TGL LAHIR",
    "alamat_lengkap": "ALAMAT LENGKAP",
    "jenis_kelamin": "JENIS KELAMIN",
    "agama": "AGAMA",
    "status_perkawinan": "STATUS PERKAWINAN",
    "pekerjaan": "PEKERJAAN"
}

def generate_document_pdf(doc, pdf_output_path):
    """
    Membuat file PDF laporan verifikasi KTP dengan ReportLab, 
    berisi header resmi, tabel 8 data terstruktur, dan foto fisik KTP.
    """
    doc_pdf = SimpleDocTemplate(
        pdf_output_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Style Kustom
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        alignment=1, # Center
        fontName="Helvetica-Bold",
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        fontName="Helvetica",
        spaceAfter=15
    )

    cell_label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#334155"),
        fontName="Helvetica-Bold"
    )

    cell_val_style = ParagraphStyle(
        'CellVal',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica"
    )

    # 1. Header PDF
    story.append(Paragraph("LAPORAN HASIL VERIFIKASI DOKUMEN KTP", title_style))
    created_str = doc.created_at.strftime("%d %B %Y, %H:%W WIB") if doc.created_at else datetime.now().strftime("%d %B %Y, %H:%W WIB")
    story.append(Paragraph(f"Sistem OCR Koperasi | ID Dokumen: #{doc.id} | Dibuat: {created_str}", subtitle_style))
    story.append(Spacer(1, 8))

    # 2. Tabel Data Terstruktur
    extracted = doc.extracted_data or {}
    table_data = [
        [Paragraph("FIELD DATA", cell_label_style), Paragraph("HASIL EKSTRAKSI OCR", cell_label_style)]
    ]

    for key, label in FIELD_LABELS.items():
        val = "-"
        if key in extracted:
            item = extracted[key]
            val = item.get("value", "") if isinstance(item, dict) else str(item)
        table_data.append([
            Paragraph(label, cell_label_style),
            Paragraph(val or "-", cell_val_style)
        ])

    table = Table(table_data, colWidths=[170, 340])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))

    story.append(table)
    story.append(Spacer(1, 16))

    # 3. Foto KTP Tersemat
    fn = (doc.filename or "").replace("uploads/", "").replace("uploads\\", "")
    img_path = os.path.join(UPLOAD_DIR, fn)
    temp_downloaded_img = None
    
    # If local file does not exist but fn is a URL, download temporarily
    if not os.path.exists(img_path) and (fn.startswith("http://") or fn.startswith("https://")):
        try:
            import urllib.request
            import tempfile
            ext = os.path.splitext(fn)[1] or ".jpg"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_file.close()
            urllib.request.urlretrieve(fn, temp_file.name)
            img_path = temp_file.name
            temp_downloaded_img = temp_file.name
        except Exception as dl_err:
            print(f"Warning: Failed downloading remote image for PDF: {dl_err}")

    if os.path.exists(img_path):
        try:
            story.append(Paragraph("LAMPIRAN FOTO FISIK KTP:", cell_label_style))
            story.append(Spacer(1, 6))
            
            # Enlarge image while preserving aspect ratio
            target_width = 6.8 * inch
            target_height = 4.2 * inch
            try:
                from PIL import Image as PILImage
                with PILImage.open(img_path) as pil_img:
                    orig_w, orig_h = pil_img.size
                    if orig_w > 0:
                        aspect = orig_h / float(orig_w)
                        target_height = target_width * aspect
                        if target_height > 4.5 * inch:
                            target_height = 4.5 * inch
                            target_width = target_height / aspect
            except Exception as pil_err:
                print(f"PIL aspect ratio calc note: {pil_err}")

            rl_img = RLImage(img_path, width=target_width, height=target_height)
            rl_img.hAlign = 'CENTER'
            story.append(rl_img)
        except Exception as e:
            print(f"Warning inserting image into PDF: {e}")

    # Build PDF
    doc_pdf.build(story)

    # Cleanup temp downloaded image if created
    if temp_downloaded_img and os.path.exists(temp_downloaded_img):
        try:
            os.remove(temp_downloaded_img)
        except Exception:
            pass

    return pdf_output_path


def send_documents_via_email(target_email: str, doc_records: list):
    """
    Mengirimkan email berisi data dokumen KTP (termasuk Lampiran PDF + Lampiran Foto KTP)
    ke alamat email tujuan menggunakan SMTP Gmail.
    """
    if not doc_records:
        return False, "Tidak ada dokumen yang dipilih."

    # Sanitasi password app dari spasi
    app_pwd = EMAIL_APP_PASSWORD.replace(" ", "")
    temp_files_to_cleanup = []

    try:
        # Menyiapkan Pesan Email (MIMEMultipart)
        msg = MIMEMultipart()
        msg['From'] = EMAIL_PENGIRIM
        msg['To'] = target_email

        count = len(doc_records)
        now_str = datetime.now().strftime("%d %B %Y, %H:%M WIB")

        if count == 1:
            doc = doc_records[0]
            extracted = doc.extracted_data or {}
            nama_user = extracted.get("nama", {}).get("value", f"Dokumen #{doc.id}") if isinstance(extracted.get("nama"), dict) else f"Dokumen #{doc.id}"
            msg['Subject'] = f"[Laporan Verifikasi Dokumen] {nama_user}".strip()
        else:
            msg['Subject'] = f"[Laporan Verifikasi Dokumen] Ringkasan {count} Dokumen Terverifikasi"

        table_rows_html = ""
        for idx, doc in enumerate(doc_records, start=1):
            extracted = doc.extracted_data or {}
            
            tt = (doc.template_type or "KTP").lower()
            if "ktp" in tt:
                jenis_doc = "KTP Indonesia"
            elif "form" in tt:
                jenis_doc = "Form Pendaftaran"
            else:
                jenis_doc = doc.template_type.replace("_", " ").title()

            nama_val = "-"
            if isinstance(extracted.get("nama"), dict):
                nama_val = extracted.get("nama", {}).get("value", "-")
            elif "nama" in extracted and isinstance(extracted["nama"], str):
                nama_val = extracted["nama"]
            elif isinstance(extracted.get("name"), dict):
                nama_val = extracted.get("name", {}).get("value", "-")

            if not nama_val or nama_val.strip() in ["", "-"]:
                nama_val = f"Dokumen #{doc.id}"

            if len(nama_val) > 32:
                nama_display = nama_val[:30] + "..."
            else:
                nama_display = nama_val

            bg_color = "#ffffff" if idx % 2 != 0 else "#f8fafc"

            table_rows_html += f"""
              <tr style="background-color: {bg_color}; border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px 12px; text-align: center; color: #64748b; font-weight: bold;">{idx}</td>
                <td style="padding: 10px 12px; color: #334155; font-weight: 500;">{jenis_doc}</td>
                <td style="padding: 10px 12px; color: #0f172a; font-weight: 600;" title="{nama_val}">{nama_display}</td>
              </tr>
            """

        catatan_banyak = ""
        if count > 30:
            catatan_banyak = """
            <p style="font-size: 12px; color: #64748b; font-style: italic; margin-top: 8px;">
              * Menampilkan seluruh dokumen. Untuk detail lebih lengkap, silakan lihat lampiran PDF.
            </p>
            """

        html_body = f"""
        <html>
          <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #1e293b; line-height: 1.6; background-color: #f1f5f9; padding: 24px;">
            <div style="max-width: 620px; margin: 0 auto; background: #ffffff; padding: 28px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); border: 1px solid #cbd5e1;">
              
              <!-- Header -->
              <h2 style="color: #0f172a; margin-top: 0; margin-bottom: 16px; font-size: 20px; border-bottom: 2px solid #f24e1e; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                📋 Laporan Verifikasi Dokumen
              </h2>
              
              <!-- Subtext -->
              <p style="font-size: 14px; color: #475569; margin-bottom: 20px;">
                Berikut ringkasan <strong>{count} dokumen</strong> yang telah diverifikasi dan tersimpan di sistem pada <strong>{now_str}</strong>:
              </p>
              
              <!-- Tabel Ringkasan (3 Kolom) -->
              <table style="width: 100%; font-size: 13.5px; border-collapse: collapse; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; margin-bottom: 16px;">
                <thead>
                  <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1; color: #334155;">
                    <th style="padding: 10px 12px; width: 40px; text-align: center;">No</th>
                    <th style="padding: 10px 12px; text-align: left; width: 140px;">Jenis Dokumen</th>
                    <th style="padding: 10px 12px; text-align: left;">Nama / Identitas Utama</th>
                  </tr>
                </thead>
                <tbody>
                  {table_rows_html}
                </tbody>
              </table>

              {catatan_banyak}

              <!-- Notice Lampiran -->
              <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px 16px; margin-top: 20px; color: #1e40af; font-size: 13px; display: flex; align-items: center; gap: 10px;">
                <span>📎 <strong>Detail lengkap tiap dokumen</strong> (termasuk foto dokumen asli) tersedia dalam lampiran PDF pada email ini.</span>
              </div>

              <!-- Footer -->
              <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0 16px 0;" />
              <p style="font-size: 12px; color: #94a3b8; text-align: center; margin: 0; line-height: 1.5;">
                Email ini dikirim otomatis oleh <strong>Sistem OCR Koperasi</strong>.<br/>Mohon tidak membalas email ini.
              </p>

            </div>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        for idx, doc in enumerate(doc_records, start=1):
            extracted = doc.extracted_data or {}
            nik = extracted.get("nik", {}).get("value", "") if isinstance(extracted.get("nik"), dict) else ""

            # Generate Temp PDF Report
            temp_pdf_path = os.path.join(UPLOAD_DIR, f"Report_KTP_{doc.id}_{nik}.pdf")
            try:
                generate_document_pdf(doc, temp_pdf_path)
                temp_files_to_cleanup.append(temp_pdf_path)

                with open(temp_pdf_path, "rb") as f:
                    mime_pdf = MIMEBase("application", "pdf")
                    mime_pdf.set_payload(f.read())
                    encoders.encode_base64(mime_pdf)
                    mime_pdf.add_header("Content-Disposition", "attachment", filename=f"Hasil_Verifikasi_KTP_{nik or doc.id}.pdf")
                    msg.attach(mime_pdf)
            except Exception as pdf_err:
                print(f"Error generating PDF for doc {doc.id}: {pdf_err}")

            # Attach Original KTP Image File
            fn = (doc.filename or "").replace("uploads/", "").replace("uploads\\", "")
            img_path = os.path.join(UPLOAD_DIR, fn)
            local_temp_img = None

            if not os.path.exists(img_path) and (fn.startswith("http://") or fn.startswith("https://")):
                try:
                    import urllib.request
                    import tempfile
                    ext = os.path.splitext(fn)[1] or ".jpg"
                    t_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                    t_file.close()
                    urllib.request.urlretrieve(fn, t_file.name)
                    img_path = t_file.name
                    local_temp_img = t_file.name
                    temp_files_to_cleanup.append(local_temp_img)
                except Exception as dl_img_err:
                    print(f"Warning downloading image for email attachment: {dl_img_err}")

            if os.path.exists(img_path):
                try:
                    with open(img_path, "rb") as f:
                        img_ext = os.path.splitext(img_path)[1].lstrip('.').lower() or 'jpeg'
                        mime_img = MIMEBase("image", img_ext)
                        mime_img.set_payload(f.read())
                        encoders.encode_base64(mime_img)
                        mime_img.add_header("Content-Disposition", "attachment", filename=f"Foto_KTP_{nik or doc.id}.{img_ext}")
                        msg.attach(mime_img)
                except Exception as img_err:
                    print(f"Error attaching image for doc {doc.id}: {img_err}")

        # Koneksi SMTP Gmail & Kirim
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_PENGIRIM, app_pwd)
        server.send_message(msg)
        server.quit()

        return True, "Email berhasil dikirim."

    except Exception as e:
        print(f"SMTP Error: {e}")
        return False, f"Gagal mengirim email: {str(e)}"
    finally:
        # Guarantees cleanup of all temporary PDF and downloaded image files
        for tmp_f in temp_files_to_cleanup:
            if os.path.exists(tmp_f):
                try:
                    os.remove(tmp_f)
                except Exception as c_err:
                    print(f"Warning cleaning up temp file {tmp_f}: {c_err}")

