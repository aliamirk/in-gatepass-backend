from typing import List
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import FileResponse
from reportlab.pdfgen import canvas
import os
import pytz
import re
from ..database import get_db
from ..schemas.gatepass import GatePassCreate, GatePassOut
from ..services import hr_service, gatepass_service
from ..config import settings

# Pakistan timezone
PKT = pytz.timezone('Asia/Karachi')

router = APIRouter(prefix="/hr", tags=["hr"])

# Default system user ID (no authentication required)
SYSTEM_USER_ID = "system"


def serialize_gatepass(doc) -> GatePassOut:
    from bson import ObjectId
    doc_id = str(doc["_id"]) if isinstance(doc["_id"], ObjectId) else doc["_id"]
    created_by = str(doc["created_by"]) if isinstance(doc["created_by"], ObjectId) else doc["created_by"]
    
    return GatePassOut(
        id=doc_id,
        number=doc["number"],
        person_name=doc["person_name"],
        description=doc["description"],
        created_by=created_by,
        status=doc["status"],
        created_at=doc["created_at"],
        entry_time=doc.get("entry_time"),
        qr_code_url=doc.get("qr_code_url"),
    )


@router.post("/gatepass/create", response_model=GatePassOut)
async def create_gatepass(payload: GatePassCreate, db=Depends(get_db)):
    doc = hr_service.create_gatepass_for_hr(db, SYSTEM_USER_ID, payload)
    return serialize_gatepass(doc)


@router.get("/gatepass/list", response_model=List[GatePassOut])
async def list_my_gatepasses(
    status: str | None = None,
    db=Depends(get_db),
):
    docs = hr_service.list_hr_gatepasses(db, SYSTEM_USER_ID, status)
    return [serialize_gatepass(d) for d in docs]





@router.get("/indexed/search", response_model=List[GatePassOut])
async def search_gatepasses(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(250, le=500),
    skip: int = Query(0),
    db=Depends(get_db)
):
    q = q.strip()
    raw_tokens = [t for t in re.split(r'[\s,]+', q) if t]
    escaped_tokens = [re.escape(t) for t in raw_tokens]

    if not escaped_tokens:
        return []

    # Fetch all matches (any token in name OR description)
    token_clauses = []
    for token in escaped_tokens:
        token_clauses.append({"person_name": {"$regex": token, "$options": "i"}})
        token_clauses.append({"description": {"$regex": token, "$options": "i"}})

    query_filter = {"$or": token_clauses}
    collection = db["gatepasses"]  # adjust if your collection name differs
    docs = list(collection.find(query_filter).sort("created_at", -1).limit(500))

    # Score each document
    def score_doc(doc):
        name = (doc.get("person_name") or "").lower()
        desc = (doc.get("description") or "").lower()
        q_lower = q.lower()

        name_exact = 0
        name_token_score = 0
        desc_token_score = 0

        # Highest priority: full query matches name exactly or name contains full query
        if q_lower == name:
            name_exact = 1000
        elif q_lower in name:
            name_exact = 500

        # Per token: name matches outrank description matches
        for token in raw_tokens:
            t = token.lower()
            if re.search(re.escape(t), name, re.IGNORECASE):
                name_token_score += 10   # each token found in name = +10
            if re.search(re.escape(t), desc, re.IGNORECASE):
                desc_token_score += 1    # each token found in description = +1

        total = name_exact + name_token_score + desc_token_score
        return total

    scored = [(score_doc(doc), doc) for doc in docs]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Apply skip and limit after scoring
    paged = scored[skip: skip + limit]
    return [serialize_gatepass(doc) for _, doc in paged]




@router.get("/analytics")
async def get_gatepass_analytics(db=Depends(get_db)):
    collection = db["gatepasses"]
    total = collection.count_documents({})
    created = collection.count_documents({"status": "created"})
    entered = collection.count_documents({"status": "entered"})
    return {"total": total, "created": created, "entered": entered}





@router.get("/gatepass/{pass_id}", response_model=GatePassOut)
async def get_gatepass_detail(pass_id: str, db=Depends(get_db)):
    doc = hr_service.get_hr_gatepass_detail(db, pass_id)
    return serialize_gatepass(doc)



@router.get("/gatepass/{pass_number}/print")
async def print_gatepass(pass_number: str, db=Depends(get_db)):
    """
    Print gatepass as PDF with logo, QR code, and scanned entry photos.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import simpleSplit

    PAGE_WIDTH, PAGE_HEIGHT = letter
    BOTTOM_MARGIN = 10

    gp = gatepass_service.get_gatepass_by_number(db, pass_number)

    if not gp:
        raise HTTPException(status_code=404, detail=f"Gate pass {pass_number} not found")

    try:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        filename = f"{gp['number']}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        c = canvas.Canvas(file_path, pagesize=letter)

        def check_new_page(current_y, required_space):
            if current_y - required_space < BOTTOM_MARGIN:
                c.showPage()
                return PAGE_HEIGHT - 50
            return current_y

        def format_pkt_time(dt):
            if not dt:
                return None
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt).astimezone(PKT)
            else:
                dt = dt.astimezone(PKT)
            return dt.strftime('%Y-%m-%d %H:%M:%S') + ' PKT'

        # ----------------------------------------------------------
        # Logo
        # ----------------------------------------------------------
        logo_path = os.path.normpath(settings.LOGO_PATH)
        if logo_path and os.path.exists(logo_path):
            logo_width = 120
            logo_height = 60
            logo_x = (PAGE_WIDTH - logo_width) / 2
            logo_y = PAGE_HEIGHT - 100
            c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)
            start_y = PAGE_HEIGHT - 140
        else:
            start_y = PAGE_HEIGHT - 80

        # ----------------------------------------------------------
        # Text Fields
        # ----------------------------------------------------------
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, start_y, f"Gate Pass: {gp['number']}")
        current_y = start_y - 25

        c.setFont("Helvetica", 12)
        current_y = check_new_page(current_y, 20)
        c.drawString(100, current_y, f"Name: {gp['person_name']}")
        current_y -= 20

        description_lines = simpleSplit(f"Description: {gp['description']}", "Helvetica", 12, PAGE_WIDTH - 200)
        for line in description_lines:
            current_y = check_new_page(current_y, 20)
            c.drawString(100, current_y, line)
            current_y -= 20

        current_y = check_new_page(current_y, 20)
        c.drawString(100, current_y, f"Status: {gp['status']}")
        current_y -= 20

        current_y -= 10
        current_y = check_new_page(current_y, 20)
        c.drawString(100, current_y, f"Created At: {format_pkt_time(gp.get('created_at'))}")
        current_y -= 20

        # ----------------------------------------------------------
        # QR Code
        # ----------------------------------------------------------
        if gp.get("qr_code_url"):
            qr_path = os.path.join(settings.MEDIA_ROOT, settings.QR_DIR, f"{gp['number']}.png")
            if not os.path.exists(qr_path):
                qr_path = "." + gp["qr_code_url"] if gp["qr_code_url"].startswith("/") else gp["qr_code_url"]
            if os.path.exists(qr_path):
                current_y = check_new_page(current_y, 170)
                qr_y = current_y - 150
                c.drawImage(qr_path, 100, qr_y, width=150, height=150)
                c.setFont("Helvetica", 11)
                c.drawString(100, qr_y - 20, "Scan QR code at gate")
                current_y = qr_y - 40

        # ----------------------------------------------------------
        # Scanned Entry Photos
        # ----------------------------------------------------------
        scan_photos = list(
            db["photos"]
            .find({"pass_number": pass_number, "type": "entry"})
            .sort("captured_at", 1)
        )

        if scan_photos:
            photo_w = 180
            photo_h = 150
            photos_per_row = 2
            col_positions = [100, 350]

            current_y = check_new_page(current_y, 30)
            current_y -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, current_y, "Scanned Entry Photos")
            current_y -= 15

            for idx, photo_doc in enumerate(scan_photos):
                col = idx % photos_per_row
                if col == 0:
                    current_y = check_new_page(current_y, 20 + photo_h + 20)
                    current_y -= 20

                photo_id = photo_doc.get("photo_id", "")
                photo_file = os.path.join(settings.MEDIA_ROOT, settings.PHOTO_DIR, photo_id)
                x = col_positions[col]

                c.setFont("Helvetica-Bold", 10)
                c.drawString(x, current_y, f"Photo {idx + 1}")

                if photo_file and os.path.exists(photo_file):
                    try:
                        c.drawImage(
                            photo_file, x, current_y - photo_h - 12,
                            width=photo_w, height=photo_h,
                            preserveAspectRatio=True, mask="auto"
                        )
                        ts = format_pkt_time(photo_doc.get("captured_at"))
                        if ts:
                            c.setFont("Helvetica", 8)
                            c.drawString(x, current_y - photo_h - 24, f"Captured: {ts}")
                    except Exception as img_err:
                        c.setFont("Helvetica", 9)
                        c.drawString(x, current_y - 20, f"Photo error: {str(img_err)[:50]}")
                else:
                    c.setFont("Helvetica", 9)
                    c.drawString(x, current_y - 20, "Photo file not found")

                if col == photos_per_row - 1 or idx == len(scan_photos) - 1:
                    current_y -= (photo_h + 40)

        # ----------------------------------------------------------
        # Signature Section (3 columns, side by side)
        # ----------------------------------------------------------
        current_y = check_new_page(current_y, 80)
        current_y -= 40

        sig_line_width = 130
        usable_width = PAGE_WIDTH - 200   # 100 margin each side
        col_gap = (usable_width - 3 * sig_line_width) / 2
        sig_x1 = 100
        sig_x2 = sig_x1 + sig_line_width + col_gap
        sig_x3 = sig_x2 + sig_line_width + col_gap

        # Draw lines
        c.setLineWidth(0.5)
        c.line(sig_x1, current_y, sig_x1 + sig_line_width, current_y)
        c.line(sig_x2, current_y, sig_x2 + sig_line_width, current_y)
        c.line(sig_x3, current_y, sig_x3 + sig_line_width, current_y)

        # Labels below lines
        c.setFont("Helvetica", 8)
        c.drawCentredString(sig_x1 + sig_line_width / 2, current_y - 14, "HR Signature")
        c.drawCentredString(sig_x2 + sig_line_width / 2, current_y - 14, "Incharge Signature")
        c.drawCentredString(sig_x3 + sig_line_width / 2, current_y - 14, "Owner / Authorized Signatory")

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

