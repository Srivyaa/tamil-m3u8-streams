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
    Extract the highest quality m3u8 stream available
    Prioritizes: 720p/1080p AAC > 480p AAC > 360p AAC > Best Audio
    """
    try:
        # First, get all available formats
        output = subprocess.check_output([
            "yt-dlp", 
            "-f", "bestvideo[height<=1080][ext=m3u8]/bestvideo[height<=720][ext=m3u8]/best[height<=480][ext=m3u8]/best[ext=m3u8]",
            "--get-url", 
            yt_url
        ], stderr=subprocess.STDOUT)
        
        url = output.decode().strip()
        if url and url.endswith(".m3u8"):
            bitrate = get_bitrate_from_m3u8(url)
            return url, bitrate
        
        # Fallback 1: Try best audio m3u8
        output = subprocess.check_output([
            "yt-dlp", 
            "-f", "bestaudio[ext=m3u8]",
            "--get-url", 
            yt_url
        ], stderr=subprocess.STDOUT)
        
        url = output.decode().strip()
        if url and url.endswith(".m3u8"):
            bitrate = get_bitrate_from_m3u8(url)
            return url, bitrate
        
        # Fallback 2: Try any m3u8
        output = subprocess.check_output([
            "yt-dlp", 
            "-f", "best[ext=m3u8]",
            "--get-url", 
            yt_url
        ], stderr=subprocess.STDOUT)
        
        url = output.decode().strip()
        if url and url.endswith(".m3u8"):
            bitrate = get_bitrate_from_m3u8(url)
            return url, bitrate
            
    except subprocess.CalledProcessError as e:
        print(f"Error getting m3u8 for {yt_url}: {e}")
    
    return None, 0

def get_bitrate_from_m3u8(m3u8_url):
    """
    Extract bitrate from m3u8 manifest
    """
    try:
        output = subprocess.check_output([
            "curl", "-s", "--max-time", "10", m3u8_url
        ], stderr=subprocess.STDOUT)
        
        content = output.decode()
        # Look for #EXT-X-STREAM-INF:BANDWIDTH=
        bandwidth_match = re.search(r'#EXT-X-STREAM-INF:.*?BANDWIDTH=(\d+)', content)
        if bandwidth_match:
            bitrate = int(bandwidth_match.group(1)) // 1000  # Convert to kbps
            return bitrate
        
        # Look for #EXTINF bitrate
        extinf_match = re.search(r'#EXT-X-MEDIA-SEQUENCE.*?BANDWIDTH=(\d+)', content)
        if extinf_match:
            bitrate = int(extinf_match.group(1)) // 1000
            return bitrate
            
    except:
        pass
    
    return 128  # Default bitrate

def get_current_time():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_current_time_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

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
    
    # Handle both formats: "Name | Lang | Icon | URL" or split lines
    parts = [p.strip() for p in line.split("|")]
    
    if len(parts) == 4:
        entries.append(parts)
    elif len(parts) == 3 and (line.endswith("|") or i+1 < len(content)):
        # Multi-line entry
        favicon = parts[2]
        i += 1
        if i < len(content):
            yt_url = content[i].strip()
            entries.append([parts[0], parts[1], favicon, yt_url])
    i += 1

print(f"Parsed {len(entries)} valid entries from yt_links.txt")

# Generate new data
json_data = []
successful_streams = 0

for entry in entries:
    if len(entry) != 4:
        continue
        
    name, lang, favicon, yt_url = entry
    
    print(f"Processing: {name}")
    m3u8, bitrate = get_highest_quality_m3u8(yt_url)
    
    if not m3u8:
        print(f"  ❌ No m3u8 found for {name}")
        continue
    
    successful_streams += 1
    print(f"  ✅ Found m3u8: {bitrate}kbps")
    
    # Determine countrycode
    name_lower = name.lower()
    if any(word in name_lower for word in ["news", "tv", "channel"]):
        countrycode = "NEWS"
        tags = "News,Live"
    elif any(word in lang or name_lower for word in ["music", "hits"]):
        countrycode = "ARTIST"
        tags = "Music"
    else:
        countrycode = "LIVE"
        tags = "Live,TV"
    
    # Generate UUIDs
    changeuuid = str(uuid.uuid4())
    stationuuid = str(uuid.uuid4())
    serveruuid = str(uuid.uuid4())
    
    now_str = get_current_time()
    now_iso = get_current_time_iso()
    
    dict_entry = {
        "changeuuid": changeuuid,
        "stationuuid": stationuuid,
        "serveruuid": serveruuid,
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
        "language": lang.lower(),
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

print(f"\nSuccessfully processed {successful_streams}/{len(entries)} streams")

# Load existing artist.json if exists
try:
    with open("artist.json", "r") as f:
        existing = json.load(f)
    print(f"Loaded {len(existing)} existing entries")
except FileNotFoundError:
    existing = []
    print("No existing artist.json found")

# Update or add entries (preserve existing UUIDs when possible)
name_to_existing = {d["name"]: d for d in existing}

updated_count = 0
added_count = 0

for new_dict in json_data:
    name = new_dict["name"]
    
    if name in name_to_existing:
        # Update existing entry
        old = name_to_existing[name]
        old["url"] = new_dict["url"]
        old["url_resolved"] = new_dict["url"]
        old["bitrate"] = new_dict["bitrate"]
        old["tags"] = new_dict["tags"]
        old["lastchangetime"] = new_dict["lastchangetime"]
        old["lastchangetime_iso8601"] = new_dict["lastchangetime_iso8601"]
        old["lastchecktime"] = new_dict["lastchecktime"]
        old["lastchecktime_iso8601"] = new_dict["lastchecktime_iso8601"]
        old["lastcheckoktime"] = new_dict["lastcheckoktime"]
        old["lastcheckoktime_iso8601"] = new_dict["lastcheckoktime_iso8601"]
        old["lastlocalchecktime"] = new_dict["lastlocalchecktime"]
        old["lastlocalchecktime_iso8601"] = new_dict["lastlocalchecktime_iso8601"]
        old["clicktimestamp"] = new_dict["clicktimestamp"]
        old["clicktimestamp_iso8601"] = new_dict["clicktimestamp_iso8601"]
        old["changeuuid"] = str(uuid.uuid4())
        updated_count += 1
    else:
        # Add new entry
        existing.append(new_dict)
        added_count += 1

# Remove entries that no longer have valid streams
existing = [e for e in existing if any(e["name"] == d["name"] for d in json_data)]

print(f"Updated: {updated_count}, Added: {added_count}, Total: {len(existing)}")

# Write back to artist.json
with open("artist.json", "w") as f:
    json.dump(existing, f, indent=2)

print("✅ artist.json updated successfully!")
