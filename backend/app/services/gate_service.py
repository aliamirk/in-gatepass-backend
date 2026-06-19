import asyncio
from typing import Optional, Dict, Any, List
from fastapi import UploadFile, HTTPException
from datetime import datetime
from pytz import timezone

from ..utils.photo_upload import save_photo_file
from . import gatepass_service

# Pakistan Standard Time
PKT = timezone('Asia/Karachi')


async def process_entry_scan(db, pass_number: str, files: List[UploadFile], gate_user_id: str) -> Dict[str, Any]:
    """
    Process entry scan: save multiple photos atomically and update gatepass status to 'entered'.
    No status pre-check - any gatepass can accept entry photos regardless of current status.
    """
    from bson import ObjectId

    # Get gatepass by number (raises 404 if missing)
    gp = gatepass_service.get_gatepass_by_number(db, pass_number)
    gatepass_id = gp["_id"]

    # Save all files concurrently
    filenames = await asyncio.gather(*(save_photo_file(f) for f in files))

    # Build photo records
    now = datetime.now(PKT)
    photo_records = []
    for filename in filenames:
        photo_records.append({
            "photo_id": filename,
            "gatepass_id": gatepass_id,
            "file_url": f"/media/photo/{filename}",
            "type": "entry",
            "captured_at": now,
            "captured_by": gate_user_id,
            "pass_number": pass_number,
        })

    # Insert all records atomically
    try:
        db["photos"].insert_many(photo_records, ordered=True)
    except Exception:
        # Roll back any inserted records
        inserted_ids = [r["_id"] for r in photo_records if "_id" in r]
        if inserted_ids:
            db["photos"].delete_many({"_id": {"$in": inserted_ids}})
        raise HTTPException(status_code=500, detail="Failed to save photo records")

    # Update gatepass status to 'entered'
    return gatepass_service.update_gatepass_on_entry(db, pass_number, gate_user_id)


