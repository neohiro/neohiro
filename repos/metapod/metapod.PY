#!/usr/bin/env python3
"""
metapod_hardening_final_extended_nopassword.py

Metapod Hardening Tool — Extended edition with additional suggested hardening functions.
PASSWORD LENGTH & EXPIRATION POLICY REMOVED AS REQUESTED.

Run as Administrator. If not elevated, the script will attempt to relaunch itself with elevation.
"""

import os
import sys
import ctypes
import subprocess
import threading
import datetime
import json
from queue import Queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ------------------------- SETTINGS (with descriptions) -------------------------
# Each entry: id, name, enable cmd, disable cmd, desc

SETTINGS = {

    # -----------------------------------------------------------
    # File Associations
    # -----------------------------------------------------------
    "File Associations": [
        {"id": "hta_notepad", "name": "Harden .hta files (open in Notepad)",
         "enable": 'ftype htafile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype htafile="%SystemRoot%\\System32\\mshta.exe" "%1" %*',
         "desc": "Open .hta files in Notepad rather than mshta.exe."},

        {"id": "wsh_notepad", "name": "Harden .wsh files",
         "enable": 'ftype wshfile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype wshfile="%SystemRoot%\\System32\\WScript.exe" "%1" %*',
         "desc": "Redirect .wsh file handling to Notepad."},

        {"id": "wsf_notepad", "name": "Harden .wsf files",
         "enable": 'ftype wsffile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype wsffile="%SystemRoot%\\System32\\WScript.exe" "%1" %*',
         "desc": "Open .wsf script files in an editor."},

        {"id": "bat_notepad", "name": "Harden .bat files",
         "enable": 'ftype batfile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype batfile="%1" %*',
         "desc": "Open batch files in Notepad instead of executing."},

        {"id": "js_notepad", "name": "Harden .js files",
         "enable": 'ftype jsfile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype jsfile="%SystemRoot%\\System32\\WScript.exe" "%1" %*',
         "desc": "Open .js files in Notepad."},

        {"id": "jse_notepad", "name": "Harden .jse files",
         "enable": 'ftype jsefile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype jsefile="%SystemRoot%\\System32\\WScript.exe" "%1" %*',
         "desc": "Open encoded JavaScript files safely."},

        {"id": "vbe_notepad", "name": "Harden .vbe files",
         "enable": 'ftype vbefile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype vbefile="%SystemRoot%\\System32\\WScript.exe" "%1" %*',
         "desc": "Open encoded VBScript files."},

        {"id": "vbs_notepad", "name": "Harden .vbs files",
         "enable": 'ftype vbsfile="%SystemRoot%\\system32\\NOTEPAD.EXE" "%1"',
         "disable": 'ftype vbsfile="%SystemRoot%\\System32\\WScript.exe" "%1" %*',
         "desc": "Open .vbs files in Notepad."},
    ],

    # -----------------------------------------------------------
    # Windows Defender
    # -----------------------------------------------------------
    "Windows Defender": [
        {"id": "def_sandbox", "name": "Enable Windows Defender Sandboxing",
         "enable": 'setx /M MP_FORCE_USE_SANDBOX 1',
         "disable": 'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" /v MP_FORCE_USE_SANDBOX /f',
         "desc": "Enable Defender process sandboxing."},

        {"id": "def_pua", "name": "Enable PUA Protection",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -PUAProtection Enable"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -PUAProtection Disable"',
         "desc": "Block potentially unwanted applications."},

        {"id": "def_passive", "name": "Enable Defender Passive Mode",
         "enable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows Defender" /v PassiveMode /t REG_DWORD /d 2 /f',
         "disable": 'reg delete "HKCU\\SOFTWARE\\Microsoft\\Windows Defender" /v PassiveMode /f',
         "desc": "Enable passive periodic scanning."},

        {"id": "def_maps", "name": "Enable Advanced Cloud Protection",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -MAPSReporting Advanced"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -MAPSReporting 0"',
         "desc": "Enable cloud-based protection."},

        {"id": "def_samples", "name": "Disable Automatic Sample Submission",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -SubmitSamplesConsent 0"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -SubmitSamplesConsent 1"',
         "desc": "Disable sample submission."},

        {"id": "def_elam", "name": "Enable Early Launch Anti-Malware",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Policies\\EarlyLaunch" /v DriverLoadPolicy /t REG_DWORD /d 3 /f',
         "disable": 'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Policies\\EarlyLaunch" /v DriverLoadPolicy /f',
         "desc": "Load ELAM early for boot protection."},
    ],

    # -----------------------------------------------------------
    # Attack Surface Reduction
    # -----------------------------------------------------------
    "Attack Surface Reduction": [
        {"id": "asr_office_childproc", "name": "Block Office Child Processes",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids D4F940AB-401B-4EFC-AADC-AD5F3C50688A -AttackSurfaceReductionRules_Actions Enabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids D4F940AB-401B-4EFC-AADC-AD5F3C50688A -AttackSurfaceReductionRules_Actions Disabled"',
         "desc": "Block Office from spawning child processes."},

        {"id": "asr_office_inject", "name": "Block Office Process Injection",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids 75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84 -AttackSurfaceReductionRules_Actions Enabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids 75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84 -AttackSurfaceReductionRules_Actions Disabled"',
         "desc": "Block Office memory injection attacks."},

        {"id": "asr_obfuscated_scripts", "name": "Block Obfuscated Scripts",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids 5BEB7EFE-FD9A-4556-801D-275E5FFC04CC -AttackSurfaceReductionRules_Actions Enabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids 5BEB7EFE-FD9A-4556-801D-275E5FFC04CC -AttackSurfaceReductionRules_Actions Disabled"',
         "desc": "Block obfuscated scripts."},

        {"id": "asr_script_launch_exec", "name": "Block JS/VBS from Executing EXEs",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids D3E037E1-3EB8-44C8-A917-57927947596D -AttackSurfaceReductionRules_Actions Enabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids D3E037E1-3EB8-44C8-A917-57927947596D -AttackSurfaceReductionRules_Actions Disabled"',
         "desc": "Prevent script engines from launching EXEs."},

        {"id": "asr_psexec_wmi", "name": "Block PSExec & WMI Lateral Movement",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids d1e49aac-8f56-4280-b9ba-993a6d77406c -AttackSurfaceReductionRules_Actions Enabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Add-MpPreference -AttackSurfaceReductionRules_Ids d1e49aac-8f56-4280-b9ba-993a6d77406c -AttackSurfaceReductionRules_Actions Disabled"',
         "desc": "Reduce lateral movement."},
    ],

    # -----------------------------------------------------------
    # System-Wide Protections
    # -----------------------------------------------------------
    "System-Wide Protections": [
        {"id": "sys_exploit_prot", "name": "Enable System Exploit Protection",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Set-Processmitigation -System -Enable DEP,EmulateAtlThunks,BottomUp,HighEntropy,SEHOP,TerminateOnError"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-Processmitigation -System -Disable DEP,EmulateAtlThunks,BottomUp,HighEntropy,SEHOP,TerminateOnError"',
         "desc": "Enable DEP, SEHOP, ASLR global mitigations."},

        {"id": "sys_lsass_ppl", "name": "Enable LSASS as Protected Process",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa" /v RunAsPPL /f',
         "desc": "Harden LSASS to resist credential dumping."},

        {"id": "sys_wdigest", "name": "Disable WDigest Credential Caching",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\WDigest" /v UseLogonCredential /t REG_DWORD /d 0 /f',
         "disable": 'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\WDigest" /v UseLogonCredential /f',
         "desc": "Prevent plain-text credential caching."},

        {"id": "sys_safedll", "name": "Enable Safe DLL Search Mode",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager" /v SafeDLLSearchMode /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager" /v SafeDLLSearchMode /f',
         "desc": "Mitigate DLL hijacking."},

        {"id": "sys_uac", "name": "Enable UAC",
         "enable": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 1 /f',
         "disable": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 0 /f',
         "desc": "Enable User Account Control."},

        {"id": "sys_uac_always", "name": "Set UAC to Always Notify",
         "enable": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 2 /f',
         "disable": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 5 /f',
         "desc": "Enable highest level UAC prompts."},
    ],

    # -----------------------------------------------------------
    # Browser + Office
    # -----------------------------------------------------------
    "Browser & Office": [
        {"id": "br_edge_smartscreen", "name": "Enable Edge SmartScreen",
         "enable": 'reg add "HKCU\\SOFTWARE\\Policies\\Microsoft\\MicrosoftEdge\\PhishingFilter" /v EnabledV9 /t REG_DWORD /d 1 /f',
         "disable": 'reg add "HKCU\\SOFTWARE\\Policies\\Microsoft\\MicrosoftEdge\\PhishingFilter" /v EnabledV9 /t REG_DWORD /d 0 /f',
         "desc": "Enable SmartScreen filtering."},

        {"id": "br_edge_pwdmgr", "name": "Disable Edge Password Manager",
         "enable": 'reg add "HKCU\\SOFTWARE\\Policies\\Microsoft\\MicrosoftEdge\\Main" /v "FormSuggest Passwords" /t REG_SZ /d no /f',
         "disable": 'reg add "HKCU\\SOFTWARE\\Policies\\Microsoft\\MicrosoftEdge\\Main" /v "FormSuggest Passwords" /t REG_SZ /d yes /f',
         "desc": "Disable built-in password manager."},

        {"id": "br_chrome_siteisolation", "name": "Enable Chrome Site Isolation",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v "SitePerProcess" /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v "SitePerProcess" /f',
         "desc": "Enforce per-site process isolation."},

        {"id": "br_chrome_doh", "name": "Enable Chrome DNS-over-HTTPS",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v "DnsOverHttpsMode" /t REG_SZ /d "on" /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v "DnsOverHttpsMode" /f',
         "desc": "Enable encrypted DNS."},

        {"id": "off_disable_macros", "name": "Disable Office Macros by Default",
         "enable": 'reg add "HKCU\\Software\\Policies\\Microsoft\\Office\\16.0\\Word\\Security" /v vbawarnings /t REG_DWORD /d 4 /f',
         "disable": 'reg add "HKCU\\Software\\Policies\\Microsoft\\Office\\16.0\\Word\\Security" /v vbawarnings /t REG_DWORD /d 1 /f',
         "desc": "Block macros with notification."},
    ],

    # -----------------------------------------------------------
    # Privacy + Logging
    # -----------------------------------------------------------
    "Privacy & Logging": [
        {"id": "priv_telemetry", "name": "Set Telemetry to Security-Only",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
         "disable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 3 /f',
         "desc": "Minimize telemetry."},

        {"id": "priv_adid", "name": "Disable Advertising ID",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AdvertisingInfo" /v DisabledByGroupPolicy /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AdvertisingInfo" /v DisabledByGroupPolicy /f',
         "desc": "Disable Advertising ID usage."},

        {"id": "priv_location", "name": "Disable Location Data",
         "enable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location" /v Value /t REG_SZ /d Deny /f',
         "disable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location" /v Value /t REG_SZ /d Allow /f',
         "desc": "Disable app location access."},

        {"id": "priv_bing", "name": "Disable Bing Search",
         "enable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f',
         "disable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 1 /f',
         "desc": "Disable Bing in Start search."},

        {"id": "priv_cortana", "name": "Disable Cortana",
         "enable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" /v CortanaConsent /t REG_DWORD /d 0 /f',
         "disable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" /v CortanaConsent /t REG_DWORD /d 1 /f',
         "desc": "Disable Cortana assistant."},

        {"id": "priv_pslog", "name": "Enable PowerShell Script Block Logging",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\ScriptBlockLogging" /v EnableScriptBlockLogging /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\ScriptBlockLogging" /v EnableScriptBlockLogging /f',
         "desc": "Enable PowerShell script logging."},

        {"id": "priv_audit_cmdline", "name": "Include Command Line in Event Logs",
         "enable": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System\\Audit" /v ProcessCreationIncludeCmdLine_Enabled /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System\\Audit" /v ProcessCreationIncludeCmdLine_Enabled /f',
         "desc": "Add command-line to process creation logs."},
    ],

    # -----------------------------------------------------------
    # Firewall & Network
    # -----------------------------------------------------------
    "Firewall & Network": [
        {"id": "fw_all_on", "name": "Enable Firewall for All Profiles",
         "enable": 'NetSh Advfirewall set allprofiles state on',
         "disable": 'NetSh Advfirewall set allprofiles state off',
         "desc": "Enable all firewalls."},

        {"id": "fw_block_inbound", "name": "Block All Inbound (Public)",
         "enable": 'netsh advfirewall set publicprofile firewallpolicy blockinboundalways,allowoutbound',
         "disable": 'netsh advfirewall set publicprofile firewallpolicy allowinbound,allowoutbound',
         "desc": "Harden the public profile."},

        {"id": "fw_netprot", "name": "Enable Defender Network Protection",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -EnableNetworkProtection Enabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-MpPreference -EnableNetworkProtection Disabled"',
         "desc": "Block malicious domains."},

        {"id": "fw_disable_smb1", "name": "Disable SMBv1",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Disable-WindowsOptionalFeature -Online -FeatureName smb1protocol -NoRestart"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Enable-WindowsOptionalFeature -Online -FeatureName smb1protocol -NoRestart"',
         "desc": "Disable legacy SMBv1."},

        {"id": "fw_disable_llmnr", "name": "Disable LLMNR",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" /v EnableMulticast /t REG_DWORD /d 0 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" /v EnableMulticast /f',
         "desc": "Disable LLMNR."},
    ],

    # -----------------------------------------------------------
    # Advanced Hardening
    # -----------------------------------------------------------
    "Advanced Hardening": [
        {"id": "adv_wpad", "name": "Disable WPAD",
         "enable": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Wpad" /v WpadOverride /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Wpad" /v WpadOverride /f',
         "desc": "Disable web proxy autodiscovery."},

        {"id": "adv_ps2", "name": "Disable PowerShell 2.0",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Get-WindowsOptionalFeature -Online | Where-Object { $_.FeatureName -like \'*PowerShellV2*\' } | Disable-WindowsOptionalFeature -Online -NoRestart"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Get-WindowsOptionalFeature -Online | Where-Object { $_.FeatureName -like \'*PowerShellV2*\' } | Enable-WindowsOptionalFeature -Online -All -NoRestart"',
         "desc": "Prevent downgrade attacks."},

        {"id": "adv_spooler", "name": "Disable Print Spooler",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Stop-Service Spooler -Force; Set-Service Spooler -StartupType Disabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-Service Spooler -StartupType Automatic; Start-Service Spooler"',
         "desc": "Disable Print Spooler if not needed."},

        {"id": "adv_rdp", "name": "Disable RDP",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f',
         "disable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f',
         "desc": "Disable Remote Desktop."},

        {"id": "adv_winrm", "name": "Disable WinRM",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Stop-Service WinRM -Force; Set-Service WinRM -StartupType Disabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-Service WinRM -StartupType Automatic; Start-Service WinRM"',
         "desc": "Disable Windows Remote Management."},

        {"id": "adv_dmaguard", "name": "Block DMA Access when Locked",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DMAGuard" /v DeviceEnumerationPolicy /t REG_DWORD /d 0 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DMAGuard" /v DeviceEnumerationPolicy /f',
         "desc": "Block DMA attacks from Thunderbolt devices."},
    ],

    # -----------------------------------------------------------
    # Additional Hardening
    # -----------------------------------------------------------
    "Additional Hardening": [
        {"id": "add_wsh_disable", "name": "Disable Windows Script Host",
         "enable": 'reg add "HKLM\\Software\\Microsoft\\Windows Script Host\\Settings" /v Enabled /t REG_DWORD /d 0 /f',
         "disable": 'reg add "HKLM\\Software\\Microsoft\\Windows Script Host\\Settings" /v Enabled /t REG_DWORD /d 1 /f',
         "desc": "Disable WSH globally."},

        {"id": "add_autorun_disable", "name": "Disable Autorun",
         "enable": 'reg add "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoDriveTypeAutoRun /t REG_DWORD /d 255 /f',
         "disable": 'reg delete "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoDriveTypeAutoRun /f',
         "desc": "Disable autorun to prevent USB malware."},

        {"id": "add_remoteassist_disable", "name": "Disable Remote Assistance",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance" /v fAllowToGetHelp /t REG_DWORD /d 0 /f',
         "disable": 'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance" /v fAllowToGetHelp /f',
         "desc": "Disable remote assistance."},

        {"id": "add_wer_disable", "name": "Disable Windows Error Reporting",
         "enable": 'reg add "HKLM\\Software\\Microsoft\\Windows\\Windows Error Reporting" /v Disabled /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\Software\\Microsoft\\Windows\\Windows Error Reporting" /v Disabled /f',
         "desc": "Disable error reporting service."},

        {"id": "add_clipboard_history_disable", "name": "Disable Clipboard History",
         "enable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Clipboard" /v EnableClipboardHistory /t REG_DWORD /d 0 /f',
         "disable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Clipboard" /v EnableClipboardHistory /t REG_DWORD /d 1 /f',
         "desc": "Disable clipboard history storage."},

        {"id": "add_smartscreen_system", "name": "Enable Windows SmartScreen",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableSmartScreen /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableSmartScreen /f',
         "desc": "Enable SmartScreen globally."},

        {"id": "add_suggestapps_disable", "name": "Disable Suggested Apps",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent" /v DisableWindowsConsumerFeatures /t REG_DWORD /d 1 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent" /v DisableWindowsConsumerFeatures /f',
         "desc": "Disable consumer feature suggestions."},

        {"id": "add_peoplebar_disable", "name": "Disable People Bar",
         "enable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v PeopleBand /t REG_DWORD /d 0 /f',
         "disable": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v PeopleBand /t REG_DWORD /d 1 /f',
         "desc": "Hide People Bar UI."},

        {"id": "add_wifisense_disable", "name": "Disable WiFi Sense",
         "enable": 'reg add "HKLM\\SOFTWARE\\Microsoft\\WcmSvc\\wifinetworkmanager\\config" /v AutoConnectAllowedOEM /t REG_DWORD /d 0 /f',
         "disable": 'reg delete "HKLM\\SOFTWARE\\Microsoft\\WcmSvc\\wifinetworkmanager\\config" /v AutoConnectAllowedOEM /f',
         "desc": "Disable WiFi Sense features."},

        {"id": "add_smb_client_fallback", "name": "Disable SMB Guest Auth",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 0 /f',
         "disable": 'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters" /v AllowInsecureGuestAuth /f',
         "desc": "Disable insecure SMB fallback."},

        {"id": "add_webdav_disable", "name": "Disable WebDAV (WebClient)",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "Stop-Service WebClient -Force; Set-Service WebClient -StartupType Disabled"',
         "disable": 'powershell -ExecutionPolicy Bypass -Command "Set-Service WebClient -StartupType Manual; Start-Service WebClient"',
         "desc": "Disable WebDAV client service."},
    ],

    # -----------------------------------------------------------
    # New: Authentication & Accounts (PASSWORD POLICY REMOVED)
    # -----------------------------------------------------------
    "Authentication & Accounts": [
        {"id": "acct_disable_builtin_admin", "name": "Disable Built-in Administrator Account",
         "enable": 'net user Administrator /active:no',
         "disable": 'net user Administrator /active:yes',
         "desc": "Disable local Administrator account."},

        {"id": "acct_disable_guest", "name": "Disable Guest Account",
         "enable": 'net user Guest /active:no',
         "disable": 'net user Guest /active:yes',
         "desc": "Disable Guest account."},

        {"id": "acct_lockout_policy", "name": "Enable Account Lockout Policy (3 attempts)",
         "enable": 'net accounts /lockoutthreshold:3 /lockoutduration:30 /lockoutwindow:30',
         "disable": 'net accounts /lockoutthreshold:0',
         "desc": "Enforce account lockout after failed attempts."},
    ],

    # -----------------------------------------------------------
    # Storage & Disk
    # -----------------------------------------------------------
    "Storage & Disk": [
        {"id": "disk_enable_bitlocker", "name": "Enable BitLocker (OS Drive)",
         "enable": 'manage-bde -on C: -rp -usedspaceonly',
         "disable": 'manage-bde -off C:',
         "desc": "Enable BitLocker drive encryption."},

        {"id": "disk_disable_autounmount", "name": "Disable Auto-Mounting Volumes",
         "enable": 'mountvol /N',
         "disable": 'mountvol /E',
         "desc": "Prevent auto-mount of new volumes."},
    ],

    # -----------------------------------------------------------
    # Updates
    # -----------------------------------------------------------
    "Updates & Patch Management": [
        {"id": "upd_enable_auto_updates", "name": "Enable Automatic Windows Updates",
         "enable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 0 /f',
         "disable": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f',
         "desc": "Enable automatic updates."},

        {"id": "upd_enable_reboot_control", "name": "Configure Active Hours",
         "enable": 'powershell -ExecutionPolicy Bypass -Command "New-ItemProperty -Path \\"HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU\\" -Name ActiveHoursStart -PropertyType DWord -Value 8 -Force; New-ItemProperty -Path \\"HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU\\" -Name ActiveHoursEnd -PropertyType DWord -Value 18 -Force"',
         "disable": '',
         "desc": "Set update active hours (8–18)."},
    ],

    # -----------------------------------------------------------
    # Logging & Monitoring
    # -----------------------------------------------------------
    "Logging & Monitoring": [
        {"id": "log_enable_firewall_logging", "name": "Enable Firewall Logging",
         "enable": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile" /v LoggingFilePath /t REG_SZ /d "%systemroot%\\system32\\LogFiles\\Firewall\\pfirewall.log" /f & reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile" /v LogFileSize /t REG_DWORD /d 16384 /f',
         "disable": '',
         "desc": "Enable Windows Firewall packet logging."},

        {"id": "log_enable_auditing_account", "name": "Enable Account Logon Auditing",
         "enable": 'auditpol /set /subcategory:"Account Logon" /success:enable /failure:enable & auditpol /set /subcategory:"Logon" /success:enable /failure:enable',
         "disable": 'auditpol /set /subcategory:"Account Logon" /success:disable /failure:disable & auditpol /set /subcategory:"Logon" /success:disable /failure:disable',
         "desc": "Enable account and logon auditing."},

        {"id": "log_forwarding_wef", "name": "Enable Event Forwarding (WECUTIL QC)",
         "enable": 'wecutil qc /q',
         "disable": 'wecutil disable-collector',
         "desc": "Prepare system for event forwarding."},
    ],
}

# ------------------------------------------------------------------------
# Recommended Preset
# ------------------------------------------------------------------------

RECOMMENDED_PRESET = {
    "enable": [
        "hta_notepad", "wsh_notepad", "wsf_notepad", "bat_notepad", "js_notepad",
        "jse_notepad", "vbe_notepad", "vbs_notepad",
        "def_pua", "def_maps", "def_elam",
        "asr_office_childproc", "asr_office_inject",
        "asr_obfuscated_scripts", "asr_script_launch_exec",
        "sys_exploit_prot", "sys_lsass_ppl", "sys_wdigest", "sys_safedll",
        "sys_uac", "sys_uac_always",
        "br_edge_smartscreen", "br_chrome_siteisolation", "br_chrome_doh",
        "off_disable_macros",
        "priv_pslog", "priv_audit_cmdline", "priv_telemetry",
        "priv_bing", "priv_cortana",
        "fw_all_on", "fw_netprot", "fw_disable_smb1", "fw_disable_llmnr",
        "adv_ps2", "adv_dmaguard",
        "add_wsh_disable", "add_autorun_disable",
        "add_clipboard_history_disable", "add_smartscreen_system",
        "acct_disable_builtin_admin", "acct_disable_guest",
        "acct_lockout_policy",
        "upd_enable_auto_updates",
        "log_enable_firewall_logging", "log_enable_auditing_account"
    ],
    "disable": []
}

# ------------------------------------------------------------------------
# Tooltip Class
# ------------------------------------------------------------------------

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self._enter)
        widget.bind("<Leave>", self._leave)

    def _enter(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID,
                         borderwidth=1, wraplength=360)
        label.pack(ipadx=4, ipady=2)

    def _leave(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
        self.tipwindow = None

# ------------------------------------------------------------------------
# HardeningTool Class
# ------------------------------------------------------------------------

class HardeningTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Metapod Hardening — Extended")
        self.root.geometry("1100x720")

        self.log_queue = Queue()
        self.backup_before_changes = tk.BooleanVar(value=True)
        self.vars = {}
        self.action_vars = {}
        self.last_backup_dir = None

        # ---------------------------------------------------
        # UI Construction
        # ---------------------------------------------------
        top_frame = ttk.Frame(root, padding=8)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.apply_button = ttk.Button(top_frame, text="Apply Changes",
                                       command=self.start_apply_thread)
        self.apply_button.pack(side=tk.RIGHT, padx=6)

        ttk.Checkbutton(
            top_frame,
            text="Create registry backup + restore point before changes",
            variable=self.backup_before_changes
        ).pack(side=tk.RIGHT, padx=8)

        ttk.Button(top_frame, text="Select Recommended Preset",
                   command=self.apply_recommended_preset).pack(side=tk.LEFT, padx=6)

        ttk.Button(top_frame, text="Select All",
                   command=self.select_all).pack(side=tk.LEFT, padx=6)

        ttk.Button(top_frame, text="Deselect All",
                   command=self.deselect_all).pack(side=tk.LEFT, padx=6)

        main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_pane.pack(expand=True, fill=tk.BOTH, padx=8, pady=(0, 8))

        left_frame = ttk.Frame(main_pane, width=220)
        main_pane.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Categories",
                  font=(None, 11, 'bold')).pack(anchor='w', padx=8, pady=(6, 2))

        self.cat_listbox = tk.Listbox(
            left_frame, exportselection=False, activestyle='none')
        self.cat_listbox.pack(expand=True, fill=tk.BOTH, padx=8, pady=4)
        self.cat_listbox.bind('<<ListboxSelect>>', self.on_category_select)

        for cat in SETTINGS.keys():
            self.cat_listbox.insert(tk.END, cat)

        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=4)

        self.cat_title = ttk.Label(right_frame, text='',
                                   font=(None, 12, 'bold'))
        self.cat_title.pack(anchor='w', padx=6, pady=(6, 0))

        options_container = ttk.Frame(right_frame)
        options_container.pack(expand=True, fill=tk.BOTH, padx=6, pady=6)

        self.canvas = tk.Canvas(options_container)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(
            options_container, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.options_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.options_frame, anchor='nw')
        self.options_frame.bind(
            '<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill=tk.BOTH, padx=8, pady=(0, 8), expand=False)

        log_frame = ttk.LabelFrame(bottom_frame, text="Output Log")
        log_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=6, pady=4)
        self.output_log = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12, state='disabled')
        self.output_log.pack(expand=True, fill=tk.BOTH)

        right_control_frame = ttk.Frame(bottom_frame)
        right_control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=6)

        ttk.Button(right_control_frame, text="Open Last Backup Folder",
                   command=self.open_last_backup).pack(fill=tk.X, pady=4)

        ttk.Button(right_control_frame, text="Create Rollback Script",
                   command=self.create_rollback_script_ui).pack(fill=tk.X, pady=4)

        for cat, items in SETTINGS.items():
            for s in items:
                self.vars[s['id']] = tk.BooleanVar(value=True)
                self.action_vars[s['id']] = tk.StringVar(value="Enable")

        self.checkbox_widgets = {}

        first_cat = list(SETTINGS.keys())[0]
        self.populate_category(first_cat)
        self.process_log_queue()

    # ------------------------------------------------------------------------
    # UI Population Functions
    # ------------------------------------------------------------------------

    def populate_category(self, category_name):
        for child in self.options_frame.winfo_children():
            child.destroy()

        self.cat_title.config(text=category_name)
        items = SETTINGS.get(category_name, [])

        for s in items:
            frame = ttk.Frame(self.options_frame)
            frame.pack(fill=tk.X, pady=2, padx=2)

            chk = ttk.Checkbutton(frame, text=s['name'], variable=self.vars[s['id']])
            chk.pack(side=tk.LEFT, anchor='w')
            Tooltip(chk, s.get('desc', ''))

            info_btn = ttk.Button(frame, text='i', width=2,
                                  command=lambda desc=s['desc'], title=s['name']: messagebox.showinfo(title, desc))
            info_btn.pack(side=tk.RIGHT, padx=6)

            combo = ttk.Combobox(frame, textvariable=self.action_vars[s['id']],
                                 values=["Enable", "Disable"], state="readonly", width=8)
            combo.pack(side=tk.RIGHT, padx=6)

            self.checkbox_widgets[s['id']] = chk

    def on_category_select(self, event=None):
        sel = self.cat_listbox.curselection()
        if sel:
            cat = self.cat_listbox.get(sel[0])
            self.populate_category(cat)

    # ------------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------------

    def process_log_queue(self):
        try:
            while not self.log_queue.empty():
                msg = self.log_queue.get_nowait()
                if msg == 'TASK_COMPLETE':
                    self.apply_button.config(state='normal')
                    messagebox.showinfo(
                        'Finished', 'All selected operations have been completed.')
                else:
                    self.output_log.config(state='normal')
                    self.output_log.insert(tk.END, msg + "\n")
                    self.output_log.see(tk.END)
                    self.output_log.config(state='disabled')
        finally:
            self.root.after(150, self.process_log_queue)

    # ------------------------------------------------------------------------
    # Command Execution
    # ------------------------------------------------------------------------

    def run_command(self, command, name, timeout=120):
        if not command:
            self.log_queue.put(f"[!] Skipped: {name}")
            return

        self.log_queue.put(f"[*] Running: {name}")

        try:
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            stdout, stderr = proc.communicate(timeout=timeout)

            if stdout:
                self.log_queue.put(f"    Output: {stdout.strip()}")
            if stderr:
                self.log_queue.put(f"    Error: {stderr.strip()}")

            if proc.returncode == 0:
                self.log_queue.put(f"[+] Success: {name}")
            else:
                self.log_queue.put(
                    f"[-] Exit code {proc.returncode}: {name}")

        except subprocess.TimeoutExpired:
            self.log_queue.put(
                f"    ERROR: Command timed out after {timeout} seconds.")
            try:
                proc.kill()
                proc.communicate()
            except Exception:
                pass
        except Exception as e:
            self.log_queue.put(f"[!] Exception: {e}")

        self.log_queue.put("-" * 40)

    # ------------------------------------------------------------------------
    # Apply Settings
    # ------------------------------------------------------------------------

    def start_apply_thread(self):
        if not messagebox.askyesno('Confirm Changes',
                                   'Are you sure you want to apply these changes?'):
            return

        self.apply_button.config(state='disabled')
        self.output_log.config(state='normal')
        self.output_log.delete("1.0", tk.END)
        self.output_log.config(state='disabled')

        threading.Thread(target=self.apply_settings_worker,
                         daemon=True).start()

    def apply_settings_worker(self):
        self.log_queue.put('Starting changes...')

        if self.backup_before_changes.get():
            try:
                self.log_queue.put(
                    '[!] Creating registry backup + restore point...')
                backup_dir = self.backup_registry()
                self.last_backup_dir = backup_dir
                self.create_restore_point()
            except Exception as e:
                self.log_queue.put(f"[!] Safety backup failed: {e}")

        for cat, items in SETTINGS.items():
            for s in items:
                if self.vars[s['id']].get():
                    action = self.action_vars[s['id']].get()
                    if action == "Enable":
                        self.run_command(s['enable'], f"Enable {s['name']}")
                    else:
                        self.run_command(s['disable'], f"Disable {s['name']}")
                else:
                    self.log_queue.put(f"Skipping: {s['name']}")

        self.log_queue.put('All tasks completed.')
        self.log_queue.put('TASK_COMPLETE')

    # ------------------------------------------------------------------------
    # Preset + Selection Helpers
    # ------------------------------------------------------------------------

    def select_all(self):
        for k in self.vars:
            self.vars[k].set(True)

        sel = self.cat_listbox.curselection()
        if sel:
            self.populate_category(self.cat_listbox.get(sel[0]))

    def deselect_all(self):
        for k in self.vars:
            self.vars[k].set(False)

        sel = self.cat_listbox.curselection()
        if sel:
            self.populate_category(self.cat_listbox.get(sel[0]))

    def apply_recommended_preset(self):
        if not messagebox.askyesno('Apply Preset', 'Apply the recommended safe preset?'):
            return

        for k in self.vars:
            self.vars[k].set(False)

        for sid in RECOMMENDED_PRESET['enable']:
            if sid in self.vars:
                self.vars[sid].set(True)
                self.action_vars[sid].set("Enable")

        for sid in RECOMMENDED_PRESET['disable']:
            if sid in self.vars:
                self.vars[sid].set(True)
                self.action_vars[sid].set("Disable")

        sel = self.cat_listbox.curselection()
        if sel:
            self.populate_category(self.cat_listbox.get(sel[0]))

        self.log_queue.put('[+] Recommended preset applied.')

    # ------------------------------------------------------------------------
    # Backup & Restore Helpers
    # ------------------------------------------------------------------------

    def backup_registry(self):
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(os.getcwd(), f'RegistryBackup_{ts}')
        os.makedirs(backup_dir, exist_ok=True)

        self.log_queue.put(f"[*] Backing up registry to: {backup_dir}")

        exports = [
            (r'HKLM', os.path.join(backup_dir, 'HKLM.reg')),
            (r'HKCU', os.path.join(backup_dir, 'HKCU.reg')),
            (r'HKCR', os.path.join(backup_dir, 'HKCR.reg')),
            (r'HKU', os.path.join(backup_dir, 'HKU.reg')),
        ]

        for hive, path in exports:
            cmd = f'reg export "{hive}" "{path}" /y'
            self.run_command(cmd, f"Backup {hive}", timeout=180)

        with open(os.path.join(backup_dir, 'metadata.txt'),
                  'w', encoding='utf-8') as f:
            f.write("Metapod Hardening Backup\n")
            f.write(str(datetime.datetime.now()))

        self.log_queue.put(f"[+] Registry backup complete.")
        return backup_dir

    def create_restore_point(self):
        cmd = (
            'powershell -ExecutionPolicy Bypass -Command '
            '"if (Get-ComputerRestorePoint -ErrorAction SilentlyContinue) '
            '{ Checkpoint-Computer -Description \\"Metapod Hardening\\" '
            '-RestorePointType MODIFY_SETTINGS } '
            'else { Write-Host \\"Restore point unavailable.\\"; exit 2 }"'
        )
        self.run_command(cmd, "Create System Restore Point")

    def open_last_backup(self):
        if not self.last_backup_dir or not os.path.isdir(self.last_backup_dir):
            messagebox.showinfo('No Backup', 'No backup has been created yet.')
            return
        subprocess.Popen(f'explorer "{self.last_backup_dir}"')

    def create_rollback_script_ui(self):
        if not self.last_backup_dir:
            messagebox.showinfo('No Backup', 'No backup created yet.')
            return

        msg = messagebox.askyesno(
            'Create Rollback Script',
            f'Create rollback script for:\n{self.last_backup_dir}?'
        )
        if not msg:
            return

        path = self.create_rollback_script(self.last_backup_dir)
        messagebox.showinfo('Rollback Created',
                            f"Rollback script created:\n{path}")

    def create_rollback_script(self, backup_dir):
        path = os.path.join(backup_dir, 'rollback_restore_registry.bat')
        lines = [
            '@echo off\n',
            'echo Restoring registry backup...\n',
        ]

        for name in ("HKLM.reg", "HKCU.reg", "HKCR.reg", "HKU.reg"):
            full = os.path.join(backup_dir, name)
            if os.path.isfile(full):
                lines.append(f'reg import "{full}"\n')

        lines.append('echo Done.\n')
        lines.append('pause\n')

        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return path

# ------------------------------------------------------------------------
# Elevation
# ------------------------------------------------------------------------

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------

if __name__ == '__main__':
    if is_admin():
        root = tk.Tk()
        HardeningTool(root)
        root.mainloop()
    else:
        script = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(
            None, 'runas', sys.executable, f'"{script}"', None, 1)
