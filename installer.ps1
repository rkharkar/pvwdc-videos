# first, check if running scripts is allowed. If not, set unrestricted permissions for running scripts
$execPolicy = Get-ExecutionPolicy
if ($execPolicy -ne "Unrestricted")
{
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted -Force;
}

# next, try getting python embedded. Could be an issue with  SSL/TLS versions, so resolve that
try {
    Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.9.1/python-3.9.1-embed-amd64.zip -UseBasicParsing -OutFile python.zip
}
catch [System.Net.WebException] {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.9.1/python-3.9.1-embed-amd64.zip -UseBasicParsing -OutFile python.zip
}

Expand-Archive -LiteralPath .\python.zip -DestinationPath .\

rm .\python.zip

Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile .\get-pip.py

.\python.exe .\get-pip.py --no-warn-script-location

rm .\get-pip.py

# I think this was for path stuff. Not sure if still required
Move-Item .\Transcriber\python39._pth .\ -force

cd .\Scripts

# ez_setup errors are irrelevant. setuptools is good enough
.\pip3.9.exe install moviepy --no-warn-script-location

# newer versions try to easy_install, which is deprecated. Will need to remove this once fixed
.\pip3.9.exe install imageio==2.4.1 --no-warn-script-location

.\pip3.9.exe install speechrecognition --no-warn-script-location

.\pip3.9.exe install fuzzywuzzy --no-warn-script-location

# dependency that isn't installed for whatever reason
.\pip3.9.exe install requests --no-warn-script-location

cd ..\Transcriber\

..\python.exe .\transcriber.py