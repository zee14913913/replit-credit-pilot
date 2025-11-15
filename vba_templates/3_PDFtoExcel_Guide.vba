''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' INFINITE GZ - PDF转Excel工具指南
' 文件名: 3_PDFtoExcel_Guide.vba
' 版本: 1.0.0
' 说明: PDF账单转Excel的推荐方案和VBA代码示例
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

'==============================================================================
' PDF转Excel方案比较
'==============================================================================

' 方案A: Adobe Acrobat Pro (付费，准确率最高)
' ------------------------------------------------
' 步骤:
' 1. 打开PDF文件
' 2. 文件 > 导出为 > 电子表格 > Microsoft Excel工作簿
' 3. 选择页面范围和设置
' 4. 导出完成后，用VBA解析Excel
'
' 优点: 准确率95%+, 格式保留好
' 缺点: 需要付费软件
'
'
' 方案B: Tabula (免费开源，推荐)
' ------------------------------------------------
' 网址: https://tabula.technology/
' 
' 步骤:
' 1. 下载并安装Tabula
' 2. 导入PDF文件
' 3. 选择表格区域
' 4. 导出为Excel或CSV
' 5. 用VBA解析导出的文件
'
' 优点: 免费, 专门提取表格, 批量处理
' 缺点: 需要手动选择表格区域
'
'
' 方案C: Python自动化工具 (我们提供)
' ------------------------------------------------
' 使用Python Tabula库自动转换
' 参考文件: tools/pdf_converter/pdf_to_excel.py
'
' 优点: 全自动, 批量处理, 免费
' 缺点: 需要Python环境
'
'==============================================================================


'==============================================================================
' VBA辅助代码：批量打开转换后的Excel文件
'==============================================================================

Option Explicit

Sub BatchProcessConvertedExcel()
    '批量处理已转换的Excel文件
    '适用于从PDF转换后的多个Excel文件
    
    Dim folderPath As String
    Dim fileName As String
    Dim wb As Workbook
    Dim processedCount As Long
    
    ' 选择包含转换后Excel文件的文件夹
    With Application.FileDialog(msoFileDialogFolderPicker)
        .Title = "选择包含转换后Excel文件的文件夹"
        If .Show = -1 Then
            folderPath = .SelectedItems(1)
        Else
            Exit Sub
        End If
    End With
    
    ' 确保路径以反斜杠结尾
    If Right(folderPath, 1) <> "\" Then
        folderPath = folderPath & "\"
    End If
    
    ' 遍历文件夹中的所有Excel文件
    fileName = Dir(folderPath & "*.xlsx")
    processedCount = 0
    
    Do While fileName <> ""
        ' 打开文件
        Set wb = Workbooks.Open(folderPath & fileName)
        
        ' 判断类型并解析
        If IsCreditCardStatement(wb.ActiveSheet) Then
            ' 解析信用卡账单
            Call ParseAndExportCreditCard(wb)
            processedCount = processedCount + 1
        ElseIf IsBankStatement(wb.ActiveSheet) Then
            ' 解析银行流水
            Call ParseAndExportBankStatement(wb)
            processedCount = processedCount + 1
        End If
        
        ' 关闭文件
        wb.Close SaveChanges:=False
        
        ' 下一个文件
        fileName = Dir()
    Loop
    
    MsgBox "批量处理完成！" & vbCrLf & "已处理 " & processedCount & " 个文件", vbInformation
End Sub


Sub ParseAndExportCreditCard(wb As Workbook)
    '解析并导出信用卡账单
    Dim ws As Worksheet
    Dim jsonData As String
    Dim outputPath As String
    
    Set ws = wb.ActiveSheet
    
    ' 构建JSON（调用主解析器）
    jsonData = BuildCreditCardJSON(ws)
    
    ' 保存到源文件夹
    outputPath = wb.Path & "\" & Replace(wb.Name, ".xlsx", ".json")
    SaveJSON jsonData, outputPath
End Sub


Sub ParseAndExportBankStatement(wb As Workbook)
    '解析并导出银行流水
    Dim ws As Worksheet
    Dim jsonData As String
    Dim outputPath As String
    
    Set ws = wb.ActiveSheet
    
    ' 构建JSON（调用主解析器）
    jsonData = BuildBankStatementJSON(ws)
    
    ' 保存到源文件夹
    outputPath = wb.Path & "\" & Replace(wb.Name, ".xlsx", ".json")
    SaveJSON jsonData, outputPath
End Sub


'==============================================================================
' PDF质量检查函数
'==============================================================================

Function CheckPDFConversionQuality(ws As Worksheet) As Boolean
    '检查PDF转Excel后的数据质量
    '返回 True 表示质量合格，False 表示需要人工检查
    
    Dim totalCells As Long
    Dim emptyCells As Long
    Dim qualityScore As Double
    
    totalCells = ws.UsedRange.Cells.Count
    emptyCells = Application.WorksheetFunction.CountBlank(ws.UsedRange)
    
    qualityScore = 1 - (emptyCells / totalCells)
    
    If qualityScore > 0.6 Then
        CheckPDFConversionQuality = True
        Debug.Print "转换质量良好: " & Format(qualityScore, "0.0%")
    Else
        CheckPDFConversionQuality = False
        Debug.Print "转换质量较差: " & Format(qualityScore, "0.0%") & " - 建议人工检查"
    End If
End Function


'==============================================================================
' 推荐工作流程
'==============================================================================

' 完整工作流程：
' 
' 1. PDF转Excel (选择方案A/B/C)
'    ├─ Adobe Acrobat Pro导出
'    ├─ Tabula手动选择表格导出
'    └─ Python工具自动批量转换
'
' 2. 质量检查
'    └─ 运行 CheckPDFConversionQuality()
'
' 3. VBA解析
'    ├─ 信用卡: 运行 ParseCreditCardStatement()
'    └─ 银行流水: 运行 ParseBankStatement()
'
' 4. 导出JSON
'    └─ 自动保存到同一文件夹
'
' 5. 上传到Replit
'    └─ POST /api/upload/vba-json
'
'==============================================================================


'==============================================================================
' 常见问题解决
'==============================================================================

' Q1: PDF转Excel后格式混乱怎么办？
' A1: 使用Adobe Acrobat Pro，或在Tabula中手动调整表格区域
'
' Q2: 转换后的Excel有多个工作表？
' A2: 修改VBA代码，遍历所有工作表：
'     For Each ws In wb.Worksheets
'         ' 处理每个工作表
'     Next ws
'
' Q3: 日期格式不一致？
' A3: VBA代码中FormatDate()函数会自动标准化为 dd-mm-yyyy
'
' Q4: 金额中有逗号？
' A4: FindCellAmount()函数会自动移除逗号
'
' Q5: 批量处理100份账单需要多久？
' A5: 大约5-10分钟（取决于电脑性能）
'
'==============================================================================


' 注意: 此文件仅作为指南，不需要导入到Excel中
' 实际使用时，请参考:
' - 1_CreditCardParser.vba
' - 2_BankStatementParser.vba
