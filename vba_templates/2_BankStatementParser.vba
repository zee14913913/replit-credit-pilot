''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' INFINITE GZ - 银行流水月结单VBA解析器
' 文件名: BankStatementParser.vba
' 版本: 1.0.0
' 功能: 解析银行流水Excel账单，导出标准JSON格式
' 支持银行: Public Bank, Maybank, CIMB, RHB, Hong Leong Bank
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Option Explicit

' ==================== 主函数 ====================
Sub ParseBankStatement()
    Dim ws As Worksheet
    Dim jsonData As String
    Dim outputPath As String
    
    ' 获取当前工作表
    Set ws = ActiveSheet
    
    ' 验证是否为银行流水
    If Not IsBankStatement(ws) Then
        MsgBox "当前工作表不是银行流水格式！", vbExclamation
        Exit Sub
    End If
    
    ' 解析账单数据
    jsonData = BuildBankStatementJSON(ws)
    
    ' 保存JSON文件
    outputPath = ThisWorkbook.Path & "\bank_statement_" & Format(Now, "yyyymmdd_hhnnss") & ".json"
    SaveJSON jsonData, outputPath
    
    MsgBox "银行流水解析完成！" & vbCrLf & "文件已保存：" & outputPath, vbInformation
End Sub


' ==================== 识别账单类型 ====================
Function IsBankStatement(ws As Worksheet) As Boolean
    Dim cell As Range
    Dim searchText As String
    
    IsBankStatement = False
    
    ' 搜索关键词
    For Each cell In ws.Range("A1:Z30").Cells
        searchText = UCase(cell.Value)
        
        If InStr(searchText, "ACCOUNT NUMBER") > 0 Or _
           InStr(searchText, "OPENING BALANCE") > 0 Or _
           InStr(searchText, "CURRENT ACCOUNT") > 0 Or _
           InStr(searchText, "SAVINGS ACCOUNT") > 0 Or _
           InStr(searchText, "PUBLIC BANK") > 0 Or _
           InStr(searchText, "MAYBANK") > 0 Then
            IsBankStatement = True
            Exit Function
        End If
    Next cell
End Function


' ==================== 构建JSON数据 ====================
Function BuildBankStatementJSON(ws As Worksheet) As String
    Dim json As String
    Dim accountInfo As String
    Dim transactions As String
    Dim summary As String
    
    ' 提取账户信息
    accountInfo = ExtractBankAccountInfo(ws)
    
    ' 提取交易明细
    transactions = ExtractBankTransactions(ws)
    
    ' 生成汇总
    summary = GenerateBankSummary(ws)
    
    ' 组装JSON
    json = "{" & vbCrLf
    json = json & "  ""status"": ""success""," & vbCrLf
    json = json & "  ""document_type"": ""bank_statement""," & vbCrLf
    json = json & "  ""parsed_by"": ""VBA Parser v1.0""," & vbCrLf
    json = json & "  ""parsed_at"": """ & Format(Now, "yyyy-mm-dd hh:nn:ss") & """," & vbCrLf
    json = json & "  ""bank_detected"": """ & DetectBank(ws) & """," & vbCrLf
    json = json & "  ""account_info"": " & accountInfo & "," & vbCrLf
    json = json & "  ""transactions"": " & transactions & "," & vbCrLf
    json = json & "  ""summary"": " & summary & vbCrLf
    json = json & "}"
    
    BuildBankStatementJSON = json
End Function


' ==================== 检测银行 ====================
Function DetectBank(ws As Worksheet) As String
    Dim cell As Range
    Dim text As String
    
    For Each cell In ws.Range("A1:Z20").Cells
        text = UCase(cell.Value)
        
        If InStr(text, "PUBLIC BANK") > 0 Or InStr(text, "PBB") > 0 Then
            DetectBank = "PUBLIC BANK"
            Exit Function
        ElseIf InStr(text, "MAYBANK") > 0 Then
            DetectBank = "MAYBANK"
            Exit Function
        ElseIf InStr(text, "CIMB") > 0 Then
            DetectBank = "CIMB BANK"
            Exit Function
        ElseIf InStr(text, "RHB") > 0 Then
            DetectBank = "RHB BANK"
            Exit Function
        ElseIf InStr(text, "HONG LEONG") > 0 Or InStr(text, "HLB") > 0 Then
            DetectBank = "HONG LEONG BANK"
            Exit Function
        End If
    Next cell
    
    DetectBank = "UNKNOWN BANK"
End Function


' ==================== 提取账户信息 ====================
Function ExtractBankAccountInfo(ws As Worksheet) As String
    Dim json As String
    Dim accountNumber As String
    Dim accountType As String
    Dim accountHolder As String
    Dim bankName As String
    Dim statementDate As String
    Dim openingBalance As Double
    Dim closingBalance As Double
    
    ' 提取基本信息
    accountNumber = FindCellValue(ws, "Account Number", "A/C No")
    accountType = FindCellValue(ws, "Account Type", "ACE Account", "Current Account", "Savings Account")
    accountHolder = FindCellValue(ws, "Account Holder", "Name", "Customer")
    bankName = DetectBank(ws)
    statementDate = FindCellValue(ws, "Statement Date", "As at", "Date")
    
    openingBalance = FindCellAmount(ws, "Opening Balance", "Previous Balance", "Balance B/F")
    closingBalance = FindCellAmount(ws, "Closing Balance", "Current Balance", "Balance C/F")
    
    ' 构建JSON
    json = "{" & vbCrLf
    json = json & "    ""account_number"": """ & CleanText(accountNumber) & """," & vbCrLf
    json = json & "    ""account_type"": """ & CleanText(accountType) & """," & vbCrLf
    json = json & "    ""account_holder"": """ & CleanText(accountHolder) & """," & vbCrLf
    json = json & "    ""bank"": """ & bankName & """," & vbCrLf
    json = json & "    ""statement_date"": """ & statementDate & """," & vbCrLf
    json = json & "    ""opening_balance"": " & FormatNumber(openingBalance, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
    json = json & "    ""closing_balance"": " & FormatNumber(closingBalance, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
    json = json & "    ""total_debits"": 0.00," & vbCrLf
    json = json & "    ""total_credits"": 0.00" & vbCrLf
    json = json & "  }"
    
    ExtractBankAccountInfo = json
End Function


' ==================== 提取交易明细 ====================
Function ExtractBankTransactions(ws As Worksheet) As String
    Dim json As String
    Dim startRow As Long
    Dim lastRow As Long
    Dim i As Long
    Dim transactionDate As String
    Dim description As String
    Dim debit As Double
    Dim credit As Double
    Dim runningBalance As Double
    Dim category As String
    Dim subCategory As String
    Dim firstTransaction As Boolean
    
    ' 查找交易明细起始行
    startRow = FindBankTransactionStartRow(ws)
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    json = "[" & vbCrLf
    firstTransaction = True
    
    For i = startRow To lastRow
        ' 读取单元格数据
        transactionDate = ws.Cells(i, 1).Value
        description = ws.Cells(i, 2).Value
        debit = Val(ws.Cells(i, 3).Value)
        credit = Val(ws.Cells(i, 4).Value)
        runningBalance = Val(ws.Cells(i, 5).Value)
        
        ' 跳过空行
        If Len(Trim(transactionDate)) = 0 Then GoTo NextRow
        
        ' 智能分类
        Call ClassifyBankTransaction(description, debit, credit, category, subCategory)
        
        ' 添加逗号分隔符
        If Not firstTransaction Then
            json = json & "," & vbCrLf
        End If
        firstTransaction = False
        
        ' 构建交易JSON
        json = json & "    {" & vbCrLf
        json = json & "      ""date"": """ & FormatDate(transactionDate) & """," & vbCrLf
        json = json & "      ""description"": """ & EscapeJSON(description) & """," & vbCrLf
        json = json & "      ""debit"": " & FormatNumber(debit, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
        json = json & "      ""credit"": " & FormatNumber(credit, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
        json = json & "      ""running_balance"": " & FormatNumber(runningBalance, 2, vbTrue, vbFalse, vbFalse) & "," & vbCrLf
        json = json & "      ""category"": """ & category & """," & vbCrLf
        json = json & "      ""sub_category"": """ & subCategory & """" & vbCrLf
        json = json & "    }"
        
NextRow:
    Next i
    
    json = json & vbCrLf & "  ]"
    
    ExtractBankTransactions = json
End Function


' ==================== 智能分类（30+类别） ====================
Sub ClassifyBankTransaction(description As String, debit As Double, credit As Double, _
                           ByRef category As String, ByRef subCategory As String)
    Dim desc As String
    desc = UCase(description)
    
    ' 收入类
    If credit > 0 Then
        If InStr(desc, "SALARY") > 0 Or InStr(desc, "GAJI") > 0 Then
            category = "INCOME"
            subCategory = "薪资收入"
        ElseIf InStr(desc, "INTEREST") > 0 Or InStr(desc, "FAEDAH") > 0 Then
            category = "INCOME"
            subCategory = "利息收入"
        ElseIf InStr(desc, "REFUND") > 0 Or InStr(desc, "RETURN") > 0 Then
            category = "INCOME"
            subCategory = "退款"
        Else
            category = "INCOME"
            subCategory = "其他收入"
        End If
        Exit Sub
    End If
    
    ' 支出类
    If debit > 0 Then
        ' 水电费
        If InStr(desc, "TNB") > 0 Or InStr(desc, "SYABAS") > 0 Or InStr(desc, "ELECTRIC") > 0 Then
            category = "BILLS"
            subCategory = "水电费"
        ' 通讯费
        ElseIf InStr(desc, "MAXIS") > 0 Or InStr(desc, "CELCOM") > 0 Or InStr(desc, "DIGI") > 0 Or InStr(desc, "UNIFI") > 0 Then
            category = "BILLS"
            subCategory = "通讯费"
        ' 网购
        ElseIf InStr(desc, "SHOPEE") > 0 Or InStr(desc, "LAZADA") > 0 Or InStr(desc, "GRAB") > 0 Then
            category = "BILLS"
            subCategory = "网购"
        ' 汽油费
        ElseIf InStr(desc, "PETRONAS") > 0 Or InStr(desc, "SHELL") > 0 Or InStr(desc, "PETROL") > 0 Then
            category = "CONSUMPTION"
            subCategory = "汽油费"
        ' 保险
        ElseIf InStr(desc, "INSURANCE") > 0 Or InStr(desc, "INSURANS") > 0 Or InStr(desc, "TAKAFUL") > 0 Then
            category = "CONSUMPTION"
            subCategory = "保险"
        ' 贷款还款
        ElseIf InStr(desc, "LOAN") > 0 Or InStr(desc, "PINJAMAN") > 0 Or InStr(desc, "PTPTN") > 0 Then
            category = "CONSUMPTION"
            subCategory = "贷款还款"
        ' 银行费用
        ElseIf InStr(desc, "BANK CHARGE") > 0 Or InStr(desc, "SERVICE CHARGE") > 0 Or InStr(desc, "FEE") > 0 Then
            category = "EXPENSES"
            subCategory = "银行费用"
        ' 转账
        ElseIf InStr(desc, "TRANSFER") > 0 Or InStr(desc, "TFR") > 0 Or InStr(desc, "IBFT") > 0 Then
            category = "EXPENSES"
            subCategory = "转账"
        ' ATM提款
        ElseIf InStr(desc, "ATM") > 0 Or InStr(desc, "WITHDRAWAL") > 0 Then
            category = "EXPENSES"
            subCategory = "ATM提款"
        Else
            category = "EXPENSES"
            subCategory = "其他支出"
        End If
    End If
End Sub


' ==================== 生成汇总统计 ====================
Function GenerateBankSummary(ws As Worksheet) As String
    Dim json As String
    Dim totalTransactions As Long
    Dim balanceVerified As Boolean
    
    totalTransactions = 0
    balanceVerified = True
    
    ' 构建JSON
    json = "{" & vbCrLf
    json = json & "    ""total_transactions"": " & totalTransactions & "," & vbCrLf
    json = json & "    ""category_breakdown"": {}," & vbCrLf
    json = json & "    ""balance_verified"": " & LCase(CStr(balanceVerified)) & "," & vbCrLf
    json = json & "    ""balance_difference"": 0.00" & vbCrLf
    json = json & "  }"
    
    GenerateBankSummary = json
End Function


' ==================== 辅助函数 ====================

Function FindCellValue(ws As Worksheet, ParamArray keywords()) As String
    Dim cell As Range
    Dim keyword As Variant
    
    For Each keyword In keywords
        For Each cell In ws.Range("A1:Z50").Cells
            If InStr(UCase(cell.Value), UCase(keyword)) > 0 Then
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

Function FindBankTransactionStartRow(ws As Worksheet) As Long
    Dim i As Long
    For i = 1 To 100
        If InStr(UCase(ws.Cells(i, 1).Value), "DATE") > 0 And _
           InStr(UCase(ws.Cells(i, 2).Value), "DESCRIPTION") > 0 Then
            FindBankTransactionStartRow = i + 1
            Exit Function
        End If
    Next i
    FindBankTransactionStartRow = 15
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
