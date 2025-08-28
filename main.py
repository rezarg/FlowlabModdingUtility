import ctypes, webbrowser, os, pyperclip, time, json, sys, tempfile

import FlowlabModdingUtils as FMU
import tkinter as tk

from typing import Optional, Literal
from tkinter import messagebox
from hashlib import md5

GUID = "com.rezarg.flowlabmoddingutils"
NAME = "Flowlab Modding Utility"
VERSION = "1.0.0b"
TITLE = NAME

DEBUG = False

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(GUID)

root = tk.Tk()
root.wm_title(f"{TITLE}{(' (Debug)' if DEBUG else '')}")
root.wm_geometry(f"1280x720+{int(root.winfo_screenwidth()/2-1280/2)}+{int(root.winfo_screenheight()/2-720/2)}")
root.wm_resizable(True, True)
root.wm_minsize(640, 380)

if os.path.exists("favicon.ico"): root.wm_iconbitmap("favicon.ico")
else:
	ICO_DATA_PATH = getattr(sys, '_MEIPASS', os.path.dirname(__file__)) + os.sep + "favicon.ico"
	tmpico = os.path.join(tempfile.gettempdir(), "favicon.ico")
	with open(ICO_DATA_PATH, "rb") as fsrc:
		with open(tmpico, "wb") as fdst:
			fdst.write(fsrc.read())
	root.wm_iconbitmap(tmpico)

# Variables

API_GAME_FETCH = "https://flowlab.io/game/fetch/%s?auth_token=null" # Get GameInfo
API_ENTITY_FOR_LEVEL = "https://flowlab.io/entity/for_level/%s?auth_token=null" # Get Level Data
API_BEHAVIOR_FOR_ENTITY = "https://flowlab.io/behavior/for_entity_class/%s?auth_token=null" # Get Entity's Behaviors
API_SPRITE_FOR_ENTITY = "/assets/users/55/user_%s/game_%s/img_asset_%s.png" # Get Entity's Sprite

AssetManager = FMU.AssetManager()
dirty = False

# Functions

def UpdateTitle(newTitle: Optional[str]):
	global TITLE
	TITLE = newTitle
	SetDirty(dirty)

def SetDirty(isDirty:bool=True):
	global dirty
	dirty = isDirty

	dirtyTitle = f"* {TITLE}{(' (Debug)' if DEBUG else '')}"
	cleanTitle = f"{TITLE}{(' (Debug)' if DEBUG else '')}"

	if isDirty and root.wm_title() != dirtyTitle: root.wm_title(dirtyTitle)
	elif not isDirty and root.wm_title() != cleanTitle: root.wm_title(cleanTitle)

def LoadAssetViewEntityClasses():
	global AssetView_EntityClasses
	for v in AssetView_EntityClasses: v["button"].destroy()
	AssetView_EntityClasses = []
	EntityClasses = reversed(sorted([{ "id": EntityClass["id"], "name": EntityClass["name"] } for EntityClass in AssetManager.GameInfo["entity_classes"]], key=lambda x: x["name"]))
	for EntityClass in EntityClasses:
		button = tk.Button(AssetView, text=EntityClass["name"], command=MenuCommandNotImplemented, border=0, width=50, anchor="w", font="Arial 10", padx=10)
		button.pack(side="top", anchor="nw", fill="x", expand=True, before=AssetViewLabelLevels, after=AssetViewLabelObjects)
		AssetView_EntityClasses.append({ "id": EntityClass["id"], "button": button })
		button.config(command=lambda entityClass=EntityClass: EditEntityClass(AssetManager.GetEntityClassFromId(entityClass["id"])))

def LoadAssetViewLevels():
	global AssetView_Levels
	for v in AssetView_Levels: v["button"].destroy()
	AssetView_Levels = []
	Levels = reversed(sorted([{ "id": Level["id"], "name": Level["name"], "ordinal": Level["ordinal"] } for Level in AssetManager.GameInfo["levels"]], key=lambda x: x["ordinal"]))
	for Level in Levels:
		button = tk.Button(AssetView, text=f"[{Level['ordinal']}] - {Level['name']}", command=MenuCommandNotImplemented, border=0, width=50, anchor="w", font="Arial 10", padx=10)
		button.pack(side="top", anchor="nw", fill="x", expand=True, after=AssetViewLabelLevels)
		AssetView_Levels.append({ "id": Level["id"], "button": button })
		button.config(command=lambda level=Level: EditLevel(level))

def MenuFileLoad():
	AssetManager.RequestManifestFromExe()

	if AssetManager.manifestPath is None: return

	LoadAssetViewEntityClasses()
	LoadAssetViewLevels()

	UpdateTitle(f"{NAME} - {AssetManager.GameInfo['name']}")

	menuFile.entryconfig("Save Game", state="normal")
	menuFile.entryconfig("Launch Game", state="normal")
	menuAssets.entryconfig("New Entity Class", state="normal")
	menuAssets.entryconfig("New Level", state="normal")
	menuAssets.entryconfig("Edit GameInfo", state="normal")
	# menuAssets.entryconfig("Add Existing Asset", state="normal")
	# menuAssets.entryconfig("Remove Existing Asset", state="normal")
	# menuAssets.entryconfig("Reorder Levels", state="normal")
	# menuAssets.entryconfig("Update Manifest", state="normal")

def MenuFileSave():
	AssetManager.SaveAll()
	SetDirty(False)

def TryExit():
	if dirty:
		choice = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Save Changes?", icon="warning", default="yes")
		if choice == None: return
		if choice == True:
			MenuFileSave()
			TryExit()
			return
	exit()

def LaunchGame():
	MenuFileSave()
	# AssetManager.CleanManifest()
	os.system(f"start {AssetManager.gamePath}")

def ClearEditView():
	for w in EditView_Widgets:
		w.destroy()

def EditLevelContents(level: dict):
	levelPath = API_ENTITY_FOR_LEVEL % level["id"]
	levelPath = f"assets/{md5(str.encode(levelPath)).hexdigest()}.json"
	os.system(f"start notepad.exe {AssetManager.rootPath}/{levelPath}")

def ChangeLevelOrdinal(levelId: int, direction: Literal["up", "down"]):
	minOrdinal = 1
	maxOrdinal = 1

	for level in AssetManager.GameInfo["levels"]: maxOrdinal = max(maxOrdinal, level["ordinal"])

	ordinal = AssetManager.GetLevelFromId(levelId)["ordinal"]

	if direction == "up": newOrdinal = max(minOrdinal, ordinal-1)
	elif direction == "down": newOrdinal = min(maxOrdinal, ordinal+1)

	if ordinal == newOrdinal: return

	for level in AssetManager.GameInfo["levels"]:
		if level["ordinal"] == newOrdinal:
			level["ordinal"] = ordinal
			break
	
	AssetManager.GetLevelFromId(levelId)["ordinal"] = newOrdinal
	SetDirty()

	LoadAssetViewLevels()
	EditLevel(AssetManager.GetLevelFromId(levelId))

def EditLevel(level: dict):
	ClearEditView()

	title = tk.Label(EditView, text=f"[Level] {level['name']}", anchor="center", font="Arial 14", state="disabled")
	title.pack(side="top", anchor="n", fill="x", expand=True)
	EditView_Widgets.append(title)

	editLevel = tk.Button(EditView, text="Edit Level", command=lambda Level=level: EditLevelContents(Level))
	editLevel.pack(side="top", anchor="w", pady=5)
	EditView_Widgets.append(editLevel)

	# ordinal_title = tk.Label(EditView, text=f"Level Ordinal", font="Arial 12", state="disabled", anchor="center")
	# ordinal_title.pack(side="top", anchor="w", fill="x", expand=True)
	# EditView_Widgets.append(ordinal_title)

	ordinal_buttons = tk.Frame(EditView)
	ordinal_buttons.pack(side="top", anchor="w")
	EditView_Widgets.append(ordinal_buttons)

	ordinal_moveUp = tk.Button(ordinal_buttons, text="Move Level Up", command=lambda Level=level: ChangeLevelOrdinal(Level["id"], "up"))
	ordinal_moveUp.pack(side="left", anchor="w", padx=(0, 5))

	ordinal_moveDown = tk.Button(ordinal_buttons, text="Move Level Down", command=lambda Level=level: ChangeLevelOrdinal(Level["id"], "down"))
	ordinal_moveDown.pack(side="left", after=ordinal_moveUp, anchor="w", padx=(5, 0))

	after = ordinal_buttons
	Levels = sorted([{ "id": Level["id"], "name": Level["name"], "ordinal": Level["ordinal"] } for Level in AssetManager.GameInfo["levels"]], key=lambda x: x["ordinal"])
	for v in Levels:
		label = tk.Label(EditView, text=f"{'* ' if v['id'] == level['id'] else ''}{v['name']}", anchor="w", font="Arial 10")
		label.pack(side="top", anchor="w", fill="x", expand=True, after=after)
		EditView_Widgets.append(label)
		after=label
	
	deleteLevel = tk.Button(EditView, text="⚠ Delete Level", command=lambda Level=level: DeleteLevel(Level))
	deleteLevel.pack(side="top", anchor="w", pady=(10, 0), after=after)
	EditView_Widgets.append(deleteLevel)

def OpenEntityClassSprite(entityClass: dict):
	spritePath = API_SPRITE_FOR_ENTITY % (AssetManager.GameInfo["user_id"], AssetManager.GameInfo["id"], entityClass["id"])
	spritePath = f"assets/{md5(str.encode(spritePath)).hexdigest()}.png"

	os.system(f"start {AssetManager.rootPath}/{spritePath}")

def CopyEntityClassBehaviors(entityClass: dict):
	behaviorPath = API_BEHAVIOR_FOR_ENTITY % entityClass['id']
	behaviorPath = f"assets/{md5(str.encode(behaviorPath)).hexdigest()}.json"
	with open(f"{AssetManager.rootPath}/{behaviorPath}") as f:
		pyperclip.copy(f.read())
		messagebox.showinfo("Copied Successfully", f"Copied Behaviors for Entity Class '{entityClass['name']}' Successfully!")

def EditEntityClassBehaviors(entityClass: dict):
	behaviorPath = API_BEHAVIOR_FOR_ENTITY % entityClass['id']
	behaviorPath = f"assets/{md5(str.encode(behaviorPath)).hexdigest()}.json"
	os.system(f"start notepad.exe {AssetManager.rootPath}/{behaviorPath}")

def EditEntityClass(entityClass: dict):
	ClearEditView()

	title = tk.Label(EditView, text=f"[Entity Class] {entityClass['name']}", font="Arial 14", state="disabled")
	title.pack(side="top", anchor="n", fill="x", expand=True)
	EditView_Widgets.append(title)

	copyBehaviors = tk.Button(EditView, text="Copy Behaviors", command=lambda EC=entityClass: CopyEntityClassBehaviors(EC))
	copyBehaviors.pack(side="top", anchor="w", pady=5)
	EditView_Widgets.append(copyBehaviors)

	editBehaviors = tk.Button(EditView, text="Edit Behaviors", command=lambda EC=entityClass: EditEntityClassBehaviors(EC))
	editBehaviors.pack(side="top", anchor="w", pady=5)
	EditView_Widgets.append(editBehaviors)

	editSprite = tk.Button(EditView, text="Edit Sprite", command=lambda EC=entityClass: OpenEntityClassSprite(EC))
	editSprite.pack(side="top", anchor="w", pady=5)
	EditView_Widgets.append(editSprite)

def CreateNewLevel():
	levelId = int(time.time())

	level = {
		"bg_color": 0xFFFFFF,
		"id": levelId,
		"name": "New Level",
		"ordinal": len(AssetManager.GameInfo["levels"]) + 1}

	AssetManager.GameInfo["levels"].append(level)

	levelPathName = API_ENTITY_FOR_LEVEL % level["id"]
	levelPathName = md5(str.encode(levelPathName)).hexdigest()

	with open(f"{AssetManager.rootPath}/assets/{levelPathName}.json", "w") as f:
		json.dump([], f)

	AssetManager.AddFile(f"assets/{levelPathName}.json")

	SetDirty()
	LoadAssetViewLevels()
	EditLevel(level)

def DeleteLevel(level: dict):
	confirm = messagebox.askyesno("Delete Level", f"Are you sure you want to delete level '{level['name']}'?\n\nTHIS CANNOT BE UNDONE")
	if not confirm: return

	for x in AssetManager.GameInfo["levels"]: # Delete level
		if x["ordinal"] != level["ordinal"]: continue
		AssetManager.GameInfo["levels"].remove(x)
		break

	AssetManager.RemoveFile(f"assets/{md5(str.encode(API_ENTITY_FOR_LEVEL % level['id'])).hexdigest()}.json")

	for v in AssetManager.GameInfo["levels"]: # Shift levels after deleted level down to fill the gap
		if v["ordinal"] <= level["ordinal"]: continue
		v["ordinal"] -= 1

	for filename in os.listdir(f"{AssetManager.rootPath}/assets"):
		if filename.startswith(md5(str.encode(API_ENTITY_FOR_LEVEL % level["id"])).hexdigest()):
			os.remove(f"{AssetManager.rootPath}/assets/{filename}")
			break

	SetDirty()
	MenuFileSave()
	LoadAssetViewLevels()
	ClearEditView()

def CreateNewEntityClass():
	MenuCommandNotImplemented()

def EditGameInfo():
	gameInfoPath = API_GAME_FETCH % AssetManager.GameInfo["id"]
	gameInfoPath = f"assets/{md5(str.encode(gameInfoPath)).hexdigest()}.json"

	os.system(f"start notepad.exe {AssetManager.rootPath}/{gameInfoPath}")

def MenuCommandNotImplemented(): messagebox.showerror("Not Implemented", "This command is not implemented yet.")

# Build Menu

menu = tk.Menu()

menuFile = tk.Menu(tearoff=0)
menuFile.add_command(label="Load Game", command=MenuFileLoad)
menuFile.add_command(label="Save Game", command=MenuFileSave, state="disabled")
menuFile.add_separator()
menuFile.add_command(label="Launch Game", command=LaunchGame, state="disabled")
menuFile.add_separator()
menuFile.add_command(label="Exit", command=TryExit)
menu.add_cascade(label="File", menu=menuFile)

menuAssets = tk.Menu(tearoff=0)
menuAssets.add_command(label="New Entity Class", command=CreateNewEntityClass, state="disabled")
menuAssets.add_command(label="New Level", command=CreateNewLevel, state="disabled")
menuAssets.add_separator()
menuAssets.add_command(label="Edit GameInfo", command=EditGameInfo, state="disabled")
# menuAssets.add_separator()
# menuAssets.add_command(label="Add Existing Asset", command=MenuCommandNotImplemented, state="disabled") # obsolete (?)
# menuAssets.add_command(label="Remove Existing Asset", command=MenuCommandNotImplemented, state="disabled") # obsolete (?)
# menuAssets.add_separator()
# menuAssets.add_command(label="Reorder Levels", command=MenuCommandNotImplemented, state="disabled") # obsolete
# menuAssets.add_separator()
# menuAssets.add_command(label="Update Manifest", command=MenuCommandNotImplemented, state="disabled") # obsolete
menu.add_cascade(label="Assets", menu=menuAssets)

menu.add_separator()

menuAbout = tk.Menu(tearoff=0)
menuAbout.add_command(label="Made by rezarg", state="disabled")
menuAbout.add_separator()
menuAbout.add_command(label="Discord Community", command=lambda: webbrowser.open("https://discord.gg/shyn7pB6Uw"))
menuAbout.add_command(label=f"Version {VERSION}", command=lambda: messagebox.showinfo(f"{NAME} Version", f"{NAME}{(' (Debug)' if DEBUG else '')}\n{GUID}-v{VERSION}"))
menu.add_cascade(label="About", menu=menuAbout)

menuDebug = tk.Menu(tearoff=0)
menuDebug.add_command(label="Dirty On",  command=lambda: SetDirty(True))
menuDebug.add_command(label="Dirty Off",  command=lambda: SetDirty(False))
if DEBUG: menu.add_cascade(label="Debug", menu=menuDebug)

root.config(menu = menu)

# AssetView

AssetViewScrollbar = tk.Scrollbar(root)
AssetViewCanvas = tk.Canvas(root, width="200", yscrollcommand=AssetViewScrollbar.set)
AssetViewCanvas.pack(side="left", anchor="w", fill="y", padx=10)
AssetViewScrollbar.pack(side="left", anchor="w", fill="y")
AssetViewScrollbar.config(command=AssetViewCanvas.yview)
AssetView = tk.Frame(AssetViewCanvas)
AssetViewId = AssetViewCanvas.create_window(0, 0, window=AssetView, anchor="nw")

AssetView.bind("<Configure>", lambda _: AssetViewCanvas.config(scrollregion=f"0 0 0 {AssetView.winfo_reqheight()}"))

AssetViewLabelObjects = tk.Label(AssetView, text="Entity Classes", font="Arial 12", anchor="center", state="disabled")
AssetViewLabelObjects.pack(side="top", anchor="w")

AssetViewLabelLevels = tk.Label(AssetView, text="Levels", font="Arial 12", anchor="center", state="disabled")
AssetViewLabelLevels.pack(side="top", anchor="w")

AssetViewLabelMargin1 = tk.Frame(AssetView, height="10")
AssetViewLabelMargin1.pack(side="top", anchor="w", before=AssetViewLabelLevels, after=AssetViewLabelObjects)
AssetViewLabelMargin2 = tk.Frame(AssetView, height="10")
AssetViewLabelMargin2.pack(side="bottom", anchor="w")

AssetView_EntityClasses = []
AssetView_Levels = []

# EditView

EditViewScrollbar = tk.Scrollbar(root)
EditViewCanvas = tk.Canvas(root, yscrollcommand=EditViewScrollbar.set)
EditViewCanvas.pack(side="left", anchor="e", fill="both", expand=True, padx=(5, 0))
EditViewScrollbar.pack(side="right", anchor="e", fill="y")
EditViewScrollbar.config(command=AssetViewCanvas.yview)
EditView = tk.Frame(EditViewCanvas)
EditViewId = EditViewCanvas.create_window(0, 0, window=EditView, anchor="nw", width=EditViewCanvas.winfo_width())

EditView.bind("<Configure>", lambda _: EditViewCanvas.config(scrollregion=f"0 0 0 {EditView.winfo_reqheight()}"))
EditViewCanvas.bind("<Configure>", lambda e: EditViewCanvas.itemconfig(EditViewId, width=e.width))

EditView_Widgets: list[tk.Widget] = []

# Mainloop

messagebox.showwarning("Crappy Code Warning", """
It is very likely you will end up corrupting your game while using this tool. This is not your fault.

Use at your own risk and make backups of your modded files regularly.

Hopefully, future versions will be less prone to errors. If your game corrupts, please share what you did before you noticed it was corrupted (i.e., I deleted a level) to rezarg on Discord.

Have fun modding!""")

root.mainloop()