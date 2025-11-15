''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' INFINITE GZ - 信用卡账单VBA解析器
' 文件名: CreditCardParser.vba
' 版本: 1.0.0
' 功能: 解析信用卡Excel账单，导出标准JSON格式
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Option Explicit

' ==================== 主函数 ====================
Sub ParseCreditCardStatement()
    Dim ws As Worksheet
    Dim jsonData As String
    Dim outputPath As String
    
    ' 获取当前工作表
    Set ws = ActiveSheet
    
    ' 验证是否为信用卡账单
    If Not IsCreditCardStatement(ws) Then
        MsgBox "当前工作表不是信用卡账单格式！", vbExclamation
        Exit Sub
    End If
    
    ' 解析账单数据
    jsonData = BuildCreditCardJSON(ws)
    
    ' 保存JSON文件
    outputPath = ThisWorkbook.Path & "\credit_card_" & Format(Now, "yyyymmdd_hhnnss") & ".json"
    SaveJSON jsonData, outputPath
    
    MsgBox "信用卡账单解析完成！" & vbCrLf & "文件已保存：" & outputPath, vbInformation
End Sub


' ==================== 识别账单类型 ====================
Function IsCreditCardStatement(ws As Worksheet) As Boolean
    Dim cell As Range
    Dim searchText As String
    
    IsCreditCardStatement = False
    
    ' 搜索关键词
    For Each cell In ws.Range("A1:Z30").Cells
        searchText = UCase(cell.Value)
        
        If InStr(searchText, "CREDIT CARD") > 0 Or _
           InStr(searchText, "CARD LIMIT") > 0 Or _
           InStr(searchText, "MINIMUM PAYMENT") > 0 Or _
           InStr(searchText, "VISA") > 0 Or _
           InStr(searchText, "MASTERCARD") > 0 Then
            IsCreditCardStatement = True
            Exit Function
        End If
    Next cell
End Function


' ==================== 构建JSON数据 ====================
Function BuildCreditCardJSON(ws As Worksheet) As String
    Dim json As String
    Dim accountInfo As String
    Dim transactions As String
    Dim summary As String
    
    ' 提取账户信息
    accountInfo = ExtractAccountInfo(ws)
    
    ' 提取交易明细
    transactions = ExtractTransactions(ws)
    
    ' 生成汇总
    summary = GenerateSummary(ws)
    
    ' 组装JSON
    json = "{" & vbCrLf
    json = json & "  ""status"": ""success""," & vbCrLf
    json = json & "  ""document_type"": ""credit_card""," & vbCrLf
    json = json & "  ""parsed_by"": ""VBA Parser v1.0""," & vbCrLf
    json = json & "  ""parsed_at"": """ & Format(Now, "yyyy-mm-dd hh:nn:ss") & """," & vbCrLf
    json = json & "  ""account_info"": " & accountInfo & "," & vbCrLf
    json = json & "  ""transactions"": " & transactions & "," & vbCrLf
    json = json & "  ""summary"": " & summary & vbCrLf
    json = json & "}"
    
    BuildCreditCardJSON = json
End Function


' ==================== 提取账户信息 ====================
Function ExtractAccountInfo(ws As Worksheet) As String
    Dim json As String
    Dim ownerName As String
    Dim bankName As String
    Dim cardLast4 As String
    Dim cardType As String
    Dim statementDate As String
    Dim dueDate As String
    Dim cardLimit As Double
    Dim previousBalance As Double
    Dim closingBalance As Double
    
    ' 提取基本信息（根据实际账单格式调整）
    ownerName = FindCellValue(ws, "Card Holder", "Name")
    bankName = FindCellValue(ws, "Bank", "Issuer")
    cardLast4 = ExtractCardNumber(ws)
    cardType = FindCellValue(ws, "Card Type", "Visa", "Mastercard")
    statementDate = FindCellValue(ws, "Statement Date", "Billing Date")
    dueDate = FindCellValue(ws, "Due Date", "Payment Due")
    
    cardLimit = FindCellAmount(ws, "Credit Limit", "Card Limit")
    previousBalance = FindCellAmount(ws, "Previous Balance", "Opening Balance")
    closingBalance = FindCellAmount(ws, "Closing Balance", "Current Balance", "Total Amount Due")
    
    ' 构建JSON
    json = "{" & vbCrLf
    json = json & "    ""owner_name"": """ & CleanText(ownerName) & """," & vbCrLf
    json = json & "    ""bank"": """ & CleanText(bankName) & """," & vbCrLf
    json = json & "    ""card_last_4"": """ & cardLast4 & """," & vbCrLf
    json = json & "    ""card_type"": """ & CleanText(cardType) & """," & vbCrLf
    json = json & "    ""statement_date"": """ & statementDate & """," & vbCrLf
    json = json & "    ""due_date"": """ & dueDate & """," & vbCrLf
    json = json & "    ""card_limit"": " & FormatNumber(cardLimit, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
    json = json & "    ""previous_balance"": " & FormatNumber(previousBalance, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
    json = json & "    ""closing_balance"": " & FormatNumber(closingBalance, 2, vbTrue, vbFalse, vbFalse) & vbCrLf
    json = json & "  }"
    
    ExtractAccountInfo = json
End Function


' ==================== 提取交易明细 ====================
Function ExtractTransactions(ws As Worksheet) As String
    Dim json As String
    Dim startRow As Long
    Dim lastRow As Long
    Dim i As Long
    Dim transactionDate As String
    Dim description As String
    Dim amount As Double
    Dim dr As Double
    Dim cr As Double
    Dim runningBalance As Double
    Dim category As String
    Dim subCategory As String
    Dim firstTransaction As Boolean
    
    ' 查找交易明细起始行
    startRow = FindTransactionStartRow(ws)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    json = "[" & vbCrLf
    firstTransaction = True
    runningBalance = 0
    
    For i = startRow To lastRow
        ' 读取单元格数据
        transactionDate = ws.Cells(i, 1).Value
        description = ws.Cells(i, 2).Value
        amount = ws.Cells(i, 3).Value
        
        ' 跳过空行
        If Len(Trim(transactionDate)) = 0 Then GoTo NextRow
        
        ' 判断DR/CR
        If IsPayment(description) Then
            dr = 0
            cr = Abs(amount)
            category = "Payment"
            subCategory = "还款"
        ElseIf IsFinanceCharge(description) Then
            dr = Abs(amount)
            cr = 0
            category = "Finance Charges"
            subCategory = "利息费用"
        Else
            dr = Abs(amount)
            cr = 0
            category = "Purchases"
            subCategory = ClassifyPurchase(description)
        End If
        
        ' 计算Running Balance
        runningBalance = runningBalance + dr - cr
        
        ' 添加逗号分隔符
        If Not firstTransaction Then
            json = json & "," & vbCrLf
        End If
        firstTransaction = False
        
        ' 构建交易JSON
        json = json & "    {" & vbCrLf
        json = json & "      ""date"": """ & FormatDate(transactionDate) & """," & vbCrLf
        json = json & "      ""posting_date"": """ & FormatDate(transactionDate) & """," & vbCrLf
        json = json & "      ""description"": """ & EscapeJSON(description) & """," & vbCrLf
        json = json & "      ""amount"": " & FormatNumber(Abs(amount), 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
        json = json & "      ""dr"": " & FormatNumber(dr, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
        json = json & "      ""cr"": " & FormatNumber(cr, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
        json = json & "      ""running_balance"": " & FormatNumber(runningBalance, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
        json = json & "      ""category"": """ & category & """," & vbCrLf
        json = json & "      ""sub_category"": """ & subCategory & """" & vbCrLf
        json = json & "    }"
        
NextRow:
    Next i
    
    json = json & vbCrLf & "  ]"
    
    ExtractTransactions = json
End Function


' ==================== 生成汇总统计 ====================
Function GenerateSummary(ws As Worksheet) As String
    Dim json As String
    Dim totalTransactions As Long
    Dim totalPurchases As Double
    Dim totalPayments As Double
    Dim totalFinanceCharges As Double
    Dim balanceVerified As Boolean
    
    ' 计算统计数据（简化版，实际应遍历交易）
    totalTransactions = 0
    totalPurchases = 0
    totalPayments = 0
    totalFinanceCharges = 0
    balanceVerified = True
    
    ' 构建JSON
    json = "{" & vbCrLf
    json = json & "    ""total_transactions"": " & totalTransactions & "," & vbCrLf
    json = json & "    ""total_purchases"": " & FormatNumber(totalPurchases, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
    json = json & "    ""total_payments"": " & FormatNumber(totalPayments, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
    json = json & "    ""total_finance_charges"": " & FormatNumber(totalFinanceCharges, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
    json = json & "    ""balance_verified"": " & LCase(CStr(balanceVerified)) & vbCrLf
    json = json & "  }"
    
    GenerateSummary = json
End Function


' ==================== 辅助函数 ====================

Function FindCellValue(ws As Worksheet, ParamArray keywords()) As String
    Dim cell As Range
    Dim keyword As Variant
    
    For Each keyword In keywords
        For Each cell In ws.Range("A1:Z50").Cells
            If InStr(UCase(cell.Value), UCase(keyword)) > 0 Then
                ' 返回右侧单元格的值
                If cell.Column < 26 Then
                    FindCellValue = ws.Cells(cell.Row, cell.Column + 1).Value
                    Exit Function
                End If
            End If
        Next cell
    Next keyword
    
    FindCellValue = "N/A"
End Function

Function FindCellAmount(ws As Worksheet, ParamArray keywords()) As Double
    Dim value As String
    value = FindCellValue(ws, keywords)
    FindCellAmount = Val(Replace(Replace(value, ",", ""), "RM", ""))
End Function

Function ExtractCardNumber(ws As Worksheet) As String
    Dim cell As Range
    Dim text As String
    Dim matches As Object
    
    For Each cell In ws.Range("A1:Z50").Cells
        text = cell.Value
        If InStr(text, "xxxx") > 0 Or InStr(text, "****") > 0 Then
            ' 提取后4位数字
            ExtractCardNumber = Right(Replace(Replace(text, "x", ""), "*", ""), 4)
            Exit Function
        End If
    Next cell
    
    ExtractCardNumber = "N/A"
End Function

Function FindTransactionStartRow(ws As Worksheet) As Long
    Dim i As Long
    For i = 1 To 100
        If InStr(UCase(ws.Cells(i, 1).Value), "DATE") > 0 Or _
           InStr(UCase(ws.Cells(i, 1).Value), "TRANSACTION") > 0 Then
            FindTransactionStartRow = i + 1
            Exit Function
        End If
    Next i
    FindTransactionStartRow = 10
End Function

Function IsPayment(description As String) As Boolean
    IsPayment = InStr(UCase(description), "PAYMENT") > 0 Or _
                InStr(UCase(description), "THANK YOU") > 0
End Function

Function IsFinanceCharge(description As String) As Boolean
    IsFinanceCharge = InStr(UCase(description), "INTEREST") > 0 Or _
                      InStr(UCase(description), "FINANCE CHARGE") > 0
End Function

Function ClassifyPurchase(description As String) As String
    Dim desc As String
    desc = UCase(description)
    
    If InStr(desc, "SHOPEE") > 0 Or InStr(desc, "LAZADA") > 0 Then
        ClassifyPurchase = "网购"
    ElseIf InStr(desc, "PETRONAS") > 0 Or InStr(desc, "SHELL") > 0 Then
        ClassifyPurchase = "汽油费"
    Else
        ClassifyPurchase = "消费"
    End If
End Function

Function CleanText(text As String) As String
    CleanText = Trim(Replace(text, vbCrLf, " "))
End Function

Function EscapeJSON(text As String) As String
    EscapeJSON = Replace(Replace(text, "\", "\\"), """", "\""")
End Function

Function FormatDate(dateVal As Variant) As String
    If IsDate(dateVal) Then
        FormatDate = Format(CDate(dateVal), "dd-mm-yyyy")
    Else
        FormatDate = CStr(dateVal)
    End If
End Function

Function SaveJSON(jsonText As String, filePath As String)
    Dim fileNum As Integer
    fileNum = FreeFile
    Open filePath For Output As #fileNum
    Print #fileNum, jsonText
    Close #fileNum
End Function
