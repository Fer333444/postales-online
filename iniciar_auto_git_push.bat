@echo off
cd /d "C:\Users\syrfase\Downloads\POSTALES_TEST\POSTALES_TEST\postales-render-deploy"
start powershell -NoExit -ExecutionPolicy Bypass -Command "python auto_git_push.py"
