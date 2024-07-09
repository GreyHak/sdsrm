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
USER_AGENT = "sdsm/1.0.0"

def getServerState(hostname, port, authorizationCode):
   package = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\n' + 'Content-Type: application/json\r\nContent-Length: 32\r\n\r\n{"function": "QueryServerState"}'

   if ALLOW_SELF_SIGNED_CERTS_FLAG:
      context = ssl._create_unverified_context()
   else:
      context = ssl.create_default_context()

   try:
      sock = socket.create_connection((hostname, port))
   except ConnectionRefusedError:
      return ("Connection refused", None)

   if not sock:
      return ("not sock", None)
   else:
      ssock = context.wrap_socket(sock, server_hostname=hostname)
      if not ssock:
         return ("not ssock", None)
      else:
         ssock.send(package.encode())
         ssock.settimeout(10)
         summary = ""

         try:
            data = ssock.recv(2048)

            if data[:12] == b"HTTP/1.1 403":
               return ("Server error: Forbidden", None)

            elif data[:10] == b"HTTP/1.1 4":
               return (f"Server error {data[9:12].decode()}", None)

            elif data[:12] == b"HTTP/1.1 200":
               dataPos = data.find(b"\r\n\r\n")
               jdata = json.loads(data.decode()[dataPos+4:])
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
            serverStatusValue.set
            return ("Exception", None)

   return ("Connection Error", None)

def setServerName(hostname, port, authorizationCode, newName):

   if not newName:
      return "Please set name"

   package = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\nContent-Type: application/json\r\nContent-Length: {57+len(newName)}\r\n\r\n' + '{"function": "RenameServer", "data":{ "serverName": "' + newName + '" }}'

   if ALLOW_SELF_SIGNED_CERTS_FLAG:
      context = ssl._create_unverified_context()
   else:
      context = ssl.create_default_context()

   try:
      sock = socket.create_connection((hostname, port))
   except ConnectionRefusedError:
      return "Connection refused"

   if not sock:
      return "not sock"
   else:
      ssock = context.wrap_socket(sock, server_hostname=hostname)
      if not ssock:
         return "not ssock"
      else:
         ssock.send(package.encode())
         ssock.settimeout(10)
         summary = ""

         try:
            data = ssock.recv(2048)

            if data[:12] == b"HTTP/1.1 403":
               return "Server error: Forbidden"

            elif data[:10] == b"HTTP/1.1 4":
               return f"Server error {data[9:12].decode()}"

            elif data[:12] == b"HTTP/1.1 204":
               return "Success"
            else:
               print(data)
               return "Server Failure"
         except TimeoutError:
            return "Exception"
   return "Connection Error"

def uploadSave(hostname, port, authorizationCode, filepath, saveName, loadCheckFlag, advancedCheckFlag):

   if not os.path.exists(filepath):
      return "No File"

   fileStats = os.stat(filepath)
   fileSize = fileStats.st_size
   print(f"File is {fileSize} bytes")

   fin = open(filepath, "rb")
   if not fin:
      return "Open Error"

   boundary = random.choices(string.ascii_letters, k=22)
   boundary = "------------------------" + ''.join(boundary)

   filename = os.path.basename(filepath)
   loadCheckFlag = str(loadCheckFlag).lower()
   advancedCheckFlag = str(advancedCheckFlag).lower()

   package2 = f'--{boundary}\r\nContent-Disposition: attachment; name="data"\r\nContent-Type: application/json\r\n\r\n' + '{"function": "UploadSaveGame", "data": {' + f'"saveName": "{saveName}", "loadSaveGame": {loadCheckFlag}, "enableAdvancedGameSettings": {advancedCheckFlag}' + '}}\r\n' + f'--{boundary}\r\nContent-Disposition: attachment; name="saveGameFile"; filename="{filename}"\r\nContent-Type: application/json\r\n\r\n'
   package3 = f'\r\n--{boundary}--\r\n'.encode()

   contentLength = len(package2) + len(package3) + fileSize
   print(f"Estimating {contentLength} bytes.")
   package1 = f'POST /api/v1 HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: {USER_AGENT}\r\nAccept: */*\r\nAuthorization: Bearer {authorizationCode}\r\nContent-Length: {contentLength}\r\nContent-Type: application/json; boundary={boundary}\r\nExpect: 100-continue\r\n\r\n'.encode()

   if ALLOW_SELF_SIGNED_CERTS_FLAG:
      context = ssl._create_unverified_context()
   else:
      context = ssl.create_default_context()

   try:
      sock = socket.create_connection((hostname, port))
   except ConnectionRefusedError:
      return "Connection refused"

   if not sock:
      return "not sock"
   else:
      ssock = context.wrap_socket(sock, server_hostname=hostname)
      if not ssock:
         return "not ssock"
      else:
         try:
            ssock.send(package1)
            ssock.settimeout(10)

            data = ssock.recv(2048)

            if data[:12] == b"HTTP/1.1 403":
               return "Server error: Forbidden"

            elif data[:10] == b"HTTP/1.1 4":
               return f"Server error {data[9:12].decode()}"

            elif data[:12] == b"HTTP/1.1 100":
               ssock.send(package2.encode())
               #totalContentBytesSent = len(package2)

               while fileSize > 0:
                  data = fin.read(min(fileSize, 16384))
                  fileSize -= len(data)
                  if fileSize == 0:
                     data += package3[:20]
                     ssock.send(data)
                     ssock.send(package3[20:])
                     #totalContentBytesSent += len(data) + len(package3[20:])
                  else:
                     ssock.send(data)
                     #totalContentBytesSent += len(data)

               data = ssock.recv(2048)
               if data[:12] == b"HTTP/1.1 204":
                  return "Success"
               else:
                  print(data)
                  return "Upload Failure"

            else:
               print(data)
               return "Auth Failure"
         except ssl.SSLEOFError:  # Seen on ssock.send when server terminated prematurely.
            return "Termination Exception"
         except TimeoutError:
            return "Timout Exception"
   return "Connection Error"
