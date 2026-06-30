import os
import pytz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse

from backend.app import routes
from backend.app.config import Settings
from backend.app.database import get_db
from backend.app.services import gatepass_service

@routes.get("/gatepass/{pass_number}/print")
async def print_gatepass(pass_number: str, db=Depends(get_db)):
    """
    Print gatepass as PDF (with QR code and exit/return photos).
    Only approved gatepasses can be printed.
    """
    

    PKT = pytz.timezone("Asia/Karachi")
    PAGE_WIDTH, PAGE_HEIGHT = letter
    BOTTOM_MARGIN = 10  # Minimum space from bottom of page

    gp = gatepass_service.get_gatepass_by_number(db, pass_number)

    if not gp:
        raise HTTPException(status_code=404, detail=f"Gate pass {pass_number} not found")

    # Status must be approved or returned
    status = str(gp.get("status", "")).strip().lower()
    if status == "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Gate pass {pass_number} is not approved. Current status: {gp.get('status')}."
        )

    try:
        os.makedirs(Settings.MEDIA_ROOT, exist_ok=True)

        filename = f"{gp['number']}.pdf"
        file_path = os.path.join(Settings.MEDIA_ROOT, filename)

        c = canvas.Canvas(file_path, pagesize=letter)

        # Helper function to check if we need a new page
        def check_new_page(current_y, required_space):
            if current_y - required_space < BOTTOM_MARGIN:
                c.showPage()
                return PAGE_HEIGHT - 50  # Start from top with margin
            return current_y

        # ----------------------------------------------------------
        # Load and Draw Logo
        # ----------------------------------------------------------
        original_logo_path = "/home/ubuntu/gatepass/media/logo.png"
        logo_path = original_logo_path
        logo_height = 0
        temp_logo_file = None

        if os.path.exists(original_logo_path):
            try:
                # Draw logo
                if logo_path and os.path.exists(logo_path):
                    logo_width = 120
                    logo_height = 60
                    logo_x = (PAGE_WIDTH - logo_width) / 2
                    logo_y = PAGE_HEIGHT - 100
                    c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)

            finally:
                if temp_logo_file and os.path.exists(temp_logo_file.name):
                    try:
                        os.unlink(temp_logo_file.name)
                    except:
                        pass

        start_y = PAGE_HEIGHT - 140

        # ----------------------------------------------------------
        # Text Fields
        # ----------------------------------------------------------
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, start_y, f"Gate Pass: {gp['number']}")

        c.setFont("Helvetica", 11)
        current_y = start_y - 25

        current_y = check_new_page(current_y, 20)
        c.setFont("Helvetica", 11)
        c.drawString(100, current_y, f"Name: {gp['person_name']}")
        current_y -= 20

        # Handle long description with text wrapping
        description_text = f"Description: {gp['description']}"
        max_width = PAGE_WIDTH - 200  # Leave margins on both sides
        
        # Split the description into multiple lines if needed
        description_lines = simpleSplit(description_text, "Helvetica", 11, max_width)
        
        for line in description_lines:
            current_y = check_new_page(current_y, 20)
            c.setFont("Helvetica", 11)
            c.drawString(100, current_y, line)
            current_y -= 20

        current_y = check_new_page(current_y, 20)
        c.setFont("Helvetica", 11)
        c.drawString(100, current_y, f"Status: {gp['status']}")
        current_y -= 20

        current_y = check_new_page(current_y, 20)
        c.setFont("Helvetica", 11)
        c.drawString(100, current_y, f"Type: {'Returnable' if gp.get('is_returnable') else 'Non-Returnable'}")

        # ----------------------------------------------------------
        # Date Formatter
        # ----------------------------------------------------------
        def format_pkt_time(dt):
            if not dt:
                return None
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt).astimezone(PKT)
            else:
                dt = dt.astimezone(PKT)
            return dt.strftime('%Y-%m-%d %H:%M:%S') + ' PKT'

        current_y -= 20
        current_y = check_new_page(current_y, 20)
        c.setFont("Helvetica", 11)
        c.drawString(100, current_y, f"Created At: {format_pkt_time(gp.get('created_at'))}")
        current_y -= 20

        if gp.get("approved_at"):
            current_y = check_new_page(current_y, 40)
            c.setFont("Helvetica", 11)
            c.drawString(100, current_y, f"Approved At: {format_pkt_time(gp.get('approved_at'))}")
            current_y -= 40

        # ----------------------------------------------------------
        # QR Code
        # ----------------------------------------------------------
        if gp.get("qr_code_url"):
            qr_path = os.path.join(Settings.MEDIA_ROOT, Settings.QR_DIR, f"{gp['number']}.png")

            if not os.path.exists(qr_path):
                qr_path = "." + gp["qr_code_url"] if gp["qr_code_url"].startswith("/") else gp["qr_code_url"]

            if os.path.exists(qr_path):
                current_y = check_new_page(current_y, 130)  # QR code + label space
                qr_y = current_y - 120
                c.drawImage(qr_path, 100, qr_y, width=130, height=130)
                c.setFont("Helvetica", 11)
                c.drawString(100, qr_y - 20, "Scan QR code at gate")
                current_y = qr_y - 40

        # ----------------------------------------------------------
        # Exit + Return Photos (SIDE BY SIDE) - Only if photos exist
        # ----------------------------------------------------------
        exit_photo_id = gp.get("exit_photo_id")
        return_photo_id = gp.get("return_photo_id")

        exit_photo_path = None
        return_photo_path = None

        if exit_photo_id:
            ep = os.path.join(Settings.MEDIA_ROOT, Settings.PHOTO_DIR, exit_photo_id)
            if os.path.exists(ep):
                exit_photo_path = ep

        if return_photo_id:
            rp = os.path.join(Settings.MEDIA_ROOT, Settings.PHOTO_DIR, return_photo_id)
            if os.path.exists(rp):
                return_photo_path = rp

        # Only show photo section if at least one photo exists
        if exit_photo_path or return_photo_path:
            photo_w = 180
            photo_h = 150
            
            # Check if we need new page for photos (title + photo + timestamp)
            required_space = 30 + photo_h + 40
            current_y = check_new_page(current_y, required_space)
            
            current_y -= 30
            c.setFont("Helvetica-Bold", 11)
            
            # Show titles only for photos that exist
            if exit_photo_path:
                c.drawString(100, current_y, "Exit Photo")
            if return_photo_path:
                c.drawString(350, current_y, "Return Photo")
            
            current_y -= 10

            # Exit Photo
            if exit_photo_path:
                try:
                    c.drawImage(exit_photo_path, 100, current_y - photo_h, width=photo_w, height=photo_h)
                    ts = format_pkt_time(gp.get("exit_time"))
                    if ts:
                        c.setFont("Helvetica", 8)
                        c.drawString(100, current_y - photo_h - 12, f"Captured: {ts}")
                        c.setFont("Helvetica-Bold", 12)  # Reset font for next section
                except Exception as e:
                    c.setFont("Helvetica", 10)
                    c.drawString(100, current_y - 12, f"Photo error: {str(e)[:50]}")
                    c.setFont("Helvetica-Bold", 12)

            # Return Photo
            if return_photo_path:
                try:
                    c.drawImage(return_photo_path, 350, current_y - photo_h, width=photo_w, height=photo_h)
                    ts = format_pkt_time(gp.get("return_time"))
                    if ts:
                        c.setFont("Helvetica", 8)
                        c.drawString(350, current_y - photo_h - 12, f"Captured: {ts}")
                except Exception as e:
                    c.setFont("Helvetica", 10)
                    c.drawString(350, current_y - 12, f"Photo error: {str(e)[:50]}")

            current_y -= (photo_h + 40)

        # ----------------------------------------------------------
        # End PDF
        # ----------------------------------------------------------
        c.showPage()
        c.save()

        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF file")

        return FileResponse(file_path, media_type="application/pdf", filename=filename)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )
