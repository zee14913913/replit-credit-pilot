import io, re, pdfplumber, datetime as dt
from decimal import Decimal

class ParseResult:
    def __init__(self, statements=None, transactions=None, meta=None):
        self.statements = statements or {}
        self.transactions = transactions or []
        self.meta = meta or {}

    def to_dict(self): return {
        "statements": self.statements, "transactions": self.transactions, "meta": self.meta
    }

def _to_amount(x):
    if x is None: return None
    s = str(x).replace(',', '').strip()
    m = re.search(r'-?\d+(\.\d+)?', s)
    return Decimal(m.group(0)) if m else None

def _infer_date(s):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%d %b %Y"):
        try: return dt.datetime.strptime(s.strip(), fmt).date()
        except: pass
    return None

class UniversalStatementParser:
    NAME = "universal"

    def match(self, text):
        score = 0
        if re.search(r'Opening Balance|期初余额', text, re.I): score += 1
        if re.search(r'Closing Balance|期末余额', text, re.I): score += 1
        if re.search(r'Date\s+Description\s+Amount', text, re.I): score += 1
        return score >= 2

    def parse(self, pdf_bytes: bytes) -> ParseResult:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            opening = re.search(r'(Opening Balance|期初余额)\s*[:：]\s*([-,\d.]+)', full_text, re.I)
            closing = re.search(r'(Closing Balance|期末余额)\s*[:：]\s*([-,\d.]+)', full_text, re.I)
            total_pay = re.search(r'(Total Payment|本期还款)\s*[:：]\s*([-,\d.]+)', full_text, re.I)

            statements = {
                "opening_balance": _to_amount(opening.group(2)) if opening else None,
                "closing_balance": _to_amount(closing.group(2)) if closing else None,
                "total_payment": _to_amount(total_pay.group(2)) if total_pay else None,
            }

            transactions=[]
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                headers = [h.strip().lower() if h else "" for h in table[0]]
                rows = table[1:]
                if "date" in headers and "amount" in headers:
                    di = headers.index("date"); ai = headers.index("amount")
                    di_desc = headers.index("description") if "description" in headers else None
                    for r in rows:
                        if not r or len(r)<=ai: continue
                        d=_infer_date(r[di] or "")
                        desc=(r[di_desc] if di_desc is not None and di_desc<len(r) else "") or ""
                        amt=_to_amount(r[ai])
                        if d and amt is not None:
                            transactions.append({"date":str(d), "desc":desc.strip(), "amount":str(amt)})
            return ParseResult(statements, transactions, {"parser": self.NAME})

class StandardStatementParser:
    NAME="standard"

    def match(self, text):
        return bool(re.search(r'Posting Date\s+Description\s+Debit\s+Credit\s+Balance', text, re.I))

    def parse(self, pdf_bytes: bytes) -> ParseResult:
        tx=[]
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                headers=[(h or "").strip().lower() for h in table[0]]
                rows=table[1:]
                try:
                    di=headers.index("posting date"); desci=headers.index("description")
                    debi=headers.index("debit"); credi=headers.index("credit")
                except ValueError:
                    continue
                for r in rows:
                    if not r or len(r)<=max(di,desci,debi,credi): continue
                    d=_infer_date(r[di] or "")
                    desc=(r[desci] or "").strip()
                    debit=_to_amount(r[debi]); credit=_to_amount(r[credi])
                    amt = credit if credit is not None else (Decimal(0)-debit if debit is not None else None)
                    if d and amt is not None:
                        tx.append({"date":str(d),"desc":desc,"amount":str(amt)})
        return ParseResult({"pattern":"standard"}, tx, {"parser": self.NAME})

class BalanceChangeParser:
    NAME="balance_change"

    def match(self, text):
        return bool(re.search(r'Balance\s+Change|Previous Balance|New Balance', text, re.I))

    def parse(self, pdf_bytes: bytes) -> ParseResult:
        tx=[]
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    m=re.search(r'(\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}|\d{4}-\d{2}-\d{2}).+?Prev[:：]\s*([-,\d.]+).+?New[:：]\s*([-,\d.]+)', line, re.I)
                    if not m: continue
                    d=_infer_date(m.group(1))
                    prev=_to_amount(m.group(2)); new=_to_amount(m.group(3))
                    if d and prev is not None and new is not None:
                        delta=new-prev
                        desc=re.sub(r'\s+', ' ', line)
                        tx.append({"date":str(d),"desc":desc,"amount":str(delta)})
        return ParseResult({"pattern":"balance_change"}, tx, {"parser": self.NAME})

class StatementAutoDetector:
    PARSERS=[UniversalStatementParser(), StandardStatementParser(), BalanceChangeParser()]

    def detect(self, text)->str:
        for p in self.PARSERS:
            if p.match(text): return p.NAME
        return self.PARSERS[0].NAME

    def parse(self, pdf_bytes: bytes)->ParseResult:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text="\n".join([p.extract_text() or "" for p in pdf.pages])
            name=self.detect(text)
            parser = next(p for p in self.PARSERS if p.NAME==name)
            return parser.parse(pdf_bytes)
        except Exception as e:
            return ParseResult(
                statements={"error": str(e)},
                transactions=[],
                meta={"parser": "error", "error_type": type(e).__name__}
            )
