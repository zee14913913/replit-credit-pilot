"""
CTOS Consent Routes - Personal & Company Consent Management
个人和公司CTOS授权书管理路由

Phase 7: CTOS Consent Integration
"""
import os
import base64
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image

from auth.admin_auth_helper import require_admin_or_accountant
from db.database import log_audit


@require_admin_or_accountant
def ctos_personal():
    """个人CTOS Consent页面"""
    return render_template('ctos/ctos_personal.html', current_date=datetime.now().strftime('%Y-%m-%d'))


@require_admin_or_accountant  
def ctos_personal_submit():
    """处理个人CTOS Consent提交"""
    try:
        # 获取表单数据
        full_name = request.form.get('full_name')
        ic_number = request.form.get('ic_number')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        signature_data = request.form.get('signature_data')
        
        # 获取IC文件
        ic_front = request.files.get('ic_front')
        ic_back = request.files.get('ic_back')
        
        if not all([full_name, ic_number, phone, email, address, signature_data]):
            flash('All fields are required', 'error')
            return redirect(url_for('ctos_personal'))
        
        # 创建客户目录
        safe_ic = ic_number.replace('-', '')
        customer_dir = f"static/uploads/ctos/personal/{safe_ic}"
        os.makedirs(customer_dir, exist_ok=True)
        
        # 保存IC文件
        if ic_front:
            ic_front.save(f"{customer_dir}/IC_FRONT.{ic_front.filename.split('.')[-1]}")
        if ic_back:
            ic_back.save(f"{customer_dir}/IC_BACK.{ic_back.filename.split('.')[-1]}")
        
        # 保存签名图片
        signature_image_data = signature_data.split(',')[1]
        signature_bytes = base64.b64decode(signature_image_data)
        signature_path = f"{customer_dir}/signature.png"
        with open(signature_path, 'wb') as f:
            f.write(signature_bytes)
        
        # 生成PDF
        pdf_filename = f"CTOS_CONSENT_{safe_ic}.pdf"
        pdf_path = f"{customer_dir}/{pdf_filename}"
        generate_ctos_personal_pdf(
            pdf_path, 
            full_name, 
            ic_number, 
            phone, 
            email, 
            address,
            signature_path
        )
        
        # Flash成功消息并重定向，让用户看到确认
        flash(f'✅ Personal CTOS Consent submitted successfully! PDF generated: {pdf_filename}', 'success')
        flash(f'📄 Download your consent PDF: <a href="/{pdf_path}" class="text-decoration-underline">Click Here</a>', 'info')
        return redirect(url_for('ctos_personal'))
        
    except Exception as e:
        flash(f'Error processing CTOS consent: {str(e)}', 'error')
        return redirect(url_for('ctos_personal'))


def generate_ctos_personal_pdf(pdf_path, name, ic, phone, email, address, signature_path):
    """生成个人CTOS Consent PDF"""
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # 标题
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 80, "CTOS PERSONAL CONSENT")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 100, "Credit Report Authorization")
    
    # 公司信息
    y = height - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Authorized By:")
    c.setFont("Helvetica", 11)
    c.drawString(150, y, "INFINITE GZ SDN BHD")
    
    # 个人信息
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "APPLICANT INFORMATION")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Full Name: {name}")
    y -= 20
    c.drawString(50, y, f"IC Number: {ic}")
    y -= 20
    c.drawString(50, y, f"Phone: {phone}")
    y -= 20
    c.drawString(50, y, f"Email: {email}")
    y -= 20
    c.drawString(50, y, f"Address: {address}")
    
    # Consent声明
    y -= 40
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "CONSENT STATEMENT")
    
    y -= 25
    c.setFont("Helvetica", 9)
    consent_text = [
        "I hereby authorize INFINITE GZ SDN BHD to obtain my personal credit report from",
        "CTOS Data Systems Sdn Bhd (CTOS) for the purpose of credit assessment, loan",
        "application processing, and financial risk evaluation.",
        "",
        "I understand that the credit report will contain my credit history, payment records,",
        "and outstanding commitments, and this information will be used strictly for the",
        "stated purposes in accordance with PDPA 2010.",
    ]
    
    for line in consent_text:
        c.drawString(50, y, line)
        y -= 15
    
    # 签名
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Signature:")
    
    # 插入签名图片
    try:
        img = ImageReader(signature_path)
        c.drawImage(img, 50, y - 60, width=150, height=50, preserveAspectRatio=True, mask='auto')
    except:
        pass
    
    y -= 80
    c.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    # 页脚
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 30, "This consent is valid for 12 months from the date of signature")
    c.drawCentredString(width/2, 20, "INFINITE GZ SDN BHD | Loan Advisory Services")
    
    c.save()


@require_admin_or_accountant
def ctos_company():
    """公司CTOS Consent页面"""
    return render_template('ctos/ctos_company.html', current_date=datetime.now().strftime('%Y-%m-%d'))


@require_admin_or_accountant
def ctos_company_submit():
    """处理公司CTOS Consent提交"""
    try:
        # 获取表单数据
        company_name = request.form.get('company_name')
        ssm_number = request.form.get('ssm_number')
        company_address = request.form.get('company_address')
        authorized_person = request.form.get('authorized_person')
        authorized_phone = request.form.get('authorized_phone')
        
        # 获取文件
        ssm_front = request.files.get('ssm_front')
        ssm_back = request.files.get('ssm_back')
        company_stamp = request.files.get('company_stamp')
        
        if not all([company_name, ssm_number, company_address, authorized_person, authorized_phone]):
            flash('All fields are required', 'error')
            return redirect(url_for('ctos_company'))
        
        # 创建公司目录
        safe_ssm = ssm_number.replace('-', '').replace('/', '_')
        company_dir = f"static/uploads/ctos/company/{safe_ssm}"
        os.makedirs(company_dir, exist_ok=True)
        
        # 保存文件
        if ssm_front:
            ssm_front.save(f"{company_dir}/SSM_FRONT.{ssm_front.filename.split('.')[-1]}")
        if ssm_back:
            ssm_back.save(f"{company_dir}/SSM_BACK.{ssm_back.filename.split('.')[-1]}")
        if company_stamp:
            stamp_path = f"{company_dir}/STAMP.{company_stamp.filename.split('.')[-1]}"
            company_stamp.save(stamp_path)
        else:
            stamp_path = None
        
        # 生成PDF
        pdf_filename = f"CTOS_SME_CONSENT_{safe_ssm}.pdf"
        pdf_path = f"{company_dir}/{pdf_filename}"
        generate_ctos_company_pdf(
            pdf_path,
            company_name,
            ssm_number,
            company_address,
            authorized_person,
            authorized_phone,
            stamp_path
        )
        
        # Flash成功消息并重定向，让用户看到确认
        flash(f'✅ Company CTOS Consent submitted successfully! PDF generated: {pdf_filename}', 'success')
        flash(f'📄 Download your consent PDF: <a href="/{pdf_path}" class="text-decoration-underline">Click Here</a>', 'info')
        return redirect(url_for('ctos_company'))
        
    except Exception as e:
        flash(f'Error processing company CTOS consent: {str(e)}', 'error')
        return redirect(url_for('ctos_company'))


def generate_ctos_company_pdf(pdf_path, company_name, ssm, address, auth_person, auth_phone, stamp_path):
    """生成公司CTOS Consent PDF"""
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # 标题
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 80, "CTOS COMPANY CONSENT")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 100, "SME Credit Report Authorization")
    
    # 公司信息
    y = height - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "COMPANY INFORMATION")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Company Name: {company_name}")
    y -= 20
    c.drawString(50, y, f"SSM Number: {ssm}")
    y -= 20
    c.drawString(50, y, f"Address: {address}")
    
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "AUTHORIZED REPRESENTATIVE")
    
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Name: {auth_person}")
    y -= 20
    c.drawString(50, y, f"Phone: {auth_phone}")
    
    # Consent声明
    y -= 40
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "CONSENT STATEMENT")
    
    y -= 25
    c.setFont("Helvetica", 9)
    consent_text = [
        "The company hereby authorizes INFINITE GZ SDN BHD to obtain the company's",
        "credit report from CTOS Data Systems Sdn Bhd (CTOS) for the purpose of SME",
        "loan assessment, business financing evaluation, and risk analysis.",
        "",
        "The authorized representative confirms having the authority to provide this",
        "consent on behalf of the company.",
    ]
    
    for line in consent_text:
        c.drawString(50, y, line)
        y -= 15
    
    # 公司盖章区域
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Company Stamp:")
    
    # 插入盖章图片（如果有）
    if stamp_path and os.path.exists(stamp_path):
        try:
            img = ImageReader(stamp_path)
            c.drawImage(img, 50, y - 80, width=100, height=80, preserveAspectRatio=True, mask='auto')
        except:
            pass
    
    y -= 100
    c.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    # 页脚
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 30, "This consent is valid for 12 months from the date of authorization")
    c.drawCentredString(width/2, 20, "INFINITE GZ SDN BHD | SME Financing Services")
    
    c.save()
