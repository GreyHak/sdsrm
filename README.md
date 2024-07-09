# SDSRM: Satisfactory Dedicated Server Remote Manager by GreyHak
> **Note:** This remote server manager is for Satisfactory 1.0 which will be
> released on September 10, 2024.  This remote server manager will not work
> with Update 8.

This is a remote server manager for Satisfactory 1.0's Dedicated Server which
implements the server's HTTPS API.

[Satisfactory](https://www.satisfactorygame.com/) is an non-competitive,
first-person, open-world, factory-building and exploration game produced by
[Coffee Stain Studios](https://www.coffeestain.com/).

Satisfactory Dedicated Server's API documentation has not yet been released.
This API implementation is based on the information Coffee Stain Studios
released in their YouTube video
[Dedicated Servers have LEVELED UP!](https://www.youtube.com/watch?v=v8piXNQwcUw&t=471s).
Since this information is currently limited, this implementation is also
limited.

Currently supported features:
 - Get Server Status
 - Set Server Name
 - Upload Save
	 - Load save on upload
	 - Enable advanced game settings on upload

This server manager works on **Windows** and **Linux**.  It requires
**Python3**.  It has been tested with Python 3.7+ on Windows 11 and Ubuntu
22.04.3 LTS.  On Linux it requires python3 with tkinter which is not installed
in the minimal python3 install.  To install python3 with tkinter on
Ubuntu/Debian, run `sudo apt install python3-tk` or the variant for your
version of python such as `sudo apt install python3.13-tk`.

![Screenshot](screenshot.png)

## SDSRM Remote Server Manager GUI

On Windows, double-click sdsrm_gui.py or run `py sdsrm_gui.py` from the
command line.

On Linux, run `python3 sdsrm_gui.py` or the variant for your version of python
such as `python3.13 sdsrm_gui.py`.

## SDSRM Remote Server Manager Library

If you would like to integrate SDSRM into your own project, SDSRM's interface
to the Satisfactory's Dedicated Server API is separate from SDSRM's GUI.  Copy
*sdsrm_lib.py* into your project and import it `import sdsrm_lib`.

This library provides the following interfaces:
 - (getStatus, serverStatus) = sdsrm_lib.getServerState(hostname, port, authorizationCode)
 - setStatus = sdsrm_lib.setServerName(hostname, port, authorizationCode, newName)
 - uploadStatus = sdsrm_lib.uploadSave(hostname, port, authorizationCode, filepath, saveName, loadCheckFlag, advancedCheckFlag)

## Credits
 - Credit to [Nate Wren](https://natewren.com/satisfontory/) for the font used
in the SDSRM logo.
 - Thanks to [textstudio.com](https://www.textstudio.com/logo/gradient-color-text-137)
for generation of the SDSRM logo.
