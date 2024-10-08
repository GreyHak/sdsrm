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

import sdsrm_lib
import tkinter as tk
from tkinter import font
from tkinter.filedialog import askopenfilename
import json

DEFAULT_SERVER_ADDRESS = "127.0.0.1"
DEFAULT_SERVER_PORT = "7777"
authorizationInfo = None

SERVER_CONFIG_FILENAME = "ServerConfig.json"

def saveServerConfig(hostname, port, password):
   with open(SERVER_CONFIG_FILENAME, "w") as fout:
      json.dump({"Host": hostname, "Port": port, "Password": password}, fout)

def loadServerConfig():
   hostname = DEFAULT_SERVER_ADDRESS
   port = DEFAULT_SERVER_PORT
   password = None
   try:
      with open(SERVER_CONFIG_FILENAME, "r") as fin:
         jdata = json.load(fin)
         if "Host" in jdata:
            hostname = jdata["Host"]
         if "Port" in jdata:
            port = jdata["Port"]
         if "Password" in jdata:
            password = jdata["Password"]
   except: # FileNotFoundError
      pass
   return (hostname, port, password)

def getServerDetails():
   hostname = serverIpEntry.get()
   port = int(serverPortEntry.get())
   password = serverPasswordEntry.get()
   return ((hostname, port), password)

def authenticated():
   global authorizationInfo

   ((hostname, port), password) = getServerDetails()

   if authorizationInfo != None:
      (adminFlag, authorizationCode) = authorizationInfo
      (authVerResultStr, authVerResult) = sdsrm_lib.verifyAuthentication(hostname, port, authorizationCode)
      if authVerResult == None:
         print("Authentication code rejected")
         authorizationInfo = None

   if authorizationInfo == None:
      adminFlag = False
      (authStatus, authCode) = sdsrm_lib.authenticate(hostname, port, adminFlag, password)
      if authCode == None:
         print("Login failed")
         serverStatusValue.set(authStatus)
         return
      authorizationInfo = (adminFlag, authCode)
      saveServerConfig(hostname, port, password)
      print("Login successful")

   return authorizationInfo != None

def onGetServerState():
   global authorizationInfo
   serverStatusValue.set("Initiated")

   if not authenticated():
      serverStatusValue.set("Auth Failure")
      return
   (adminFlag, authorizationCode) = authorizationInfo
   ((hostname, port), password) = getServerDetails()

   print(f"\ngetServerState({hostname}:{port})")
   (getStatus, serverStatus) = sdsrm_lib.getServerState(hostname, port, authorizationCode)
   print(f"getServerState returned: {getStatus}, len {len(serverStatus)}")

   if serverStatus != None:
      serverStatusValue.set(serverStatus)
   else:
      authorizationInfo = None
      serverStatusValue.set(getStatus)

def onSetServerName():
   global authorizationInfo
   setServerNameStatusValue.set("Initiated")

   if not authenticated():
      setServerNameStatusValue.set("Auth Failure")
      return
   (adminFlag, authorizationCode) = authorizationInfo
   ((hostname, port), password) = getServerDetails()

   newName = setServerNameEntry.get()
   print(f"\nsetServerName({hostname}:{port}, {newName})")
   setStatus = sdsrm_lib.setServerName(hostname, port, authorizationCode, newName)
   print(f"setServerName returned: {setStatus}")

   setServerNameStatusValue.set(setStatus)

def onBrowseSave():
   filepath = askopenfilename(filetypes=[("Satisfactory Save Files", "*.sav"), ("All Files", "*.*")])
   print(filepath)
   savePathValue.set(filepath)

def onUploadSave():
   global authorizationInfo
   uploadSaveStatusValue.set("Initiated")

   if not authenticated():
      uploadSaveStatusValue.set("Auth Failure")
      return
   (adminFlag, authorizationCode) = authorizationInfo
   ((hostname, port), password) = getServerDetails()

   filepath = savePathValue.get()
   saveName = saveNameEntry.get()
   loadCheckFlag = loadCheck.get()
   advancedCheckFlag = advancedCheck.get()

   print(f"\nuploadSave({hostname}:{port}, {filepath}, {saveName}, {loadCheckFlag}, {advancedCheckFlag})")
   uploadStatus = sdsrm_lib.uploadSave(hostname, port, authorizationCode, filepath, saveName, loadCheckFlag, advancedCheckFlag)
   print(f"uploadSave returned: {uploadStatus}")

   uploadSaveStatusValue.set(uploadStatus)

if __name__ == '__main__':

   (hostname, port, password) = loadServerConfig()

   pady = 8
   myLabelColor = "gray90"  # Dynamic, not-editable text
   myRowColor = "#575757"
   myRowTextColor = "white"
   myOtherRowColor = "#3f3f3f"
   myOtherRowTextColor = "white"

   # https://www.studytonight.com/tkinter/python-tkinter-label-widget
   window = tk.Tk()
   window.title("SDSRM: Satisfactory Dedicated Server Remote Manager by GreyHak")
   window.resizable(False, False)
   window.configure(background=myRowColor)

   defaultFont = font.nametofont('TkTextFont').actual()
   defaultFontFamily = defaultFont["family"]
   myNormalFont = (defaultFontFamily, 20)
   mySmallFont = (defaultFontFamily, 16)

   photo = tk.PhotoImage(file="sdsrm_logo.gif")
   tk.Label(image=photo, bg=myRowColor).pack()

   frame1 = tk.Frame(pady=pady, padx=31, bg=myOtherRowColor)
   frame1.pack()
   tk.Label(frame1, font=myNormalFont, bg=myOtherRowColor, fg=myOtherRowTextColor, text="Server IP Address/Port:").pack(side=tk.LEFT)
   serverIpEntry = tk.Entry(frame1, font=myNormalFont, width=20, textvariable=tk.StringVar(window, hostname))
   serverIpEntry.pack(side=tk.LEFT)
   serverPortEntry = tk.Entry(frame1, font=myNormalFont, width=6, textvariable=tk.StringVar(window, port))
   serverPortEntry.pack(side=tk.LEFT)
   tk.Label(frame1, bg=myOtherRowColor, width=10).pack(side=tk.LEFT)
   tk.Label(frame1, font=myNormalFont, bg=myOtherRowColor, fg=myOtherRowTextColor, text="Password:").pack(side=tk.LEFT)
   serverPasswordEntry = tk.Entry(frame1, font=myNormalFont, width=40, show="*", textvariable=tk.StringVar(window, (password, "")[password == None]))
   serverPasswordEntry.pack(side=tk.LEFT)

   frame2 = tk.Frame(pady=pady, bg=myRowColor)
   frame2.pack()
   tk.Button(frame2, font=myNormalFont, bg=myRowColor, fg=myRowTextColor, text="Get Server State", command=onGetServerState).pack(side=tk.LEFT)
   serverStatusValue = tk.StringVar(window, "Server state unknown.  Please click 'Get Server State'.")
   serverStatusLabel = tk.Label(frame2, font=mySmallFont, bg=myLabelColor, width=120, height=10, textvariable=serverStatusValue)
   serverStatusLabel.pack(side=tk.LEFT)

   frame3 = tk.Frame(pady=pady, padx=129, bg=myOtherRowColor)
   frame3.pack()
   tk.Label(frame3, font=myNormalFont, bg=myOtherRowColor, fg=myOtherRowTextColor, text="New Server Name:").pack(side=tk.LEFT)
   tk.Label(frame3, bg=myOtherRowColor, width=1).pack(side=tk.LEFT)
   setServerNameEntry = tk.Entry(frame3, font=myNormalFont, width=40)
   setServerNameEntry.pack(side=tk.LEFT)
   tk.Label(frame3, bg=myOtherRowColor, width=4).pack(side=tk.LEFT)
   tk.Button(frame3, font=myNormalFont, bg=myOtherRowColor, fg=myOtherRowTextColor, text="Set Server Name", command=onSetServerName).pack(side=tk.LEFT)
   setServerNameStatusValue = tk.StringVar(window, "<>")
   setServerNameStatusLabel = tk.Label(frame3, font=myNormalFont, bg=myLabelColor, width=20, textvariable=setServerNameStatusValue)
   setServerNameStatusLabel.pack(side=tk.LEFT)

   frame4 = tk.Frame(pady=pady, padx=1, bg=myRowColor)
   frame4.pack()

   frame4a = tk.Frame(frame4, bg=myRowColor)
   frame4a.pack()
   tk.Button(frame4a, font=myNormalFont, bg=myRowColor, fg=myRowTextColor, text="Browse for Save", command=onBrowseSave).pack(side=tk.LEFT)
   savePathValue = tk.StringVar(window, "Please browse for save file.")
   savePathLabel = tk.Label(frame4a, font=mySmallFont, bg=myLabelColor, wraplength=93*12, width=93, textvariable=savePathValue)
   savePathLabel.pack(side=tk.LEFT)
   tk.Label(frame4a, bg=myRowColor, width=4).pack(side=tk.LEFT)
   loadCheck = tk.BooleanVar(window, False)
   tk.Checkbutton(frame4a, font=myNormalFont, bg=myRowColor, fg=myRowTextColor, activebackground=myRowColor, activeforeground=myRowTextColor, highlightbackground=myRowColor, selectcolor=myRowColor, text="Load Save on Upload", variable=loadCheck).pack(side=tk.LEFT)

   frame4b = tk.Frame(frame4, bg=myRowColor)
   frame4b.pack()
   tk.Label(frame4b, font=myNormalFont, bg=myRowColor, fg=myRowTextColor, text="Save Name:").pack(side=tk.LEFT)
   saveNameEntry = tk.Entry(frame4b, font=myNormalFont, width=27, textvariable=tk.StringVar(window, "New Save Game"))
   saveNameEntry.pack(side=tk.LEFT)
   tk.Label(frame4b, bg=myRowColor, width=4).pack(side=tk.LEFT)
   advancedCheck = tk.BooleanVar(window, False)
   tk.Checkbutton(frame4b, font=myNormalFont, bg=myRowColor, fg=myRowTextColor, activebackground=myRowColor, activeforeground=myRowTextColor, highlightbackground=myRowColor, selectcolor=myRowColor, text="Enable Advanced Game Settings on Upload", variable=advancedCheck).pack(side=tk.LEFT)
   tk.Label(frame4b, bg=myRowColor, width=4).pack(side=tk.LEFT)
   tk.Button(frame4b, font=myNormalFont, bg=myRowColor, fg=myRowTextColor, text="Upload Save", height=0, command=onUploadSave).pack(side=tk.LEFT)
   uploadSaveStatusValue = tk.StringVar(window, "<>")
   uploadSaveStatusLabel = tk.Label(frame4b, font=myNormalFont, bg=myLabelColor, width=20, textvariable=uploadSaveStatusValue)
   uploadSaveStatusLabel.pack(side=tk.LEFT)

   window.mainloop()
