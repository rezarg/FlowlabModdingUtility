from typing import Optional
from tkinter import filedialog
import tkinter as tk
import urllib.parse as URL
import json, os

def DecodeManifest(path: str) -> dict:
	with open(path) as f:
		data = json.load(f)

		encoded: str = data["assets"]

		tokenGroups = []
		tokens = []

		reusable = []

		i = -1
		while i < len(encoded) - 1:
			i += 1

			if encoded[i] == "a":
				pass
			elif encoded[i] == "h":
				pass
			elif encoded[i] == "g":
				tokens = []  # Reset token group
				pass
			elif encoded[i] == "o":
				tokenGroups.append(tokens) # Close token group
				pass
			elif encoded[i] == "y":
				length = ""
				n = 1
				while True:
					if encoded[i + n] == ":":
						break
					length += encoded[i + n]
					n += 1

				i += len(length) + 2
				content = URL.unquote(encoded[i : i + int(length)])
				i += int(length) - 1

				tokens.append({"type": "str", "value": content})
				reusable.append(content)
			elif encoded[i] == "i":
				number = ""
				n = 1
				while True:
					if encoded[i + n].isdigit():
						number += encoded[i + n]
						n += 1
					else:
						break

				i += len(number)

				tokens.append({"type": "int", "value": int(number)})
			elif encoded[i] == "z":
				tokens.append({"type": "int", "value": 0})
			elif encoded[i] == "R":
				number = ""
				n = 1
				while True:
					if encoded[i + n].isdigit():
						number += encoded[i + n]
						n += 1
					else:
						break

				i += len(number)

				tokens.append(
					{
						"type": "str",
						"value": reusable[int(number)],
						"source": int(number),
					}
				)
			else:
				tokens.append({"type": "null", "value": encoded[i]})
				print(f"Unknown character found: {encoded[i]}")

		decoded = []

		i = -1
		while i < len(tokenGroups) - 1:
			i += 1

			decodedObject = {}

			j = -1
			while j < len(tokenGroups[i]) - 1:
				j += 1

				token = tokenGroups[i][j]

				if token["type"] == "null":
					pass

				decodedObject[token["value"]] = tokenGroups[i][j + 1]["value"]
				j += 1

				pass

			decoded.append(decodedObject)

		return {
			"rootPath": "/".join(path.split("/")[:-2]),
			"rootPathRTM": "../",
			"version": 2,
			"assets": decoded
		}

def GetReusable(reusable: list, token: str) -> tuple[str, bool]:
	if reusable.count(token) > 0:
		return f"R{reusable.index(token)}", True
	else:
		reusable.append(token)
		return token, False

def EncodeManifest(outputPath: str, manifest: dict) -> dict:
	encoded = {
		"name": None,
		"assets": None,
		"rootPath": "../",
		"version": 2,
		"libraryArgs": [],
		"libraryType": None,
	}

	assets = "a"
	reusable = []

	i = -1
	while i < len(manifest["assets"]) - 1:
		i += 1

		token = manifest["assets"][i]

		if token["type"] != "FONT":
			pathStr, pSr = GetReusable(reusable, 'path')
			path, _ = GetReusable(reusable, URL.quote(token["path"], ""))
			sizeStr, sSr = GetReusable(reusable, 'size')
			typeStr, tSr = GetReusable(reusable, 'type')
			type, tr = GetReusable(reusable, token["type"])
			idStr, iSr = GetReusable(reusable, 'id')
			id, ir = GetReusable(reusable, URL.quote(token["id"], ""))
						
			assets += "o"

			if pSr: assets += pathStr
			else: assets += f"y{len(pathStr)}:{pathStr}"
			assets += f"y{len(path)}:{path}"

			if sSr: assets += sizeStr
			else: assets += f"y{len(sizeStr)}:{sizeStr}"
			assets += f"i{token['size']}"

			if tSr: assets += typeStr
			else: assets += f"y{len(typeStr)}:{typeStr}"
			if tr: assets += type
			else: assets += f"y{len(type)}:{type}"

			if iSr: assets += idStr
			else: assets += f"y{len(idStr)}:{idStr}"
			if ir: assets += id
			else: assets += f"y{len(id)}:{id}"

			assets += "g"
		else:
			assets += "o"

			sizeStr, sSr = GetReusable(reusable, 'size')
			typeStr, tSr = GetReusable(reusable, 'type')
			type, tr = GetReusable(reusable, token["type"])
			classNameStr, cNSr = GetReusable(reusable, 'className')
			className, cNr = GetReusable(reusable, token["className"])
			idStr, iSr = GetReusable(reusable, 'id')
			id, ir = GetReusable(reusable, URL.quote(token["id"], ""))

			if sSr: assets += sizeStr
			else: assets += f"y{len(sizeStr)}:{sizeStr}"
			assets += f"i{token['size']}"

			if tSr: assets += typeStr
			else: assets += f"y{len(typeStr)}:{typeStr}"
			if tr: assets += type
			else: assets += f"y{len(type)}:{type}"

			if cNSr: assets += classNameStr
			else: assets += f"y{len(classNameStr)}:{classNameStr}"
			if cNr: assets += className
			else: assets += f"y{len(className)}:{className}"

			if iSr: assets += idStr
			else: assets += f"y{len(idStr)}:{idStr}"
			if ir: assets += id
			else: assets += f"y{len(id)}:{id}"

			assets += "g"

	assets += "h"

	encoded["assets"] = assets

	with open(outputPath, "w") as f: json.dump(encoded, f)

	return encoded

def MassReplace(string: str, old: list[str], new: str) -> str:
	res = string
	for v in old: res = res.replace(v, new)
	return res

class BehaviorData:
	def __init__(self):
		self.version = "2"
		self.nodes = []
		self.links = []
	
	def ToJSON(self):
		return {
			"version": self.version,
			"nodes": self.nodes,
			"links": self.links}

class EntityBehaviors:
	def __init__(self, id: int, version: int = 1, behaviorData: BehaviorData = None):
		self.id = id
		self.version = version
		self.data = behaviorData if behaviorData is not None else BehaviorData()
	
	def AddNode(self, node: dict):
		self.data.nodes.append(node)
		return self
	
	def AddLink(self, nodeFrom: dict, outputId: int, nodeTo: dict, inputId: int):
		self.data.links.append({
			"input_id": f"{nodeTo['id']}i{str(outputId)}",
			"output_id": f"{nodeFrom['id']}o{str(inputId)}"})
		return self

	def ToJSON(self):
		return {
			"id": self.id,
			"version": self.version,
			"data": self.data.ToJSON()}

class AssetManager:
	def __init__(self, manifestPath: str = ""):
		self.manifest = None
		self.manifestPath = None
		self.rootPath = None
		self.gamePath = None

		self.GameInfo = None

		if manifestPath != "": self.SetManifestFromFile(manifestPath)
	
	# def CleanManifest(self): # I shouldn't have to use this.
	# 	for asset in self.manifest["assets"]:
	# 		if "path" not in asset: path = asset["id"]
	# 		else: path = asset["path"]
	# 		# print(f"[MANIFEST CLEANER]: Checking Asset: {path} ...")
	# 		if not os.path.exists(os.path.join(self.rootPath, path)):
	# 			print(f"[MANIFEST CLEANER]: Removed Asset from Manifest. Asset not found: '{path}'")
	# 			self.manifest["assets"].remove(asset)
	# 	return self

	def __getEntityClasses__(self) -> dict:
		entityClasses = []
		for token in self.manifest["assets"]:
			if token["type"] != "TEXT": continue
			if token["path"].split(".")[-1] != "json": continue
			with open(f"{self.manifest['rootPath']}/{token['path']}") as f: data = json.load(f)
			if "data" not in data: continue
			# fileId: str = token["id"].split("/")[-1].split(".")[0]
			# entityClasses.append({
			# 	"hash": fileId,
			# 	"id": data["id"],
			# 	"version": data["version"],
			# 	"data": data["data"]
			# })
			entityClasses.append(EntityBehaviors(
				data["id"],
				data["version"],
				data["data"]))
		return entityClasses
	
	def RequestManifestFromExe(self):
		window = tk.Tk()
		window.withdraw()
		exePath = filedialog.askopenfilename(defaultextension=".exe", filetypes=[("Flowlab Game Files", "*.exe")])
		rootPath = os.path.dirname(exePath)
		try:
			self.SetManifestFromFile(f"{rootPath}/manifest/default.json")
			self.gamePath = exePath
		except Exception as e:
			print(f"Failed to load Manifest from '{rootPath}/manifest/default.json'. Error: {e}")
		finally:
			window.destroy()
		return self
	
	def SetManifestFromFile(self, path: str):
		if path == "": return
		if not path.endswith(".json"): raise ValueError("Manifest Path must be a JSON file.")
		manifest = DecodeManifest(path)
		rootPath = os.path.normpath(os.path.join(os.path.dirname(path), manifest["rootPathRTM"])).replace("\\", "/")
		self.manifest = manifest
		self.manifestPath = path
		self.rootPath = rootPath
		self.GameInfo = self.__loadGameInfo__()
		return self
	
	def SaveManifest(self):
		EncodeManifest(self.manifestPath, self.manifest)
		
	def SaveGameInfo(self):
		for token in self.manifest["assets"]:
			if token["type"] != "TEXT": continue
			if not token["path"].endswith(".json"): continue
			with open(f"{self.rootPath}/{token['path']}", "r") as f:
				content = f.read()
				if content == "":
					print(f"Warning: Asset File {f.name} is Corrupted.")
				else:
					try:
						data = json.loads(content)
						if not "game" in data: continue
						with open(f"{self.rootPath}/{token['path']}", "w") as f:
							json.dump({ "game": self.GameInfo }, f)
							return
					except Exception as e:
						raise Exception(f"Error while saving to {f.name}: {e}")

	def SaveAll(self):
		self.SaveGameInfo()
		self.SaveManifest()

	def GetBehaviorsForEntity(self, id: int) -> Optional[EntityBehaviors]:
		for entityClass in self.__getEntityClasses__():
			if entityClass.id == id: return entityClass
		return None
	
	def __loadGameInfo__(self) -> dict:
		for token in self.manifest["assets"]:
			if token["type"] != "TEXT": continue
			if not token["path"].endswith(".json"): continue
			with open(f"{self.rootPath}/{token['path']}") as f:
				content = f.read()
				if content == "":
					print(f"Warning: Asset File {f.name} is Corrupted.")
				else:
					try:
						data = json.loads(content)
						if "game" in data: return data["game"]
					except Exception as e:
						raise Exception(f"Error while parsing {f.name}: {e}")
		raise ValueError("Manifest is corrupted or not found.")
	
	def GetLevelFromId(self, id: int) -> dict:
		for level in self.GameInfo["levels"]:
			if level["id"] == id: return level
		raise ValueError(f"No level with ID {id} found in Manifest.")

	def GetEntityClassFromId(self, id: int) -> dict:
		for entityClass in self.GameInfo["entity_classes"]:
			if entityClass["id"] == id: return entityClass
		raise ValueError(f"No entity class with ID {id} found in Manifest.")

	def AddFile(self, path: str, relativeToRootDir: bool = True):
		realPath = path.replace("\\", "/")
		if relativeToRootDir:
			realPath = os.path.normpath(os.path.join(self.rootPath, path)).replace("\\", "/")
		for asset in self.manifest["assets"]:
			if ("path" in asset and asset["path"] == path) or asset["id"] == path:
				print(f"Asset already in Manifest: '{path}'.")
				return
		conversion = {
			"json": "TEXT",
			"png": "IMAGE",
			"ogg": "SOUND",
			"otf": "FONT",
			"ttf": "FONT",
			"woff": "BINARY"}
		extension = path.split(".")[-1]
		assetType = extension in conversion and conversion[extension] or "BINARY"
		if assetType != "BINARY" and assetType != "FONT":
			asset = {
				"path": path,
				"size": os.path.getsize(realPath),
				"type": assetType,
				"id": path}
		else:
			asset = {
				"size": os.path.getsize(realPath),
				"type": assetType,
				"className": MassReplace(path.replace("assets/", "__ASSET__assets_"), ["-", "."], "_").lower(),
				"id": path}
		self.manifest["assets"].append(asset)
		print(f"Added new Asset to Manifest '{realPath}': {asset}")
		return self.UpdateManifest()

	def RemoveFile(self, path: str, relativeToRootDir: bool = True):
		realPath = path.replace("\\", "/")
		if relativeToRootDir:
			realPath = os.path.normpath(os.path.join(self.rootPath, path)).replace("\\", "/")
		assetFound = None
		for asset in self.manifest["assets"]:
			if ("path" in asset and asset["path"] == path) or asset["id"] == path:
				assetFound = asset
				break
		if assetFound is None:
			print(f"Failed to Remove Asset from Manifest. Asset not in Manifest: '{path}'.")
			return
		self.manifest["assets"].remove(assetFound)
		print(f"Removed Asset from Manifest: '{realPath}'.")
		return self

	def UpdateManifest(self):
		for asset in self.manifest["assets"]:
			path = os.path.join(self.rootPath, "path" in asset and asset["path"] or asset["id"]).replace("\\", "/")
			newSize = os.path.getsize(path)
			if asset["size"] != newSize:
				diff = newSize - asset["size"]
				asset["size"] = newSize
				print(f"Updated Size of '{path}' ({diff > 0 and '+' or '-'}{abs(diff)})")
		return self