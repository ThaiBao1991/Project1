' =========================================================================
' Chay_Ung_Dung_MBC.vbs - Khoi dong 1-Click: Tu chay Python ngam & Mo Web
' - Khong hien man hinh den (Chay hoan toan an danh / silent).
' - Tu dong chay open_file_helper.py de ho tro mo truc tiep file Excel, Word, UNC.
' - Tu dong mo file index.html bang trinh duyet mac dinh cua may.
' =========================================================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Lay duong dan thu muc hien tai chua file VBS
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Khoi chay Python Helper duoi che do an (WindowStyle = 0: An danh hoan toan)
helperScript = scriptDir & "\open_file_helper.py"

' Uu tien dung pythonw de khong hien bat ky console nao
cmdHelper = "cmd.exe /c start /b pythonw """ & helperScript & """ || start /b python """ & helperScript & """"
WshShell.Run cmdHelper, 0, False

' 2. Doi nhe 300ms de helper lang nghe cong 38271
WScript.Sleep 300

' 3. Mo Web App tren trinh duyet mac dinh qua dia chi cuc bo 127.0.0.1:38271 (Hoac mo file index.html neu helper chua xong)
appUrl = "http://127.0.0.1:38271/"
WshShell.Run """" & appUrl & """", 1, False
