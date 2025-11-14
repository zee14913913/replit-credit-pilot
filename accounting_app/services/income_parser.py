import re
from typing import Dict

class IncomeParser:

    @staticmethod
    def parse_income_from_text(text: str) -> Dict:
        """
        提取工资单 / 税单 / EPF / 银行流水中的收入数据。
        返回统一结构。
        """

        clean = text.replace(",", "").lower()

        results = {
            "basic_salary": 0.0,
            "allowance": 0.0,
            "epf_contribution": 0.0,
            "net_salary": 0.0,
            "gross_salary": 0.0,
            "annual_income": 0.0,
            "bank_inflow": 0.0
        }

        m = re.search(r"basic salary[:\s]+(\d+\.?\d*)", clean)
        if m:
            results["basic_salary"] = float(m.group(1))

        m = re.search(r"allowance[:\s]+(\d+\.?\d*)", clean)
        if m:
            results["allowance"] = float(m.group(1))

        m = re.search(r"epf (?:employee|contribution)[:\s]+(\d+\.?\d*)", clean)
        if m:
            results["epf_contribution"] = float(m.group(1))

        m = re.search(r"net salary[:\s]+(\d+\.?\d*)", clean)
        if m:
            results["net_salary"] = float(m.group(1))

        m = re.search(r"gross salary[:\s]+(\d+\.?\d*)", clean)
        if m:
            results["gross_salary"] = float(m.group(1))

        m = re.search(r"annual income[:\s]+(\d+\.?\d*)", clean)
        if m:
            results["annual_income"] = float(m.group(1))

        m = re.search(r"total inflow[:\s]+(\d+\.?\d*)", clean)
        if m:
            results["bank_inflow"] = float(m.group(1))

        return results
