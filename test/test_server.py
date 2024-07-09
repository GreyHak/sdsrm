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

import socket
import ssl
import json
import time

AUTHORIZATION_CODE = b"pAAGskAG7aotFqpiI6vivswwphnU"

def parseHeaders(request):
   headers = []
   nextStart = 0
   data = None
   while True:
      eol = request.find(b"\r\n", nextStart)
      if eol == -1:
         break
      if eol == nextStart:
         data = request[eol + 2:]
         break
      headers.append(request[nextStart:eol])
      nextStart = eol + 2
   return (headers, data)

RECV_SIZE = 1048576 # curl sends it through as 16384 bytes

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

# openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem -subj "/C=US"
context.load_cert_chain('cert.pem')

ERROR_MESSAGE_400 = b"HTTP/1.1 400\r\nServer: FactoryGame/++FactoryGame+dev-CL-332077 (Windows)\r\nkeep-alive: timeout=15.000000\r\ncontent-length: 0\r\n\r\n"
ERROR_MESSAGE_403 = b"HTTP/1.1 403\r\nServer: FactoryGame/++FactoryGame+dev-CL-332077 (Windows)\r\nkeep-alive: timeout=15.000000\r\ncontent-length: 0\r\n\r\n"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
   s.bind(("127.0.0.1", 7777))
   s.listen()
   print("Successfully Started Satisfactory API Test Server")
   with context.wrap_socket(s, server_side=True) as ssock:
      while True:
         try:
            conn, addr = ssock.accept()
            print(f"Connected by {addr}")
            while True:
               request = conn.recv(RECV_SIZE)

               if not request:
                  print("ERROR: Empty request")
                  conn.sendall(ERROR_MESSAGE_400)
                  conn.close()
                  break
               print(f"bytes(request)={request}")

               print(f"str(request)={request.decode()}")
               (headers, data) = parseHeaders(request)
               totalContentBytesReceived = len(data)

               print(f"headers={headers}")
               if len(headers) == 0:
                  print("ERROR: No headers.")
                  conn.sendall(ERROR_MESSAGE_400)
                  conn.close()
                  break
               if headers[0] != b"POST /api/v1 HTTP/1.1":
                  print("ERROR: Server only supports POST to for the v1 API.")
                  conn.sendall(ERROR_MESSAGE_400)
                  conn.close()
                  break

               contentTypeJsonFlag = False
               contentTypeBoundary = None
               for header in headers:
                  lowerHeader = header.lower()
                  if lowerHeader[:14] == b"content-type: ":
                     if lowerHeader[14:30] == b"application/json":
                        contentTypeJsonFlag = True
                        if lowerHeader[30:41] == b"; boundary=":
                           contentTypeBoundary = header[41:]

               if not contentTypeJsonFlag:
                  print("ERROR: Test server is assuming that the real server requires the header 'Content-Type: application/json' as demonstrated.")
                  conn.sendall(ERROR_MESSAGE_400)
                  conn.close()
                  break

               authorizationCode = None
               contentLength = None
               for header in headers:
                  if b"authorization: bearer " in header.lower():
                     authorizationCode = header[22:]
                  if header[:16].lower() == b"content-length: ":
                     contentLength = int(header[16:])
               if authorizationCode != AUTHORIZATION_CODE:
                  print("Failed authenication")
                  conn.sendall(ERROR_MESSAGE_403)
                  conn.close()
                  break

               continue100Flag = b"expect: 100-continue" in (header.lower() for header in headers)
               if continue100Flag:
                  print("100 Continue")
                  conn.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")
                  data = conn.recv(RECV_SIZE)
                  totalContentBytesReceived += len(data)

               if data == None:
                  print("ERROR: No data")
                  conn.sendall(ERROR_MESSAGE_400)
                  conn.close()
                  break

               print("=====DATA START=====")
               print(data)
               print("======DATA END======")

               if contentTypeBoundary != None:
                  contentTypeBoundary = b"--" + contentTypeBoundary
                  if data[:len(contentTypeBoundary)+2] != contentTypeBoundary + b"\r\n":
                     print(f"ERROR: Boundary'ed data doesn't start with boundary string {contentTypeBoundary}.")
                     conn.sendall(ERROR_MESSAGE_400)
                     conn.close()
                     break

                  components = []
                  nextStart = len(contentTypeBoundary)
                  while data[nextStart:nextStart+2] == b"\r\n":  # Stop will be "--"
                     nextStart += 2
                     eol = data.find(contentTypeBoundary, nextStart)
                     if eol == -1:
                        components.append(data[nextStart:])
                        break
                     components.append(data[nextStart:eol-2])
                     nextStart = eol + len(contentTypeBoundary)

                  for componentIdx in range(len(components)):
                     print(f"=====COMPONENT {componentIdx} START=====")
                     print(components[componentIdx])
                     print(f"======COMPONENT {componentIdx} END======")

                  (componentHeaders, data) = parseHeaders(components[0])

               print("Parsing JSON...")
               jdata = json.loads(data.decode())
               if "function" in jdata:
                  function = jdata["function"]
                  print(f"function={function}")

                  VALID_FUNCTIONS = ("QueryServerState", "RenameServer", "UploadSaveGame")

                  if function not in VALID_FUNCTIONS:
                     print(f"ERROR: Unknown function '{function}'")
                     conn.sendall(ERROR_MESSAGE_400)
                     conn.close()
                     break

                  print(f"Responding to {function}")

                  if function == "QueryServerState":
                     responseJson = '{"data":{"serverGameState":{"activeSessionName":"PIE209","numConnectedPlayers":0,"techTier":2,"activeSchematic":"None","gamePhase":"/Script/FactoryGame.FGGamePhase\'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_0.GP_Project_Assembly_Phase_0\'","isGameRunning":true,"totalGameDuration":2176,"isGamePaused":true,"averageTickRate":30.286127090454102,"autoLoadSessionName":"PIE209"}}}'
                     conn.sendall(str.encode(f'HTTP/1.1 200\r\nServer: FactoryGame/++FactoryGame+dev-CL-332077 (Windows)\r\nkeep-alive: timeout=15.000000\r\ncontent-length: {len(responseJson)}\r\n\r\n{responseJson}'))
                     print("Success")
                  elif function == "RenameServer":
                     if "data" in jdata and "serverName" in jdata["data"]:
                        newServerName = jdata["data"]["serverName"]
                        print(f"New server name '{newServerName}'")
                        conn.sendall(b"HTTP/1.1 204\r\nServer: FactoryGame/++FactoryGame+dev-CL-332077 (Windows)\r\nkeep-alive: timeout=15.000000\r\ncontent-length: 0\r\n\r\n")
                        print("Success")
                     else:
                        print("ERROR: Improperly formatted RenameServer function")
                        conn.sendall(ERROR_MESSAGE_400)
                  elif function == "UploadSaveGame":
                     if contentTypeBoundary == None:
                        print("ERROR: Improperly formatted RenameServer function")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif len(components) != 2:
                        print("ERROR: UploadSaveGame doesn't have two components")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif len(componentHeaders) != 2:
                        print("ERROR: UploadSaveGame secondary header count unexpected")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif componentHeaders[0].lower() != b'content-disposition: attachment; name="data"':
                        print("ERROR: UploadSaveGame secondary header's first header unexpected")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif componentHeaders[1].lower() != b"content-type: application/json":
                        print("ERROR: UploadSaveGame secondary header's second header unexpected")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif "data" not in jdata:
                        print("ERROR: UploadSaveGame command component missing data")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif "saveName" not in jdata["data"]:
                        print("ERROR: UploadSaveGame command component data missing saveName")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif "loadSaveGame" not in jdata["data"]:
                        print("ERROR: UploadSaveGame command component data missing loadSaveGame")
                        conn.sendall(ERROR_MESSAGE_400)
                     elif "enableAdvancedGameSettings" not in jdata["data"]:
                        print("ERROR: UploadSaveGame command component data missing enableAdvancedGameSettings")
                        conn.sendall(ERROR_MESSAGE_400)
                     else:
                        saveName = jdata["data"]["saveName"]
                        loadSaveGame = jdata["data"]["loadSaveGame"]
                        enableAdvancedGameSettings = jdata["data"]["enableAdvancedGameSettings"]
                        expectedFirstHeader = b'Content-Disposition: attachment; name="saveGameFile"; filename="'

                        (componentHeaders, data) = parseHeaders(components[1])
                        if len(componentHeaders) < 1:
                           print("ERROR: UploadSaveGame third header count insufficient")
                           conn.sendall(ERROR_MESSAGE_400)
                        elif componentHeaders[0][:len(expectedFirstHeader)] != expectedFirstHeader:
                           print(f"ERROR: UploadSaveGame third header missing content-disposition: {componentHeaders[0]}")
                           conn.sendall(ERROR_MESSAGE_400)
                        elif componentHeaders[0][-1:] != b'"':
                           print(f"ERROR: UploadSaveGame third header bad content-disposition: {componentHeaders[0]}")
                           conn.sendall(ERROR_MESSAGE_400)
                        else:
                           filename = componentHeaders[0][len(expectedFirstHeader):-1]
                           print(f"Loading save game saveName={saveName}, loadSaveGame={loadSaveGame}, enableAdvancedGameSettings={enableAdvancedGameSettings}, filename={filename}")
                           with open("out.txt", "wb") as fout:
                              if continue100Flag:
                                 dataEnd = -1
                                 contentTypeBoundary = b"\r\n" + contentTypeBoundary + b"--\r\n"
                                 print(f"Searching for {contentTypeBoundary}")
                                 while dataEnd == -1:
                                    # Intentionally not writing as we go to more easily handle having
                                    # the boundary separator cross between the last two SSL "packets".
                                    startSearch = max(0, len(data)-len(contentTypeBoundary))
                                    moreData = conn.recv(RECV_SIZE)
                                    totalContentBytesReceived += len(moreData)
                                    data += moreData
                                    dataEnd = data.find(contentTypeBoundary, startSearch)
                                    if dataEnd != -1:
                                       print("Trimming data to boundary end")
                                       data = data[:dataEnd]
                              fout.write(data)

                           conn.sendall(b"HTTP/1.1 204\r\nServer: FactoryGame/++FactoryGame+dev-CL-332077 (Windows)\r\nkeep-alive: timeout=15.000000\r\ncontent-length: 0\r\n\r\n")

                           print(f"Success wrote {len(data)}-byte file for save game saveName={saveName}, loadSaveGame={loadSaveGame}, enableAdvancedGameSettings={enableAdvancedGameSettings}, filename={filename}")

                  else:
                     print(f"ERROR: Coding error: Missing case for function '{function}'")
                     conn.sendall(ERROR_MESSAGE_400)

                  if contentLength == None:
                     print(f"Received {totalContentBytesReceived} content bytes.")
                  elif totalContentBytesReceived == contentLength:
                     print(f"Received {totalContentBytesReceived} content bytes, matching specified Content-Length.")
                  elif totalContentBytesReceived > contentLength:
                     print(f"Received {totalContentBytesReceived} content bytes, off from the specified Content-Length by +{totalContentBytesReceived - contentLength} bytes.")
                  elif totalContentBytesReceived < contentLength:
                     print(f"Received {totalContentBytesReceived} content bytes, off from the specified Content-Length by {totalContentBytesReceived - contentLength} bytes.")

                  conn.close()
                  break

         except ssl.SSLError as error:
            print(f"ssl.SSLError: {error}")
