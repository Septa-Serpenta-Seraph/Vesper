@echo off
REM Detached multi-file HuggingFace downloader for Windows (survives SSH drops when
REM launched via: wmic process call create "cmd /c C:\hf_download.bat")
REM Pattern verified 8/4/2026 with MiniMax H3 (~42.5GB, 4 files).
REM Edit BASE + the per-file blocks below, scp to C:\hf_download.bat, then:
REM   ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "wmic process call create \"cmd /c C:\\hf_download.bat\""
REM Poll C:\hf_download.log for ALL DONE / FAIL markers.

set BASE=https://huggingface.co/ORG/REPO/resolve/main
if not exist "C:\ComfyUI\models\diffusion_models" mkdir "C:\ComfyUI\models\diffusion_models"
if not exist "C:\ComfyUI\models\text_encoders" mkdir "C:\ComfyUI\models\text_encoders"
if not exist "C:\ComfyUI\models\vae" mkdir "C:\ComfyUI\models\vae"
echo START %date% %time% > C:\hf_download.log

REM --- FILE 1 ---
cd /d C:\ComfyUI\models\diffusion_models
curl -L -o MODEL_ONE.safetensors.tmp -H "User-Agent: ComfyUI/1.0" --max-time 7200 "%BASE%/diffusion_models/MODEL_ONE.safetensors?download=true"
if %errorlevel%==0 (ren MODEL_ONE.safetensors.tmp MODEL_ONE.safetensors && echo FILE1 DONE >> C:\hf_download.log) else (echo FILE1 FAIL %errorlevel% >> C:\hf_download.log)

REM --- FILE 2 ---
cd /d C:\ComfyUI\models\text_encoders
curl -L -o TEXT_ENC.safetensors.tmp -H "User-Agent: ComfyUI/1.0" --max-time 7200 "%BASE%/text_encoders/TEXT_ENC.safetensors?download=true"
if %errorlevel%==0 (ren TEXT_ENC.safetensors.tmp TEXT_ENC.safetensors && echo FILE2 DONE >> C:\hf_download.log) else (echo FILE2 FAIL %errorlevel% >> C:\hf_download.log)

echo ALL DONE %date% %time% >> C:\hf_download.log
