Attribute VB_Name = "StampByAntigravity_Module"
' ============================================================
' Module: StampByAntigravity (Image-Based) - Gọi từ Access
' Tác giả: Antigravity IDE
' Phiên bản: 1.0
' ============================================================
'
' HƯỚNG DẪN:
'   Script Python: StampByAntigravity.py
'   Cú pháp: python StampByAntigravity.py <pdf_path> <config_name>
'
'   - <config_name> là tên file JSON trong thư mục stamp_configs/
'     (không cần đuôi .json)
'   - Config được tạo bằng StamFolder01/02/03.py rồi nhập vào
'     stamp_configs/ của StampByAntigravity
'
' ============================================================

' ── Cấu hình đường dẫn cố định ─────────────────────────────
Private Const PYTHON_EXE   As String = "C:\Python312\python.exe"
Private Const SCRIPT_PATH  As String = "C:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\StamptAuto\StampByAntigravity\StampByAntigravity.py"

' ── Hàm đóng dấu 1 file với 1 config ─────────────────────
Public Function StampOneFile(pdfPath As String, configName As String) As Boolean
    Dim wsh As Object
    Dim cmd As String
    Dim exitCode As Long

    pdfPath = Replace(pdfPath, "file:///", "")
    pdfPath = Replace(pdfPath, "#", "")
    pdfPath = Replace(pdfPath, "\", "/")

    cmd = "cmd /c """ & _
          """" & PYTHON_EXE & """ " & _
          """" & SCRIPT_PATH & """ " & _
          """" & pdfPath & """ " & _
          """" & configName & """"

    Debug.Print "[StampByAntigravity] CMD: " & cmd

    Set wsh = CreateObject("WScript.Shell")
    exitCode = wsh.Run(cmd, 0, True)   ' 0 = ẩn cửa sổ, True = chờ kết thúc
    Set wsh = Nothing

    ' Exit code: 0=OK, 1=lỗi, 2=không trang nào được đóng dấu
    StampOneFile = (exitCode = 0)

    If exitCode = 0 Then
        Debug.Print "[StampByAntigravity] OK: " & pdfPath
    ElseIf exitCode = 2 Then
        Debug.Print "[StampByAntigravity] WARN: Không trang nào được đóng dấu: " & pdfPath
    Else
        Debug.Print "[StampByAntigravity] ERROR (exit=" & exitCode & "): " & pdfPath
    End If
End Function

' ── Sub chính: gọi từ nút bấm Access ─────────────────────
Public Sub Stamp_ImageBased_Click()
    Dim rs          As DAO.Recordset
    Dim pdfPath     As String
    Dim configName  As String
    Dim dem         As Long
    Dim maxCheck    As Long
    Dim fso         As Object
    Dim successCount As Long
    Dim failCount   As Long

    ' ── ĐỔI configName theo loại dấu cần đóng ──────────────
    ' Ví dụ: "GRR", "GRR_IMX_MsNa", "Grr_LMX_MsNa_HCN"
    ' (Tên file JSON trong stamp_configs/, không cần .json)
    configName = "GRR"

    maxCheck     = 999
    dem          = 0
    successCount = 0
    failCount    = 0

    Set fso = CreateObject("Scripting.FileSystemObject")
    Set rs  = Me.Table_DATA_CONFIRM_SF.Form.RecordsetClone

    If rs.EOF And rs.BOF Then
        MsgBox "Không có dữ liệu để xử lý.", vbInformation
        GoTo ExitHere
    End If

    rs.MoveFirst

    Do While Not rs.EOF

        If rs!check = True Then
            dem = dem + 1

            If dem > maxCheck Then
                MsgBox "Vượt quá giới hạn " & maxCheck & " file.", vbExclamation
                Exit Do
            End If

            pdfPath = rs!Driver

            If fso.FileExists(Replace(Replace(Replace(pdfPath, "file:///", ""), "#", ""), "/", "\")) Then
                If StampOneFile(pdfPath, configName) Then
                    successCount = successCount + 1
                Else
                    failCount = failCount + 1
                    Debug.Print "Thất bại: " & pdfPath
                End If
            Else
                Debug.Print "Không tìm thấy file: " & pdfPath
                failCount = failCount + 1
            End If
        End If

        rs.MoveNext
    Loop

    MsgBox "Hoàn tất!" & vbCrLf & _
           "✓ Thành công: " & successCount & vbCrLf & _
           "✗ Thất bại  : " & failCount, vbInformation

ExitHere:
    On Error Resume Next
    rs.Close
    Set rs  = Nothing
    Set fso = Nothing
End Sub

' ── Sub gọi với config tuỳ chọn (qua InputBox) ────────────
Public Sub Stamp_ImageBased_WithChoice()
    Dim configName As String
    configName = InputBox("Nhập tên cấu hình đóng dấu:" & vbCrLf & _
                          "(Ví dụ: GRR, GRR_IMX_MsNa, Grr_LMX_MsNa_HCN)", _
                          "Chọn Config", "GRR")
    If configName = "" Then Exit Sub
    ' Gán configName vào biến module rồi gọi lại Stamp_ImageBased_Click
    ' (hoặc tích hợp trực tiếp)
    Debug.Print "Sử dụng config: " & configName
    ' Gọi StampOneFile trực tiếp cho demo:
    ' Call StampOneFile("C:/path/to/file.pdf", configName)
End Sub
