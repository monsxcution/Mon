
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "C:\Users\Mon\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\STool Dashboard.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\Python313\python.exe"
oLink.Arguments = ""c:\Users\Mon\Desktop\Main\Main.py""
oLink.Description = "Start STool Dashboard"
oLink.WorkingDirectory = "c:\Users\Mon\Desktop\Main"
oLink.Save
