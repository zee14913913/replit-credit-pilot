''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' INFINITE GZ - 数据验证器
' 文件名: 4_DataValidator.vba
' 版本: 1.0.0
' 功能: 验证账单数据的准确性和完整性
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Option Explicit

'==============================================================================
' 余额验证
'==============================================================================

Function ValidateBalance(ws As Worksheet, docType As String) As Boolean
    '验证账单余额是否一致
    '返回 True = 验证通过, False = 验证失败
    
    Dim openingBalance As Double
    Dim closingBalance As Double
    Dim calculatedClosing As Double
    Dim difference As Double
    Dim tolerance As Double
    
    tolerance = 0.01 ' 容差±0.01
    
    If docType = "credit_card" Then
        ' 信用卡余额验证
        openingBalance = FindCellAmount(ws, "Previous Balance", "Opening Balance")
        closingBalance = FindCellAmount(ws, "Closing Balance", "Current Balance", "Total Amount Due")
        
        Dim totalPurchases As Double
        Dim totalPayments As Double
        Dim totalCharges As Double
        
        totalPurchases = CalculateTotalPurchases(ws)
        totalPayments = CalculateTotalPayments(ws)
        totalCharges = CalculateTotalFinanceCharges(ws)
        
        calculatedClosing = openingBalance + totalPurchases - totalPayments + totalCharges
        
    ElseIf docType = "bank_statement" Then
        ' 银行流水余额验证
        openingBalance = FindCellAmount(ws, "Opening Balance", "Balance B/F")
        closingBalance = FindCellAmount(ws, "Closing Balance", "Current Balance", "Balance C/F")
        
        Dim totalDebits As Double
        Dim totalCredits As Double
        
        Call CalculateTotalDebitsCredits(ws, totalDebits, totalCredits)
        
        calculatedClosing = openingBalance + totalCredits - totalDebits
    End If
    
    difference = Abs(calculatedClosing - closingBalance)
    
    If difference <= tolerance Then
        ValidateBalance = True
        Debug.Print "✓ 余额验证通过"
        Debug.Print "  期初余额: RM " & Format(openingBalance, "#,##0.00")
        Debug.Print "  期末余额: RM " & Format(closingBalance, "#,##0.00")
        Debug.Print "  计算余额: RM " & Format(calculatedClosing, "#,##0.00")
        Debug.Print "  差异: RM " & Format(difference, "#,##0.00")
    Else
        ValidateBalance = False
        Debug.Print "✗ 余额验证失败！"
        Debug.Print "  期初余额: RM " & Format(openingBalance, "#,##0.00")
        Debug.Print "  期末余额: RM " & Format(closingBalance, "#,##0.00")
        Debug.Print "  计算余额: RM " & Format(calculatedClosing, "#,##0.00")
        Debug.Print "  差异: RM " & Format(difference, "#,##0.00")
        Debug.Print "  ⚠ 建议人工检查账单数据！"
    End If
End Function


'==============================================================================
' 数据完整性检查
'==============================================================================

Function ValidateDataCompleteness(ws As Worksheet) As Boolean
    '检查账单数据的完整性
    
    Dim issues As Collection
    Set issues = New Collection
    
    Dim startRow As Long
    Dim lastRow As Long
    Dim i As Long
    Dim transactionDate As String
    Dim description As String
    Dim amount As Variant
    
    startRow = FindTransactionStartRow(ws)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    For i = startRow To lastRow
        transactionDate = Trim(ws.Cells(i, 1).Value)
        description = Trim(ws.Cells(i, 2).Value)
        amount = ws.Cells(i, 3).Value
        
        ' 跳过空行
        If Len(transactionDate) = 0 Then GoTo NextCheck
        
        ' 检查日期
        If Not IsDate(transactionDate) Then
            issues.Add "行 " & i & ": 日期格式无效 (" & transactionDate & ")"
        End If
        
        ' 检查描述
        If Len(description) = 0 Then
            issues.Add "行 " & i & ": 交易描述为空"
        End If
        
        ' 检查金额
        If Not IsNumeric(amount) Then
            issues.Add "行 " & i & ": 金额格式无效 (" & amount & ")"
        End If
        
NextCheck:
    Next i
    
    ' 输出检查结果
    If issues.Count = 0 Then
        ValidateDataCompleteness = True
        Debug.Print "✓ 数据完整性检查通过"
    Else
        ValidateDataCompleteness = False
        Debug.Print "✗ 发现 " & issues.Count & " 个数据问题:"
        
        Dim issue As Variant
        For Each issue In issues
            Debug.Print "  " & issue
        Next issue
    End If
End Function


'==============================================================================
' 辅助计算函数
'==============================================================================

Function CalculateTotalPurchases(ws As Worksheet) As Double
    '计算信用卡总消费
    Dim startRow As Long
    Dim lastRow As Long
    Dim i As Long
    Dim description As String
    Dim amount As Double
    Dim total As Double
    
    startRow = FindTransactionStartRow(ws)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    total = 0
    
    For i = startRow To lastRow
        description = UCase(ws.Cells(i, 2).Value)
        amount = Val(ws.Cells(i, 3).Value)
        
        If Len(Trim(description)) = 0 Then GoTo NextRow
        
        ' 排除还款和利息
        If InStr(description, "PAYMENT") = 0 And _
           InStr(description, "INTEREST") = 0 And _
           InStr(description, "FINANCE CHARGE") = 0 Then
            total = total + Abs(amount)
        End If
        
NextRow:
    Next i
    
    CalculateTotalPurchases = total
End Function


Function CalculateTotalPayments(ws As Worksheet) As Double
    '计算信用卡总还款
    Dim startRow As Long
    Dim lastRow As Long
    Dim i As Long
    Dim description As String
    Dim amount As Double
    Dim total As Double
    
    startRow = FindTransactionStartRow(ws)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    total = 0
    
    For i = startRow To lastRow
        description = UCase(ws.Cells(i, 2).Value)
        amount = Val(ws.Cells(i, 3).Value)
        
        If InStr(description, "PAYMENT") > 0 Or _
           InStr(description, "THANK YOU") > 0 Then
            total = total + Abs(amount)
        End If
    Next i
    
    CalculateTotalPayments = total
End Function


Function CalculateTotalFinanceCharges(ws As Worksheet) As Double
    '计算总利息费用
    Dim startRow As Long
    Dim lastRow As Long
    Dim i As Long
    Dim description As String
    Dim amount As Double
    Dim total As Double
    
    startRow = FindTransactionStartRow(ws)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    total = 0
    
    For i = startRow To lastRow
        description = UCase(ws.Cells(i, 2).Value)
        amount = Val(ws.Cells(i, 3).Value)
        
        If InStr(description, "INTEREST") > 0 Or _
           InStr(description, "FINANCE CHARGE") > 0 Then
            total = total + Abs(amount)
        End If
    Next i
    
    CalculateTotalFinanceCharges = total
End Function


Sub CalculateTotalDebitsCredits(ws As Worksheet, ByRef totalDebit As Double, ByRef totalCredit As Double)
    '计算银行流水总借贷
    Dim startRow As Long
    Dim lastRow As Long
    Dim i As Long
    Dim debit As Double
    Dim credit As Double
    
    startRow = FindBankTransactionStartRow(ws)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    totalDebit = 0
    totalCredit = 0
    
    For i = startRow To lastRow
        debit = Val(ws.Cells(i, 3).Value)
        credit = Val(ws.Cells(i, 4).Value)
        
        totalDebit = totalDebit + debit
        totalCredit = totalCredit + credit
    Next i
End Sub


'==============================================================================
' 综合验证报告
'==============================================================================

Sub GenerateValidationReport()
    '生成完整的数据验证报告
    
    Dim ws As Worksheet
    Dim docType As String
    Dim balanceValid As Boolean
    Dim dataComplete As Boolean
    Dim qualityScore As Double
    
    Set ws = ActiveSheet
    
    Debug.Print String(80, "=")
    Debug.Print "数据验证报告"
    Debug.Print String(80, "=")
    Debug.Print ""
    
    ' 判断账单类型
    If IsCreditCardStatement(ws) Then
        docType = "credit_card"
        Debug.Print "账单类型: 信用卡账单"
    ElseIf IsBankStatement(ws) Then
        docType = "bank_statement"
        Debug.Print "账单类型: 银行流水"
    Else
        Debug.Print "✗ 无法识别账单类型"
        Exit Sub
    End If
    
    Debug.Print ""
    
    ' 验证余额
    Debug.Print "【余额验证】"
    balanceValid = ValidateBalance(ws, docType)
    Debug.Print ""
    
    ' 验证数据完整性
    Debug.Print "【数据完整性】"
    dataComplete = ValidateDataCompleteness(ws)
    Debug.Print ""
    
    ' 质量评分
    If balanceValid And dataComplete Then
        qualityScore = 100
    ElseIf balanceValid Or dataComplete Then
        qualityScore = 70
    Else
        qualityScore = 40
    End If
    
    Debug.Print "【综合评分】"
    Debug.Print "  质量评分: " & qualityScore & "%"
    
    If qualityScore >= 90 Then
        Debug.Print "  ✓ 数据质量优秀，可直接上传"
    ElseIf qualityScore >= 70 Then
        Debug.Print "  ⚠ 数据质量良好，建议检查后上传"
    Else
        Debug.Print "  ✗ 数据质量较差，需要人工检查"
    End If
    
    Debug.Print ""
    Debug.Print String(80, "=")
End Sub


'==============================================================================
' 辅助函数（复用主解析器中的函数）
'==============================================================================

' 这些函数应该从主解析器中引用:
' - IsCreditCardStatement()
' - IsBankStatement()
' - FindTransactionStartRow()
' - FindBankTransactionStartRow()
' - FindCellAmount()
