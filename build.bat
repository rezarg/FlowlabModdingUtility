@echo off

pyinstaller main.py ^
	--name FlowlabModdingUtility ^
	--icon favicon.ico ^
	--onefile ^
	--noconsole ^
	--clean ^
	--noconfirm ^
	--add-data "favicon.ico;."

pause