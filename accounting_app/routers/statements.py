from fastapi import APIRouter, UploadFile, File, HTTPException
from accounting_app.services.statements_parsers import StatementAutoDetector
router = APIRouter(prefix="/credit-cards/statements", tags=["credit_cards.statements"])

@router.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF statement")
    pdf_bytes = await file.read()
    try:
        res = StatementAutoDetector().parse(pdf_bytes).to_dict()
        return res
    except Exception as e:
        raise HTTPException(500, f"Failed to parse PDF: {str(e)}")
