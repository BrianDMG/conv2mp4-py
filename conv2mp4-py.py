#!/usr/bin/python
"""----------------------------------------------------------------------------------
Imports (do not change)
----------------------------------------------------------------------------------"""
import datetime
import os
import os.path
import subprocess
import sys
import requests

"""=====================================================================================================================
conv2mp4-py - https://github.com/BrianDMG/conv2mp4-py v0.9 BETA

This Python script will recursively search through a user-defined file path and convert all videos of user-specified 
file types to MP4 with H264 video and AAC audio using ffmpeg. If a conversion failure is detected, the script re-encodes
the file with HandbrakeCLI. Upon successful encoding, Plex libraries are refreshed and source file is deleted. 
The purpose of this script is to reduce the amount of transcoding CPU load on a Plex server.
========================================================================================================================

ffmpeg : https://ffmpeg.org/download.html
handbrakecli : https://handbrake.fr/downloads.php 

----------------------------------------------------------------------------------------------------------------------
User-defined variables
------------------------------------------------------------------------------------------------------------------------
media_path = the path to the media you want to convert
file_types = the extensions of the files you want to convert in the format "*.ex1", "*.ex2" 
log_path = path you want the log file to save to. defaults to your desktop.
log_name = the filename of the log file
plexIP = the IP address and port of your Plex server (for the purpose of refreshing its libraries)
plex_token = your Plex server's token (for the purpose of refreshing its libraries).
	NOTE: See https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token
		  Plex server token is also easy to retrieve with PlexPy, Ombi, Couchpotato, or SickRage 
ffmeg_bin_dir = path to ffmpeg bin folder. This is the directory containing ffmpeg.exe and ffprobe.exe 
ffmpeg_exe = name of the ffmpeg executable (eg. ffmpeg.exe, ffmpeg.sh, etc.)
ffprobe_exe = name of the ffprobe executable (eg. ffprobe.exe, ffprobe.sh, etc.)
handbrake_dir = path to Handbrake directory. This is the directory containing HandBrakeCLI.exe
handbrakecli_exe = name of the handbrakecli executable (eg. handbrakecli.exe, handbrake.sh)
garbage = the extensions of the files you want to delete in the format "*.ex1", "*.ex2".
---------------------------------------------------------------------------------------------------------------------"""
media_path = '//yourpath/here/'
file_types = '.mkv', '.avi', '.flv', '.mpeg', '.ts'
log_path = '//yourpath/here/'
log_name = "conv2mp4-py.log"
plex_ip = 'plexip:32400'
plex_token = 'plextoken'
ffmeg_bin_dir = '//yourpath/here/'
ffmpeg_exe = "ffmpeg."
ffprobe_exe = "ffprobe."
handbrake_dir = '//yourpath/here/'
handbrakecli_exe = "handbrakecli."
garbage = '.nfo', '.idx', '.txt'  # Change to a single, non-existent extension to negate

"""---------------------------------------------------------------------------------------------------------------------
Static variables (do not change)
---------------------------------------------------------------------------------------------------------------------"""
# Print initial wait notice to console
print "\nconv2mp4-py v0.9 BETA - https://github.com/BrianDMG/conv2mp4-py"
print "-----------------------------------------------------------------\n"
print "Building file list, please wait. This may take a while, especially for large libraries.\n"

# Get current time to store as start time for script
script_dur_start = datetime.datetime.now().strftime('%H:%M:%S')

# Build file paths to executables
ffmpeg = os.path.join(ffmeg_bin_dir, ffmpeg_exe)
ffprobe = os.path.join(ffmeg_bin_dir, ffprobe_exe)
handbrake = os.path.join(handbrake_dir, handbrakecli_exe)
log = os.path.join(log_path, log_name)

# Initialize disk usage change to 0
diskusage = 0
dur_ticks_total = 0
dur_total = datetime.timedelta(hours=0, minutes=0, seconds=0)

"""---------------------------------------------------------------------------------------------------------------------
Classes (do not change)
---------------------------------------------------------------------------------------------------------------------"""


# Logging and console output
class Tee(object):
	def __init__(self, *targets):
		self.targets = targets

	def write(self, obj):
		for ftarg in self.targets:
			ftarg.write(obj)
			ftarg.flush()  # If you want the output to be visible immediately


ftarg = open(log, 'w')
original = sys.stdout
sys.stdout = Tee(sys.stdout, ftarg)

"""---------------------------------------------------------------------------------------------------------------------
General functions (do not change)
---------------------------------------------------------------------------------------------------------------------"""


# List files in the queue in the log
def list_targets():
	global queue_Count, queue_list
	queue_Count = 0
	queue_list = ''
	check_path = os.path.exists(media_path)
	if not check_path:
		print "Path not found: " + media_path
		print "Ensure your media_path exists and is accessible."
		print "Aborting script."
		exit()
	else:
		for root, dirs, targets in os.walk(media_path):
			for target_name in targets:
				if target_name.endswith(file_types):
					queue_Count += 1
					fullpath = os.path.normpath(os.path.join(str(root), str(target_name)))
					queue_list = queue_list + "\n" + (str(queue_Count) + ': ' + fullpath)
		if queue_Count == 1:
			print ("There is " + str(queue_Count) + " file in the queue:")
		elif queue_Count > 1:
			print ("There are " + str(queue_Count) + " files in the queue:")
		else:
			print ("There are no files to be converted in " + media_path + ". Congrats!")
		print queue_list


# Make time human-readable
def humanize_time(secs):
	if secs != "N/A":
		mins, secs = divmod(int(secs), 60)
		hours, mins = divmod(mins, 60)
		return '%02d:%02d:%02d' % (hours, mins, secs)
	else:
		mins, secs = divmod(30, 60)
		hours, mins = divmod(mins, 60)
		return '%02d:%02d:%02d' % (hours, mins, secs)


# Refresh Plex libraries
def plex_refresh():
	requests.get(plexURL)
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Plex libraries refreshed")


# Find out what video and audio codecs a file is using
def codec_discovery():
	global get_vid_codec, get_aud_codec, dur_ticks, duration

	# Check video codec with ffprobe
	get_vid_codec = subprocess.Popen(ffprobe + " -v error -select_streams v:0 -show_entries stream=codec_name -of "
								 + "default=nokey=1:noprint_wrappers=1 " + old_file, shell=True,
								 stdout=subprocess.PIPE).stdout.read().rstrip('\r\n')
	# Check audio codec with ffprobe
	get_aud_codec = subprocess.Popen(ffprobe + " -v error -select_streams a:0 -show_entries stream=codec_name -of  "
								 + "default=nokey=1:noprint_wrappers=1 " + old_file, shell=True,
								 stdout=subprocess.PIPE).stdout.read().rstrip('\r\n')
	# Get duration of file
	get_duration = subprocess.Popen(ffprobe + " -v error -show_entries format=duration -of"
									+ " default=noprint_wrappers=1:nokey=1 " + old_file, shell=True,
									stdout=subprocess.PIPE).stdout.read().rstrip('\r\n')
	head, sep, tail = get_duration.partition('.')
	get_duration_temp = humanize_time(head)
	hrs, mint, sec = get_duration_temp.split(':', 2)
	get_duration_temp2 = datetime.datetime.strptime(get_duration_temp, "%H:%M:%S")
	duration = datetime.datetime.strftime(get_duration_temp2, '%H:%M:%S')
	duration = datetime.timedelta(hours=int(hrs), minutes=int(mint), seconds=int(sec))


# $script:dur_ticks = $get_duration_temp.ticks

# Delete garbage files
def garbage_collection():
	global garbage_count, garbage_list
	garbage_count = 0
	garbage_list = ''
	for root, dirs, targets in os.walk(media_path):
		for target_name in targets:
			if target_name.endswith(garbage):
				garbage_count += 1
				fullpath = os.path.normpath(os.path.join(str(root), str(target_name)))
				garbage_list = garbage_list + "\n" + (str(garbage_count) + ': ' + fullpath)
				os.remove(fullpath)
	if garbage_count == 0:
		print ("\nGarbage Collection: There was no garbage found!")
	elif garbage_count == 1:
		print ("\nGarbage Collection: The following file was deleted:")
	else:
		print ("\nGarbage Collection: The following " + str(garbage_count) + " files were deleted:")
	print garbage_list


# Log various session statistics
def final_statistics():
	print "\n===================================================================================="
	# Print total session disk usage changes
	diskusage_gb = diskusage / 1024
	if -1024 > float(diskusage) > 1024:
		print ("\nTotal session disk usage change: " + str(round(diskusage_gb, 2)) + "GB")
	elif -1 > float(diskusage) > 1:
		print ("\nTotal session disk usage change: " + str(round(diskusage, 2)) + "MB")
	else:
		diskusage_kb = float(diskusage) * 1024
		print ("\nTotal session disk usage change was " + str(round(diskusage_kb, 2)) + "KB.")
	# Do some time math to get total script runtime
	script_dur_temp = datetime.datetime.now().strftime('%H:%M:%S')
	script_dur_total = datetime.datetime.strptime(script_dur_temp, '%H:%M:%S') - datetime.datetime.strptime(
		script_dur_start, '%H:%M:%S')
	print ("\n" + str(dur_total) + " of video processed in " + str(script_dur_total))
	# Do some math/rounding to get session average conversion speed
	# avgConv = dur_ticks_total / script_dur_temp.Ticks
	# avgConv = float(round(avgConv,2))
	# print ("Average conversion speed of " + avgConv + "x")
	print "\n===================================================================================="


"""---------------------------------------------------------------------------------------------------------------------
File size comparison functions (do not change)
---------------------------------------------------------------------------------------------------------------------"""


# If new and old files are the same size
def if_same():
	try:
		os.remove(old_file)
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Same file size.")
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " " + old_file + " deleted.")
	except (IOError, OSError):
		print (datetime.datetime.now().strftime(
			'%m/%d/%Y %H:%M:%S') + " ERROR: " + old_file + " could not be deleted. Full error below.")
		print ("This is very likely a permissions issue. Check the file/folder permissions.")
		print ("Aborting script.")
		exit()


# If new file is larger than old file
def if_larger():
	global diskusage
	diff_gt = (((float(new_file_size)) - float(old_file_size)) / 1024000)
	try:
		os.remove(os.path.normpath(old_file))
		if float(diff_gt) < 1.024:
			diff_gt_kb = diff_gt * 1024
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " New file is "
				   + str(round(diff_gt_kb, 2)) + "KB larger.")
		else:
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " New file is "
				   + str(round(diff_gt, 2)) + "MB larger.")
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + old_file + " deleted.")
		diskusage = diskusage + diff_gt
		if -1 < float(diskusage) < 1:
			diskusage_kb = diskusage * 1024
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Current cumulative storage difference: "
				   + str(round(diskusage_kb, 2)) + "KB")
		else:
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Current cumulative storage difference: "
				   + str(round(diskusage, 2)) + "MB")
	except (IOError, OSError):
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " ERROR: " + old_file + " could not be deleted.")
		print ("This is very likely a permissions issue. Check the file/folder permissions.")
		print ("Aborting script.")
		exit()


# If new file is smaller than old file
def if_smaller():
	global diskusage
	diff_lt = (((float(old_file_size)) - float(new_file_size)) / 1024000)
	try:
		os.remove(os.path.normpath(old_file))
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + old_file + " deleted.")
		if float(diff_lt) < 1.024:
			diff_lt_kb = diff_lt * 1024
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " New file is "
				   + str(round(diff_lt_kb, 2)) + "KB smaller.")
		else:
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " New file is " + str(
				round(diff_lt, 2)) + "MB smaller.")
		diskusage = diskusage - diff_lt
		if -1 < float(diskusage) < 1:
			diskusage_kb = diskusage * 1024
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Current cumulative storage difference: "
				   + str(round(diskusage_kb, 2)) + "KB")
		else:
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Current cumulative storage difference: "
				   + str(round(diskusage, 2)) + "MB")
	except (IOError, OSError):
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " ERROR: " + old_file
			   + " could not be deleted. Full error below.")
		print ("This is very likely a permissions issue. Check the file/folder permissions.")
		print ("Aborting script.")
		exit()


# If new file is over 25% smaller than the original file, trigger encoding failure
def if_faildetected():
	diff_err = ((new_file_size - old_file_size) / 1024000)
	try:
 		if -1 < float(diff_err) < 1:
			diff_err_kb = diff_err * 1024
			print (
				datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " EXCEPTION: New file is over 25% smaller ("
				+ str(round(diff_err_kb, 2)) + "KB).")
		else:
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " EXCEPTION: New file is over 25% smaller ("
				   + str(round(diff_err, 2)) + "MB).")
		os.remove(new_file)
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " " + new_file + " deleted.")
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " FAILOVER: Re-encoding " + old_file
			   + " with Handbrake.")
	except (IOError, OSError):
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " ERROR: " + new_file
			   + " could not be deleted. Aborting script.")
		exit()


"""---------------------------------------------------------------------------------------------------------------------
File conversion functions (do not change)
---------------------------------------------------------------------------------------------------------------------"""


# If a file video codec is already H264 and audio codec is already AAC, use these arguments
def simple_convert():
	print (datetime.datetime.now().strftime(
		'%m/%d/%Y %H:%M:%S') + " Video: " + get_vid_codec.upper() + ", Audio: " + get_aud_codec.upper()
		   + " . Performing simple container conversion to MP4.")
	ff_args = (" -n -fflags +genpts -i " + old_file + " -threads 0 -map 0 -c:v copy -c:a copy -c:s mov_text " + new_file)
	subprocess.Popen(ffmpeg + ff_args, stdout=subprocess.PIPE).stdout.read()
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " ffmpeg completed")


# If a file video codec is already H264, but audio codec is not AAC, use these arguments
def encode_audio():
	print (datetime.datetime.now().strftime(
		'%m/%d/%Y %H:%M:%S') + " Video: " + get_vid_codec.upper() + " , Audio: " + get_aud_codec.upper()
		   + ". Encoding audio to AAC")
	ff_args = (" -n -fflags +genpts -i " + old_file + " -threads 0 -map 0 -c:v copy -c:a aac -c:s mov_text " + new_file)
	subprocess.Popen(ffmpeg + ff_args, stdout=subprocess.PIPE).stdout.read()
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " ffmpeg completed")


# If a file video codec is not H264, and audio codec is already AAC, use these arguments
def encode_video():
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Video: " + get_vid_codec.upper()
		   + " , Audio: " + get_aud_codec.upper() + ". Encoding video to H264.")
	ff_args = (" -n -fflags +genpts -i " + old_file + " -threads 0 -map 0 -c:v libx264 -c:a copy -c:s mov_text "
			   + new_file)
	subprocess.Popen(ffmpeg + ff_args, stdout=subprocess.PIPE).stdout.read()
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " ffmpeg completed")


# If a file video codec not already H264, and audio codec is not AAC, use these arguments
def encode_both():
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Video: " + get_vid_codec.upper()
		   + ", Audio: " + get_aud_codec.upper() + ". Encoding video to H264 and audio to AAC.")
	ff_args = (" -n -fflags +genpts -i " + old_file + " -threads 0 -map 0 -c:v libx264 -c:a aac -c:s mov_text "
			   + new_file)
	subprocess.Popen(ffmpeg + ff_args, stdout=subprocess.PIPE).stdout.read()
	print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " ffmpeg completed")


# If an encode failure using ffmpeg is detected, failover to HandbrakeCLI
def encode_handbrake():
	try:
		hb_args = (" -i " + old_file + " -o " + new_file + " -f mp4 -a 1,2,3,4,5,6,7,8,9,10 --subtitle " +
				   "scan,1,2,3,4,5,6,7,8,9,10 -e x264 --encoder-preset slow --encoder-profile high " +
				   "--encoder-level 4.1 -q 18 -E aac --audio-copy-mask aac --verbose=1 --decomb " +
				   "--loose-anamorphic --modulus 2")
		subprocess.Popen(handbrake + hb_args, stdout=subprocess.PIPE).stdout.read()
		print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Handbrake finished.")
	except (IOError, OSError):
		print (datetime.datetime.now().strftime(
			'%m/%d/%Y %H:%M:%S') + " ERROR: Handbrake has encountered an error. Aborting script.")
		exit()


"""---------------------------------------------------------------------------------------------------------------------
Preperation 
---------------------------------------------------------------------------------------------------------------------"""
# Clear log contents
open(log, 'w').close()

"""---------------------------------------------------------------------------------------------------------------------
Begin search loop 
---------------------------------------------------------------------------------------------------------------------"""

print "\nconv2mp4-py v0.9 BETA - https://github.com/BrianDMG/conv2mp4-py"
print "-----------------------------------------------------------------\n"
# List files in the queue in the log
list_targets()

print ""

# Begin performing operations on files
i = 0
for root, dirs, targets in os.walk(media_path):
	for target_name in targets:
		if target_name.endswith(file_types):
			i = (i + 1)
			old_file = os.path.normpath(os.path.join(str(root), str(target_name)))
			new_file = os.path.splitext(old_file)[0] + ".mp4"
			progress = float(i) / float(queue_Count) * 100
			progress = str(round(progress, 2))
			plexURL = "http://" + plex_ip + "/library/sections/all/refresh?X-Plex-Token=" + plex_token
			print "------------------------------------------------------------------------------------"
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " Processing - " + old_file)
			print (datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') + " File " + str(i) + " of " + str(queue_Count)
				   + " - Total queue " + str(progress) + "%")

			"""---------------------------------------------------------------------------------------------------------
			Codec discovery to determine whether video, audio, or both needs to be encoded
			---------------------------------------------------------------------------------------------------------"""
			codec_discovery()

			"""---------------------------------------------------------------------------------------------------------
			Statistics-gathering derived from Codec Discovery 
			---------------------------------------------------------------------------------------------------------"""
			# Running tally of session container duration (cumulative length of video processed)
			dur_total = dur_total + duration
			# Running tally of ticks (time expressed as an integer) for script runtime
			# dur_ticks_total = dur_ticks_total + dur_ticks

			"""---------------------------------------------------------------------------------------------------------
			Begin ffmpeg conversion based on codec discovery 
			---------------------------------------------------------------------------------------------------------"""
			# Video is already H264, Audio is already AAC
			if get_vid_codec == 'h264' and get_aud_codec == 'aac':
				simple_convert()

			# Video is already H264, Audio is not AAC
			elif get_vid_codec == 'h264' and get_aud_codec != 'aac':
				encode_audio()

			# Video is not H264, Audio is already AAC
			elif get_vid_codec != 'h264' and get_aud_codec == 'aac':
				encode_video()

			# Video is not H264, Audio is not AAC
			else:
				encode_both()

			# Refresh Plex libraries
			plex_refresh()

			"""---------------------------------------------------------------------------------------------------------
			Begin file comparison between old file and new file to determine conversion success
			---------------------------------------------------------------------------------------------------------"""
			# Load files for comparison
			old_file_size = os.stat(old_file).st_size
			new_file_size = os.stat(new_file).st_size
			confDelOld = os.path.isfile(old_file)
			confDelNew = os.path.isfile(new_file)

			# If new file is the same size as old file, log status and delete old file
			if new_file_size == old_file_size:
				if_same()

			# If new file is larger than old file, log status and delete old file
			elif new_file_size > old_file_size:
				if_larger()

			# If new file is much smaller than old file (indicating a failed conversion), log status, delete new file,
			# and re-encode with HandbrakeCLI
			elif new_file_size < (old_file_size * .75):
				if_faildetected()

				"""-----------------------------------------------------------------------------------------------------
				Begin Handbrake encode
				-----------------------------------------------------------------------------------------------------"""
				# Handbrake CLI: https://trac.handbrake.fr/wiki/CLIGuide#presets
				encode_handbrake()
				# Load files for comparison
				old_file_size = os.stat(old_file).st_size
				new_file_size = os.stat(new_file).st_size
				# If new file is much smaller than old file (likely because the script was aborted during re-encode),
				# leave original file alone and print error
				if new_file_size < (old_file_size * .75):
					if_faildetected()
				# If new file is the same size as old file, log status and delete old file
				elif new_file_size == old_file_size:
					if_same()
				# If new file is larger than old file, log status and delete old file
				elif new_file_size > old_file_size:
					if_larger()
				# If new file is smaller than old file, log status and delete old file
				else:
					if_smaller()
			# If new file is smaller than old file, log status and delete old file
			else:
				if_smaller()
"""---------------------------------------------------------------------------------------------------------------------
Wrap-up
---------------------------------------------------------------------------------------------------------------------"""
final_statistics()
garbage_collection()
print ("\nFinished")
exit()
