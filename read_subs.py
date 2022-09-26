import sys
import codecs
from functools import reduce
from subprocess import call

max_length = 10000
split_length = 1000

class interval:
	def __init__(self, s, f, type):
		if isinstance(s, str):
			self.start_time = convert_to_milliseconds(s)
			self.end_time = convert_to_milliseconds(f)
		else:
			self.start_time = s
			self.end_time = f
		self.duration = self.end_time - self.start_time
		# "real" intervals correspond to actual lines of dialog from the subtitle file
		# "fake" intervals are inferred from gaps between dialog
		self.type = type
	def __str__(self):
		return convert_to_timestamp(self.start_time) + ", " + convert_to_timestamp(self.end_time) + ", " + str(self.duration) + ", " + self.type
	
# timestamp is in hundredths of a second - not milliseconds!	
def convert_to_milliseconds(t):
	millis = 0
	t_arr = t.split(":")
	millis = millis + int(t_arr[0])*60*60*100
	millis = millis + int(t_arr[1])*60*100
	seconds = t_arr[2].split(".")[0]
	lsd = t_arr[2].split(".")[1]
	millis = millis + int(seconds) * 100 + int(lsd)
	return millis * 10

def convert_to_timestamp(t):
	hours = t // (60*60*1000)
	t = t - (hours * 60*60*1000)
	minutes = t // (60*1000)
	t = t - (minutes * 60 * 1000)
	seconds = t // 1000
	t = t - (seconds * 1000)
	milliseconds = t % 1000
	#same gotcha the other direction - milliseconds is a 3-digit quantity!
	return ":".join([str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2)]) + "." + str(milliseconds).zfill(3)
def reduce_func(l, x):
	if l == []:
		return [x]
	if l[-1].duration + x.duration <= 10000:
		return l + [interval(l[-1].start_time, x.end_time, "fake")]
	else:
		return l + [x]

if len(sys.argv) < 3:
	print("Usage: ", sys.argv[0], " formatted_subfile.txt video_file output_dir")
	exit(1)

subtitle_file = sys.argv[1]
video_file = sys.argv[2]
output_dir = sys.argv[3]

subtitles = []
times = []
deltas = []
intervals = []
f = codecs.open(subtitle_file, encoding='utf-8')
for line in f:
	subtitles.append(repr(line))
	
for s in subtitles:
	start_time = s.split(",")[1]
	end_time = s.split(",")[2]
	intervals.append(interval(start_time, end_time, "real"))
complete_intervals = []
for i in range(len(intervals) - 1):
	complete_intervals.append(intervals[i])
	if intervals[i+1].start_time != intervals[i].end_time:
		new_interval = interval(intervals[i].end_time, intervals[i+1].start_time, "fake")
		complete_intervals.append(new_interval)

split_intervals = []
# split into 1-second chunks:
# - fake intervals longer than split length
# - real intervals longer than max length
for i in range(len(complete_intervals)):
	if (complete_intervals[i].duration > split_length and complete_intervals[i].type == "fake") or (complete_intervals[i].duration > max_length and complete_intervals[i].type == "real"):
		num_chunks = complete_intervals[i].duration // split_length + 1
		for j in range(num_chunks):
			start_time = complete_intervals[i].start_time + split_length*j
			end_time = start_time + split_length
			if end_time > complete_intervals[i].end_time:
				end_time = complete_intervals[i].end_time
			new_interval = interval(start_time, end_time, "fake")
			split_intervals.append(new_interval)
	else:
		split_intervals.append(complete_intervals[i])
		
for s in split_intervals:
	print(s)
length = len(split_intervals)
k = 0

# greedily coalesce intervals together until they reach max_length
while k < length - 2:
	if split_intervals[k].duration + split_intervals[k + 1].duration < max_length:
		new_interval = interval(split_intervals[k].start_time, split_intervals[k+1].end_time, "fake")
		split_intervals.insert(k, new_interval)
		del split_intervals[k+1]
		del split_intervals[k+1]
		length -= 1
	else:
		k += 1

count=0
for s in split_intervals:
	args = ["ffmpeg", "-ss", convert_to_timestamp(s.start_time), "-t", convert_to_timestamp(s.duration), "-i", video_file, "-i", "palette.png", "-filter_complex", r"fps=24,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse", output_dir + str(count) + ".gif"]
	print(args)
	call(args)
	count += 1
		
