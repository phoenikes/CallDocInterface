$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\CallDocSQLHKSync.lnk")
$Shortcut.TargetPath = "$PSScriptRoot\dist\CallDocSQLHKSync.exe"
$Shortcut.IconLocation = "$PSScriptRoot\resources\app_icon.ico"
$Shortcut.Description = "CallDoc-SQLHK Synchronisierung"
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.Save()
