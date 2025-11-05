from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse
import os
from accounting_app.services import loans_harvester as L

router = APIRouter(prefix="/loans", tags=["loans"])

@router.get("/updates")
def list_updates(q: str | None = None, limit: int = 100):
    L.init()
    return L.list_updates(q, limit)

@router.get("/intel")
def list_intel(q: str | None = None, limit: int = 200):
    L.init()
    return L.list_intel(q, limit)

@router.get("/updates/last")
def last():
    return {"last_harvest_at": L.get_last_harvest(), "min_hours": int(os.getenv("MIN_REFRESH_HOURS","20"))}

@router.post("/updates/refresh")
def refresh(request: Request, x_refresh_key: str | None = Header(None)):
    expect = os.getenv("LOANS_REFRESH_KEY")
    if not expect or x_refresh_key != expect:
        raise HTTPException(401, "unauthorized")
    done, ts = L.harvest_if_due(force=True)
    return {"refreshed": done, "at": ts}

@router.get("/updates/export.csv")
def export_updates(q: str | None = None, limit: int = 1000):
    rows = L.list_updates(q, limit)
    data = L.export_csv(rows)
    return StreamingResponse(iter([data]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=loan_updates.csv","Cache-Control":"private, max-age=600"})

@router.get("/intel/export.csv")
def export_intel(q: str | None = None, limit: int = 1000):
    rows = L.list_intel(q, limit)
    data = L.export_csv(rows)
    return StreamingResponse(iter([data]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=loan_intel.csv","Cache-Control":"private, max-age=600"})
