# MyCG AI Service - API Documentation

## Overview

The MyCG AI Service provides REST APIs for document processing, AI-powered analysis, and WhatsApp integration for accounting and GST compliance.

**Base URL**: `http://localhost:8001` (development) / `https://api.mycg.app` (production)

## Authentication

All API endpoints require authentication via API key in the header:

```bash
Authorization: Bearer your-api-key-here
```

## Document Processing APIs

### Upload Document for Processing

Process documents (bank statements, invoices, notices) with OCR and AI analysis.

**Endpoint**: `POST /api/v1/document/process`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (file, required): Document file (PDF, JPEG, PNG)
- `user_id` (string, required): User identifier
- `document_type` (string, optional): Document type (`auto`, `bank_statement`, `invoice`, `gst_notice`)
- `ocr_method` (string, optional): OCR method (`auto`, `tesseract`, `easyocr`, `google_vision`)

**Example Request**:
```bash
curl -X POST "http://localhost:8001/api/v1/document/process" \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@bank_statement.pdf" \
  -F "user_id=user_123" \
  -F "document_type=bank_statement"
```

**Response**:
```json
{
  "message": "Document uploaded successfully",
  "processing_id": "user_123_uuid",
  "status": "processing",
  "estimated_time": "1-2 minutes"
}
```

### Get Processing Status

Check the status of document processing.

**Endpoint**: `GET /api/v1/document/status/{processing_id}`

**Example**:
```bash
curl "http://localhost:8001/api/v1/document/status/user_123_uuid" \
  -H "Authorization: Bearer your-api-key"
```

**Response**:
```json
{
  "processing_id": "user_123_uuid",
  "status": "completed",
  "message": "Check your Node.js backend for results"
}
```

## AI Services APIs

### Ask AI Question

Get answers to GST, tax, and compliance questions.

**Endpoint**: `POST /api/v1/ai/query`

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "query": "What is the GST rate for software services?",
  "context": "Optional context",
  "user_id": "user_123",
  "query_type": "gst"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/ai/query" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the GST rate for software services?",
    "user_id": "user_123",
    "query_type": "gst"
  }'
```

**Response**:
```json
{
  "answer": "The GST rate for software services is 18%. This applies to software development, maintenance, and support services provided by businesses.",
  "confidence": "high",
  "sources": ["GST Act", "AI Analysis"],
  "follow_up_questions": [
    "What about export of software services?",
    "Are there any exemptions for software services?"
  ],
  "query_id": "gst_1234"
}
```

### Analyze Government Notice

Analyze government notices and get actionable insights.

**Endpoint**: `POST /api/v1/ai/analyze-notice`

**Request Body**:
```json
{
  "notice_text": "Your GSTR-1 for October 2023 is pending...",
  "notice_type": "gst",
  "user_id": "user_123"
}
```

**Response**:
```json
{
  "notice_type": "gst",
  "urgency": "high",
  "key_points": [
    "Missing GSTR-1 filing for October 2023",
    "Late fee applicable"
  ],
  "required_actions": [
    "File GSTR-1 immediately",
    "Pay applicable late fees"
  ],
  "due_date_mentioned": true,
  "extracted_due_date": "2024-01-20",
  "suggested_response": "File the return immediately with applicable late fees to avoid further penalties",
  "confidence": 0.9
}
```

### Generate Notice Reply

Generate a reply draft for government notices.

**Endpoint**: `POST /api/v1/ai/generate-reply/{notice_id}`

**Request Body**: Notice analysis object

**Response**:
```json
{
  "notice_id": "notice_123",
  "reply_draft": "Dear Sir/Madam,\n\nWe acknowledge receipt of your notice dated...",
  "status": "generated"
}
```

### Suggest Recurring Entries

Get AI-powered suggestions for recurring transactions.

**Endpoint**: `POST /api/v1/ai/suggest-recurring`

**Parameters**:
- `user_id` (string, required): User identifier
- `transaction_limit` (integer, optional): Number of transactions to analyze (default: 50)

**Response**:
```json
{
  "user_id": "user_123",
  "suggestions": [
    {
      "description": "Office Rent",
      "amount": 50000,
      "frequency": "monthly",
      "category": "Office Expenses",
      "confidence": 0.95,
      "next_due_estimate": "2024-02-01"
    }
  ],
  "count": 1
}
```

## WhatsApp APIs

### Webhook Endpoint

Handle incoming WhatsApp messages (configured with Twilio).

**Endpoint**: `POST /api/v1/whatsapp/webhook`

**Content-Type**: `application/x-www-form-urlencoded`

This endpoint is automatically called by Twilio when messages are received.

### Send Message

Send WhatsApp message programmatically.

**Endpoint**: `POST /api/v1/whatsapp/send-message`

**Parameters**:
- `to_number` (string): Recipient phone number
- `message` (string): Message text

**Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/whatsapp/send-message" \
  -H "Authorization: Bearer your-api-key" \
  -d "to_number=+1234567890&message=Hello from MyCG!"
```

### Send Notification

Send formatted notifications via WhatsApp.

**Endpoint**: `POST /api/v1/whatsapp/send-notification`

**Request Body**:
```json
{
  "to_number": "+1234567890",
  "notification_type": "gst_reminder",
  "data": {
    "due_date": "2024-01-20",
    "business_name": "ABC Company"
  }
}
```

**Notification Types**:
- `gst_reminder`: GST filing reminders
- `document_processed`: Document processing completion
- `compliance_alert`: Compliance alerts

## Health Check APIs

### Basic Health Check

**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "MyCG AI Service",
  "version": "1.0.0",
  "uptime": "2:15:30"
}
```

### Detailed Health Check

**Endpoint**: `GET /api/v1/health/detailed`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "redis": {"status": "healthy", "response_time_ms": 5.2},
    "node_backend": {"status": "healthy", "response_time_ms": 150.3}
  },
  "system": {
    "cpu_percent": 15.3,
    "memory_percent": 45.2,
    "disk_percent": 60.1
  },
  "ai_services": {
    "openai": {"status": "healthy"},
    "google_vision": {"status": "configured"}
  }
}
```

## Error Responses

All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": "Error description",
  "error_type": "ValidationException",
  "request_id": "req_abc123",
  "path": "/api/v1/document/process"
}
```

**Common HTTP Status Codes**:
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (missing/invalid API key)
- `422`: Unprocessable Entity (file processing error)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error
- `503`: Service Unavailable (AI services down)

## Rate Limits

- General API: 10 requests/second
- WhatsApp webhook: 50 requests/second
- Document upload: 10 requests/second per user

## WebSocket Support

Real-time updates for document processing status:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/processing/{processing_id}');
ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log('Processing status:', status);
};
```