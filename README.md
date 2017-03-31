# conv2mp4-py
Pythonl script that recursively searches through a user-defined file path and convert all videos of user-specified  file types to MP4 with H264 video and AAC audio as needed using ffmpeg. If a conversion failure is detected, the script re-encodes the file with HandbrakeCLI. Upon successful encoding, Plex libraries are refreshed and source file is deleted.  The purpose of this script is to reduce the amount of transcoding CPU load on a Plex server and increase video compatibility across platforms.<br><br>
PowerShell version can be found here: <a href="https://github.com/BrianDMG/conv2mp4-ps">conv2mp4-ps</a><br><br>
<b><u>Dependencies</u></b><br>
This script requires Python 2.7+, ffmpeg, ffprobe (included with ffmpeg), and Handbrake (HandbrakeCLI.exe) to be installed. You can download them from here:<br>
<a href="https://www.python.org/downloads/">Python 2.7+</a><br>
<a href="https://ffmpeg.org/download.html">ffmpeg</a><br>
<a href="https://handbrake.fr/downloads.php">Handbrake</a><br><br>
<b>Usage</b><br>
Run this script the same way you would run any other Python script on your system.<br><br>
<b>User-defined variables</b><br>
There are several user-defined variables you will need to edit using notepad or a program like <a href="https://notepad-plus-plus.org/download/v6.9.2.html">Notepad++</a>.<br><br>
<b>media_path</b> = the path to the media you want to convert<br>
<b>file_types</b> = the extensions of the files you want to convert in the format "*.ex1", "*.ex2"<br>
<b>log_path</b> = path you want the log file to save to.<br>
<b>log_name</b> = the filename of the log file
<b>plex_ip</b> = the IP address and port of your Plex server (for the purpose of refreshing its libraries)<br>
<b>plex_token</b> = your Plex server's token (for the purpose of refreshing its libraries).<br>
<i>NOTE: See https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token<br>
Plex server token is also easy to retrieve with PlexPy, Ombi, Couchpotato, or SickRage</i><br>
<b>ffmeg_bin_dir</b> = path to ffmpeg bin folder. This is the directory containing ffmpeg and ffprobe executables.<br> 
<b>ffmpeg_exe</b> = name of the ffmpeg executable (eg. ffmpeg.exe, ffmpeg.sh, etc.)<br>
<b>ffprobe_exe</b> = name of the ffprobe executable (eg. ffprobe.exe, ffprobe.sh, etc.)<br>
<b>handbrake_dir</b> = path to Handbrake directory (no trailing "\"). This is the directory containing HandBrakeCLI.exe<br>
<b>handbrakecli_exe</b> = name of the handbrakecli executable (eg. handbrakecli.exe, handbrake.sh)<br>
<b>garbage</b> = the extensions of the files you want to delete in the format "*.ex1", "*.ex2".<br>
