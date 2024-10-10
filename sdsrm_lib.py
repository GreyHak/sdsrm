# This file is part of the SDSRM distribution (https://github.com/GreyHak/sdsrm).
# Copyright (c) 2024 GreyHak (github.com/GreyHak).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import json
import random
import socket
import ssl
import string

ALLOW_SELF_SIGNED_CERTS_FLAG = True
USER_AGENT = "sdsm/1.1.0"

context = None
sock = None
ssock = None

def connect(hostname, port):
   global context
   global sock
   global ssock

   if ssock != None:
      return True

   if context == None:
      if ALLOW_SELF_SIGNED_CERTS_FLAG:
         context = ssl._create_unverified_context()
      else:
         context = ssl.create_default_context()

   if sock == None:
      try:
         sock = socket.create_connection((hostname, port))
      except ConnectionRefusedError:
         return False

   if not sock:
      return False

   ssock = context.wrap_socket(sock, server_hostname=hostname)
   return True

def authenticate(hostname, port, adminFlag, password):
   if adminFlag:
      minimumPrivilegeLevel = "Administrator"
   else:
      minimumPrivilegeLevel = "Client"

   if password == None or len(password) == 0:
      package = '{"function": "PasswordlessLogin", "data": {"MinimumPrivilegeLevel": "' + minimumPrivilegeLevel + '"}}'
   else:
      package = '{"function": "PasswordLogin", "data": {"MinimumPrivilegeLevel": "' + minimumPrivilegeLevel + '", "Password": "' + password + '"}}'

   package = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nContent-Type: application/json\r\nContent-Length: {len(package)}\r\n\r\n{package}'

   global sock
   global ssock
   for returnFlag in (False, True):
      if not connect(hostname, port):
         return ("Connection Failed", None)

      try:
         print("DEBUG: Authenticating")
         ssock.send(package.encode())
         break
      except ssl.SSLEOFError:
         print("Reconnecting because socket has closed")
         sock = None
         ssock = None
         if returnFlag:
            return ("Bad Sock", None)

   ssock.settimeout(10)

   try:
      data = ssock.recv(2048)

      if data[:12] == b"HTTP/1.1 403":
         return ("Server error: Forbidden", None)

      elif data[:10] == b"HTTP/1.1 4":
         return (f"Server error {data[9:12].decode()}", None)

      elif data[:12] == b"HTTP/1.1 200":
         data = ssock.recv(2048)
         try:
            data = json.loads(data.decode())
         except json.decoder.JSONDecodeError:
            print(f"JSON decode failed: '{data}'")
            return ("JSON decode error", None)
         if "errorCode" in data:
            if "errorMessage" in data:
               return (f"{data['errorCode']}: {data['errorMessage']}", None)
            else:
               return (data["errorCode"], None)
         if "data" not in data:
            return ("Missing data", None)
         if "authenticationToken" not in data["data"]:
            return ("Missing token", None)
         return ("Success", data["data"]["authenticationToken"])

      else:
         print(f"Unsupported returned data from server: '{data}'")
         return ("Server Failure", None)
   except TimeoutError:
      return ("Timed Out", None)

def verifyAuthentication(hostname, port, authorizationCode):
   package = '{"function": "VerifyAuthenticationToken"}'
   package = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\nContent-Type: application/json\r\nContent-Length: {len(package)}\r\n\r\n{package}'

   global sock
   global ssock
   for returnFlag in (False, True):
      if not connect(hostname, port):
         return ("Connection Failed", None)

      try:
         print("DEBUG: Verifying Authentication")
         ssock.send(package.encode())
         break
      except ssl.SSLEOFError:
         print("Reconnecting because socket has closed")
         sock = None
         ssock = None
         if returnFlag:
            return ("Bad Sock", False)

   ssock.settimeout(10)

   try:
      data = ssock.recv(2048)
   except TimeoutError:
      return ("Timed Out", False)

   if data[:12] == b"HTTP/1.1 401":
      return ("Auth Failure", False)

   if data[:10] == b"HTTP/1.1 4":
      return (f"Server error {data[9:12].decode()}", False)

   if data[:12] == b"HTTP/1.1 204":
      return ("Success", True)

   print(f"Unsupported returned data from server: '{data}'")
   return ("Server Failure", False)

def getServerState(hostname, port, authorizationCode):
   package = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\n' + 'Content-Type: application/json\r\nContent-Length: 32\r\n\r\n{"function": "QueryServerState"}'

   global sock
   global ssock
   for returnFlag in (False, True):
      if not connect(hostname, port):
         return ("Connection Failed", None)

      try:
         ssock.send(package.encode())
         break
      except ssl.SSLEOFError:
         print("Reconnecting because socket has closed")
         sock = None
         ssock = None
         if returnFlag:
            return ("Bad Sock", None)

   ssock.settimeout(10)
   summary = ""

   try:
      data = ssock.recv(2048)

      if data[:12] == b"HTTP/1.1 403":
         return ("Server error: Forbidden", None)

      elif data[:10] == b"HTTP/1.1 4":
         return (f"Server error {data[9:12].decode()}", None)

      elif data[:12] == b"HTTP/1.1 200":
         data = ssock.recv(2048)
         try:
            jdata = json.loads(data.decode())
         except json.decoder.JSONDecodeError:
            print(f"JSON decode failed: '{data}'")
            return ("JSON decode error", None)
         if "data" in jdata:
            if "serverGameState" in jdata["data"]:
               serverGameState = jdata["data"]["serverGameState"]
               if "activeSessionName" in serverGameState:
                  activeSessionName = serverGameState["activeSessionName"]
                  summary += f"Active Session Name: {activeSessionName}\n"
               if "numConnectedPlayers" in serverGameState:
                  numConnectedPlayers = serverGameState["numConnectedPlayers"]
                  summary += f"Number of Connected Players: {numConnectedPlayers}\n"
               if "techTier" in serverGameState:
                  techTier = serverGameState["techTier"]
                  summary += f"Tech Tier: {techTier}\n"
               if "activeSchematic" in serverGameState:
                  activeSchematic = serverGameState["activeSchematic"]
                  summary += f"Active Schematic: {activeSchematic}\n"
               if "gamePhase" in serverGameState:
                  gamePhase = serverGameState["gamePhase"]
                  GAME_PHASE_NAMES = {
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_0.GP_Project_Assembly_Phase_0'": "Onboarding",
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_1.GP_Project_Assembly_Phase_1'": "Distribution Platform",
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_2.GP_Project_Assembly_Phase_2'": "Construction Dock",
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_3.GP_Project_Assembly_Phase_3'": "Main Body",
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_4.GP_Project_Assembly_Phase_4'": "Propulsion Systems",
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_5.GP_Project_Assembly_Phase_5'": "Assembly",
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_6.GP_Project_Assembly_Phase_6'": "Completing",
                     "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_7.GP_Project_Assembly_Phase_7'": "Completed",
                     }
                  if gamePhase in GAME_PHASE_NAMES:
                     gamePhase = GAME_PHASE_NAMES[gamePhase]
                  summary += f"Game Phase: {gamePhase}\n"
               if "isGameRunning" in serverGameState:
                  isGameRunning = serverGameState["isGameRunning"]
                  if isGameRunning:
                     summary += f"Game Is Running\n"
                  else:
                     summary += f"Game Not Running\n"
               if "totalGameDuration" in serverGameState:
                  totalGameDuration = serverGameState["totalGameDuration"]
                  summary += f"Total Game Duration: {totalGameDuration}\n"
               if "isGamePaused" in serverGameState:
                  isGamePaused = serverGameState["isGamePaused"]
                  if isGamePaused:
                     summary += f"Game Is Paused\n"
                  else:
                     summary += f"Game Not Paused\n"
               if "averageTickRate" in serverGameState:
                  averageTickRate = serverGameState["averageTickRate"]
                  summary += f"Average Tick Rate: {averageTickRate}\n"
               if "autoLoadSessionName" in serverGameState:
                  autoLoadSessionName = serverGameState["autoLoadSessionName"]
                  summary += f"Auto Load Session Name: {autoLoadSessionName}\n"
               if len(summary) > 0:
                  summary = summary[:-1]
      return ("Success", summary)
   except TimeoutError:
      return ("Timed Out", None)


def setServerName(hostname, port, authorizationCode, newName):

   if not newName:
      return "Please set name"

   package = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\nContent-Type: application/json\r\nContent-Length: {57+len(newName)}\r\n\r\n' + '{"function": "RenameServer", "data":{ "serverName": "' + newName + '" }}'

   global sock
   global ssock
   for returnFlag in (False, True):
      if not connect(hostname, port):
         return ("Connection Failed", None)

      try:
         ssock.send(package.encode())
         break
      except ssl.SSLEOFError:
         print("Reconnecting because socket has closed")
         sock = None
         ssock = None
         if returnFlag:
            return ("Bad Sock", None)

   ssock.settimeout(10)

   try:
      data = ssock.recv(2048)

      if data[:12] == b"HTTP/1.1 403":
         return "Server error: Forbidden"

      elif data[:10] == b"HTTP/1.1 4":
         return f"Server error {data[9:12].decode()}"

      elif data[:12] == b"HTTP/1.1 204":
         return "Success"
      else:
         print(f"Unsupported returned data from server: '{data}'")
         return "Server Failure"
   except TimeoutError:
      return "Timed Out"

# curl https://localhost:7777/api/v1 --insecure -v -H "Authorization: Bearer WXYZ" -H "Content-Type: multipart/form-data" -F data="{\"function\": \"UploadSaveGame\", \"data\": {\"saveName\": \"New Save Game\", \"loadSaveGame\": false, \"enableAdvancedGameSettings\": false}}";type=application/json -F saveGameFile=@upload.sav
def uploadSave(hostname, port, authorizationCode, filepath, saveName, loadCheckFlag, advancedCheckFlag):

   if not os.path.exists(filepath):
      return "No File"

   fileStats = os.stat(filepath)
   fileSize = fileStats.st_size

   fin = open(filepath, "rb")
   if not fin:
      return "Open Error"

   boundary = random.choices(string.ascii_letters, k=22)
   boundary = "------------------------" + ''.join(boundary)

   filename = os.path.basename(filepath)
   loadCheckFlag = str(loadCheckFlag).lower()
   advancedCheckFlag = str(advancedCheckFlag).lower()

   package2 = f'--{boundary}\r\nContent-Disposition: form-data; name="data"\r\nContent-Type: application/json\r\n\r\n' + '{"function": "UploadSaveGame", "data": {' + f'"saveName": "{saveName}", "loadSaveGame": {loadCheckFlag}, "enableAdvancedGameSettings": {advancedCheckFlag}' + '}}\r\n' + f'--{boundary}\r\nContent-Disposition: form-data; name="saveGameFile"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'
   package3 = f'\r\n--{boundary}--\r\n'.encode()

   contentLength = len(package2) + len(package3) + fileSize
   package1 = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\nContent-Length: {contentLength}\r\nContent-Type: multipart/form-data; boundary={boundary}\r\nExpect: 100-continue\r\n\r\n'.encode()

   global sock
   global ssock
   for returnFlag in (False, True):
      if not connect(hostname, port):
         return "Connection Failed"

      try:
         ssock.send(package1)
         break
      except ssl.SSLEOFError:
         print("Reconnecting because socket has closed")
         sock = None
         ssock = None
         if returnFlag:
            return "Bad Sock"

   try:
      ssock.send(package2.encode())

      print(f"Sending file of size {fileSize} bytes")
      while fileSize > 0:
         data = fin.read(min(fileSize, 16384))
         fileSize -= len(data)
         if fileSize == 0:
            data += package3[:20]
            ssock.send(data)
            ssock.send(package3[20:])
         else:
            ssock.send(data)

      data = ssock.recv(2048)
      if data[:12] == b"HTTP/1.1 202": # Uploaded and Loading
         return "Success"
      elif data[:12] == b"HTTP/1.1 201": # Uploaded only
         return "Success"
      # 204 is considered a success on the server.
      # 204 is being considered an error here because it likely means
      # the save by the specified name already exists on the server
      # and WAS NOT replaced by the upload file.
      elif data[:12] == b"HTTP/1.1 204":
         return "Save Already Exists"
      else:
         print(f"Unsupported returned data from server: '{data}'")
         return f"Upload Failure {data[9:12].decode()}"

   except (ssl.SSLEOFError, ssl.SSLZeroReturnError):  # Seen on ssock.send when server terminated prematurely.
      return "Termination Exception"
   except TimeoutError:
      return "Timed Out"

def shutdown(hostname, port, authorizationCode):
   package = '{"function": "Shutdown"}'
   package = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\nContent-Type: application/json\r\nContent-Length: {len(package)}\r\n\r\n{package}'

   global sock
   global ssock
   for returnFlag in (False, True):
      if not connect(hostname, port):
         return "Connection Failed"

      try:
         print("DEBUG: Verifying Authentication")
         ssock.send(package.encode())
         break
      except ssl.SSLEOFError:
         print("Reconnecting because socket has closed")
         sock = None
         ssock = None
         if returnFlag:
            return "Bad Sock"

   ssock.settimeout(10)

   try:
      data = ssock.recv(2048)
   except TimeoutError:
      return "Timed Out"

   if data[:12] == b"HTTP/1.1 401":
      return "Auth Failure"

   if data[:10] == b"HTTP/1.1 4":
      return f"Server error {data[9:12].decode()}"

   if data[:12] == b"HTTP/1.1 204":
      return "Success"

   print(f"Unsupported returned data from server: '{data}'")
   return "Server Failure"
