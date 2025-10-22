import json
import subprocess
import uuid
import datetime
import re

def get_current_time():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_current_time_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def get_highest_quality_m3u8(yt_url):
    """
    FIXED: Handles channel/live URLs + extracts highest quality m3u8
    """
    try:
        print(f"    🔍 Trying URL: {yt_url}")
        
        # STEP 1: Get the ACTUAL LIVE STREAM URL first
        print("    📡 Fetching live stream URL...")
        output = subprocess.check_output([
            "yt-dlp", 
            "--get-url",
            "-f", "best[ext=m3u8]",
            "--no-warnings",
            yt_url
        ], stderr=subprocess.STDOUT, timeout=30)
        
        stream_url = output.decode().strip()
        print(f"    📡 Found stream: {stream_url[:80]}...")
        
        if not stream_url.endswith('.m3u8'):
            print("    ❌ Not an m3u8 stream")
            return None, 0
        
        # STEP 2: Get highest quality variant
        print("    🎥 Checking quality variants...")
        variants_output = subprocess.check_output([
            "yt-dlp", 
            "-F",  # List formats
            stream_url
        ], stderr=subprocess.STDOUT, timeout=15)
        
        # STEP 3: Select best m3u8 format
        format_cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=1080][ext=m3u8_native]/bestvideo[height<=720][ext=m3u8_native]/best[ext=m3u8_native]/bestaudio[ext=m3u8_native]",
            "--get-url",
            stream_url
        ]
        
        output = subprocess.check_output(format_cmd, stderr=subprocess.STDOUT, timeout=20)
        best_url = output.decode().strip()
        
        if best_url and best_url.endswith('.m3u8'):
            bitrate = get_bitrate_from_m3u8(best_url)
            print(f"    ✅ HIGH QUALITY: {bitrate}kbps")
            return best_url, bitrate
        
        # FALLBACK: Use original stream
        bitrate = get_bitrate_from_m3u8(stream_url)
        print(f"    ✅ QUALITY: {bitrate}kbps")
        return stream_url, bitrate
        
    except subprocess.CalledProcessError as e:
        print(f"    ❌ yt-dlp error: {e}")
    except subprocess.TimeoutExpired:
        print(f"    ⏰ Timeout - stream may be offline")
    
    return None, 0

def get_bitrate_from_m3u8(m3u8_url):
    """Extract bitrate from m3u8"""
    try:
        output = subprocess.check_output([
            "curl", "-s", "--max-time", "8", m3u8_url
        ], stderr=subprocess.STDOUT)
        
        content = output.decode()
        bandwidth_match = re.search(r'BANDWIDTH=(\d+)', content)
        if bandwidth_match:
            return int(bandwidth_match.group(1)) // 1000
        
    except:
        pass
    
    return 128  # Default

# Parse yt_links.txt
entries = []
with open("yt_links.txt", "r") as f:
    content = f.readlines()

i = 0
while i < len(content):
    line = content[i].strip()
    if not line:
        i += 1
        continue
    
    parts = [p.strip() for p in line.split("|")]
    
    if len(parts) == 4:
        entries.append(parts)
    elif len(parts) == 3 and i+1 < len(content):
        favicon = parts[2]
        i += 1
        yt_url = content[i].strip()
        entries.append([parts[0], parts[1], favicon, yt_url])
    i += 1

print(f"✅ Parsed {len(entries)} entries")

# Process streams
json_data = []
successful = 0

for entry in entries:
    if len(entry) != 4: continue
        
    name, lang, favicon, yt_url = entry
    print(f"\n📺 Processing: {name}")
    
    m3u8, bitrate = get_highest_quality_m3u8(yt_url)
    
    if m3u8:
        successful += 1
        print(f"   🎉 SUCCESS: {bitrate}kbps")
        
        # Determine type
        name_lower = name.lower()
        if "news" in name_lower:
            countrycode, tags = "NEWS", "News,Live"
        elif "hits" in name_lower or "music" in lang.lower():
            countrycode, tags = "ARTIST", "Music"
        else:
            countrycode, tags = "LIVE", "Live,TV"
        
        # Create entry
        now_str = get_current_time()
        now_iso = get_current_time_iso()
        
        dict_entry = {
            "changeuuid": str(uuid.uuid4()),
            "stationuuid": str(uuid.uuid4()),
            "serveruuid": str(uuid.uuid4()),
            "name": name,
            "url": m3u8,
            "url_resolved": m3u8,
            "homepage": "",
            "favicon": favicon,
            "tags": tags,
            "country": "India",
            "countrycode": countrycode,
            "iso_3166_2": "",
            "state": "Tamil Nadu",
            "language": "tamil",
            "languagecodes": "ta",
            "votes": 0,
            "lastchangetime": now_str,
            "lastchangetime_iso8601": now_iso,
            "codec": "AAC",
            "bitrate": bitrate,
            "hls": 1,
            "lastcheckok": 1,
            "lastchecktime": now_str,
            "lastchecktime_iso8601": now_iso,
            "lastcheckoktime": now_str,
            "lastcheckoktime_iso8601": now_iso,
            "lastlocalchecktime": now_str,
            "lastlocalchecktime_iso8601": now_iso,
            "clicktimestamp": now_str,
            "clicktimestamp_iso8601": now_iso,
            "clickcount": 0,
            "clicktrend": 0,
            "ssl_error": 0,
            "geo_lat": None,
            "geo_long": None,
            "geo_distance": None,
            "has_extended_info": False
        }
        json_data.append(dict_entry)
    else:
        print(f"   ❌ FAILED")

print(f"\n🎉 SUCCESS: {successful}/{len(entries)} streams")

# Update existing json
try:
    with open("artist.json", "r") as f:
        existing = json.load(f)
except:
    existing = []

name_to_existing = {d["name"]: d for d in existing}
updated = 0

for new_entry in json_data:
    if new_entry["name"] in name_to_existing:
        old = name_to_existing[new_entry["name"]]
        old.update({
            k: v for k, v in new_entry.items() 
            if k in ["url", "url_resolved", "bitrate", "tags", "lastchangetime", 
                    "lastchangetime_iso8601", "lastchecktime", "lastchecktime_iso8601",
                    "lastcheckoktime", "lastcheckoktime_iso8601", "clicktimestamp", 
                    "clicktimestamp_iso8601", "changeuuid"]
        })
        updated += 1
    else:
        existing.append(new_entry)

# Write output
with open("artist.json", "w") as f:
    json.dump(existing, f, indent=2)

print(f"✅ Updated {updated} entries | Total: {len(existing)}")
print("🎵 artist.json ready!")
