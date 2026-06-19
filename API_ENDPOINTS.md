# Gate Pass Management System - API Endpoints

## System Workflow

1. **HR creates gate pass** → QR code generated automatically → Admin gets notification
2. **Admin approves/rejects** gate pass → HR gets notification
3. **HR/Admin prints** gate pass (with QR code)
4. **Gate person scans QR** at exit → Photo uploaded → Status updated
5. **For returnable passes**: Gate person scans QR at return → Photo uploaded → Status updated

## API Endpoints

### HR Routes (`/hr`)

- `POST /hr/gatepass/create` - Create a new gate pass
  - Body: `{person_name: str, description: str, is_returnable: bool}`
  - Returns: GatePass with QR code URL
  - Auto-generates QR code and notifies admin

- `GET /hr/gatepass/list?status=<status>` - List gate passes created by HR
  - Query params: `status` (optional): pending, approved, rejected, etc.

- `GET /hr/gatepass/{pass_id}` - Get gate pass details

- `GET /hr/gatepass/{pass_id}/print` - Print gate pass as PDF (with QR code)
  - Only works for approved gate passes
  - Returns PDF file

### Admin Routes (`/admin`)

- `GET /admin/gatepass/pending` - Get all pending gate passes

- `GET /admin/gatepass/all?status=<status>` - Get all gate passes
  - Query params: `status` (optional)

- `GET /admin/gatepass/{pass_id}` - Get gate pass details

- `POST /admin/gatepass/{pass_id}/approve` - Approve a gate pass
  - Updates status to "approved"
  - Notifies HR

- `POST /admin/gatepass/{pass_id}/reject` - Reject a gate pass
  - Updates status to "rejected"
  - Notifies HR

- `GET /admin/gatepass/{pass_id}/print` - Print gate pass as PDF (with QR code)
  - Returns PDF file

### Gate Routes (`/gate`)

- `POST /gate/scan-exit` - Scan QR code at gate exit
  - Form data: `pass_number: str` (required, e.g., "GP-2024-0001"), `file: UploadFile` (required photo)
  - Validates gatepass is approved
  - Uploads and stores photo in database with gatepass linkage
  - Updates status to "pending_return" (if returnable) or "completed" (if not)
  - Photo is stored with gatepass_id, type ("exit"), timestamp, and gate user info

- `POST /gate/scan-return` - Scan QR code at gate return
  - Form data: `pass_number: str` (required, e.g., "GP-2024-0001"), `file: UploadFile` (required photo)
  - Only for returnable gate passes with status "pending_return"
  - Uploads and stores photo in database with gatepass linkage
  - Updates status to "returned"
  - Photo is stored with gatepass_id, type ("return"), timestamp, and gate user info

- `GET /gate/gatepass/number/{pass_number}` - Get gatepass details by pass number
  - Use this when scanning QR code (QR contains pass number like "GP-2024-0001")
  - Returns full gatepass details including id, status, etc.

- `GET /gate/gatepass/id/{pass_id}` - Get gatepass details by pass ID
  - Use this when you have the gatepass ID (internal use)

- `GET /gate/photos/{pass_number}` - Get all photos for a gatepass by pass number
  - Returns all photos (exit and return) associated with the gatepass
  - Includes photo_id, file_url, type, captured_at, captured_by, pass_number
  - Query photos by pass_number directly (e.g., "GP-2024-0001")

### Notification Routes (`/notifications`)

- `GET /notifications/admin` - Get all notifications for admin

- `GET /notifications/hr` - Get all notifications for HR

- `GET /notifications/mark-read/{notification_id}` - Mark notification as read

### QR Code Routes (`/qr`)

- `GET /qr/{pass_number}` - Get QR code image for a gate pass number
  - Returns PNG image
  - Example: `/qr/GP-2024-0001`

### Media Routes (`/media`)

- `POST /media/upload-photo` - Upload a photo (generic)

- `GET /media/photo/{photo_id}` - Get photo by ID

### Pass Routes (`/pass`)

- `GET /pass/list?status=<status>` - List all gate passes
  - Query params: `status` (optional)

## Gate Pass Statuses

- `pending` - Created by HR, waiting for admin approval
- `approved` - Approved by admin, ready to use
- `rejected` - Rejected by admin
- `pending_return` - Used at exit (for returnable passes), waiting for return
- `completed` - Used at exit (for non-returnable passes)
- `returned` - Returned at gate (for returnable passes)

## Gate Pass Types

- **Returnable**: Person must return and scan again at gate
- **Non-returnable**: Single use, no return required

## Data Models

### GatePass
```json
{
  "id": "string",
  "number": "GP-2024-0001",
  "person_name": "string",
  "description": "string",
  "created_by": "string",
  "is_returnable": true/false,
  "status": "pending|approved|rejected|pending_return|completed|returned",
  "status_history": [...],
  "created_at": "datetime",
  "approved_at": "datetime",
  "exit_photo_id": "string",
  "return_photo_id": "string",
  "exit_time": "datetime",
  "return_time": "datetime",
  "qr_code_url": "/qr/GP-2024-0001"
}
```

### Notification
```json
{
  "notf_id": "string",
  "user_id": "admin|hr",
  "title": "string",
  "message": "string",
  "gatepass_id": "string",
  "is_read": false,
  "created_at": "datetime"
}
```

### Photo
```json
{
  "photo_id": "string",
  "gatepass_id": "string",
  "file_url": "/media/photo/{filename}",
  "type": "exit|return",
  "captured_at": "datetime",
  "captured_by": "string",
  "pass_number": "GP-2024-0001"
}
```

## Example Workflow

1. HR creates gate pass:
   ```
   POST /hr/gatepass/create
   {
     "person_name": "John Doe",
     "description": "Meeting with client",
     "is_returnable": true
   }
   ```
   - Returns gate pass with QR code
   - Admin receives notification

2. Admin approves:
   ```
   POST /admin/gatepass/{pass_id}/approve
   ```
   - HR receives notification

3. HR/Admin prints:
   ```
   GET /hr/gatepass/{pass_id}/print
   ```
   - Returns PDF with QR code

4. Gate person scans QR code at exit:
   ```
   # QR code contains pass number (e.g., "GP-2024-0001")
   # Directly scan exit with pass_number and photo
   POST /gate/scan-exit
   pass_number: GP-2024-0001
   file: [photo file]
   ```
   - Photo is stored in database with gatepass linkage
   - Updates status to "pending_return"
   - Can view photos: `GET /gate/photos/GP-2024-0001`

5. Gate person scans at return (if returnable):
   ```
   POST /gate/scan-return
   pass_number: GP-2024-0001
   file: [photo file]
   ```
   - Photo is stored in database with gatepass linkage
   - Updates status to "returned"
   - Can view all photos: `GET /gate/photos/GP-2024-0001`

