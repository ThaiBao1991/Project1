# tools/save_gh_token.ps1 — lưu token GitHub MỘT LẦN, không bật hộp thoại đăng nhập.
#
# VÌ SAO: các tool Python trước đây gọi `git credential fill` mỗi lần upload.
# Khi Git Credential Manager không đọc được credential, nó bật hộp thoại đăng
# nhập GitHub — chạy nền nhiều tiến trình nên hộp thoại hiện liên tục.
#
# Script này đọc credential ĐÃ LƯU trong Windows Credential Locker và ghi ra:
#   %LOCALAPPDATA%\VocabularyApp\github_token.txt
# Sau đó mọi tool dùng tools/gh_token.py (đọc file này trước) ⇒ không hỏi lại.
#
# Cách dùng (PowerShell):
#   powershell -ExecutionPolicy Bypass -File tools\save_gh_token.ps1
#
# Nếu Credential Locker chưa có token: mở GitHub → Settings → Developer settings
# → Personal access tokens → tạo token (scope `repo`), rồi chạy:
#   powershell -ExecutionPolicy Bypass -File tools\save_gh_token.ps1 -Token "ghp_..."
param(
    [string]$Token = ""
)

$ErrorActionPreference = "Stop"
$dir = Join-Path $env:LOCALAPPDATA "VocabularyApp"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$outFile = Join-Path $dir "github_token.txt"

if ($Token) {
    Set-Content -Path $outFile -Value $Token.Trim() -Encoding ascii -NoNewline
    Write-Host "Da luu token (tu tham so) vao $outFile"
    exit 0
}

$cs = @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class VocabCredReader {
    [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool CredRead(string target, int type, int reservedFlag, out IntPtr credentialPtr);
    [DllImport("advapi32.dll", SetLastError=true)]
    static extern void CredFree(IntPtr cred);
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
    struct CREDENTIAL {
        public uint Flags; public uint Type; public string TargetName; public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize; public IntPtr CredentialBlob;
        public uint Persist; public uint AttributeCount; public IntPtr Attributes;
        public string TargetAlias; public string UserName;
    }
    public static string Get(string target) {
        IntPtr p;
        if (!CredRead(target, 1, 0, out p)) return "";
        try {
            CREDENTIAL c = (CREDENTIAL)Marshal.PtrToStructure(p, typeof(CREDENTIAL));
            byte[] b = new byte[c.CredentialBlobSize];
            Marshal.Copy(c.CredentialBlob, b, 0, (int)c.CredentialBlobSize);
            return Encoding.Unicode.GetString(b).TrimEnd('\0');
        } finally { CredFree(p); }
    }
}
'@
Add-Type -TypeDefinition $cs -Language CSharp

$tok = [VocabCredReader]::Get("git:https://github.com")
if (-not $tok) {
    Write-Host "KHONG tim thay credential 'git:https://github.com' trong Windows Credential Locker."
    Write-Host "Hay tao Personal Access Token (scope repo) roi chay lai:"
    Write-Host '  powershell -ExecutionPolicy Bypass -File tools\save_gh_token.ps1 -Token "ghp_..."'
    exit 1
}
Set-Content -Path $outFile -Value $tok -Encoding ascii -NoNewline
Write-Host "Da luu token ($($tok.Length) ky tu) vao $outFile"
