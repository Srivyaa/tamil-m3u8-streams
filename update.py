import json
import subprocess
import uuid
import datetime
import re
import time

def get_current_time():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_current_time_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def is_live_stream(url):
    """Check if URL is live stream"""
    return '/live' in url or '/channel/' in url

def get_youtube_stream_url(yt_url):
    """Get ACTUAL stream URL from any YouTube URL"""
    try:
        print(f"       📡 Extracting stream...")
        
        # UNIVERSAL METHOD - Works for ALL YouTube URLs
        cmd = [
            "yt-dlp",
            "--get-url",
            "-f", "best[ext=m3u8]/best",
            "--no-warnings",
            "--quiet",
            yt_url
        ]
        
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=25)
        stream_url = output.decode().strip()
        
        if stream_url and '.m3u8' in stream_url:
            return stream_url
        elif stream_url:
            print(f"       🔄 Found non-m3u8: {stream_url[:60]}...")
            return None
            
    except:
        pass
    
    return None

def get_best_m3u8_variant(stream_url):
    """Get highest quality m3u8 variant"""
    try:
        # Get format list
        formats = subprocess.check_output([
            "yt-dlp", "-F", stream_url
        ], stderr=subprocess.DEVNULL, timeout=10).decode()
        
        # Try 720p first
        cmd = ["yt-dlp", "-f", "bestvideo[height<=720][ext=m3u8_native]/best[ext=m3u8_native]", "--get-url", stream_url]
        try:
            output = subprocess.check_output(cmd, timeout=10)
            url = output.decode().strip()
            if url and '.m3u8' in url:
                return url
        except:
            pass
        
        # Fallback to any m3u8
        cmd = ["yt-dlp", "-f", "best[ext=m3u8_native]", "--get-url", stream_url]
        output = subprocess.check_output(cmd, timeout=10)
        url = output.decode().strip()
        if url and '.m3u8' in url:
            return url
            
    except:
        pass
    
    return stream_url  # Return original if variant fails

def get_bitrate(m3u8_url):
    """Get bitrate from m3u8"""
    try:
        content = subprocess.check_output([
            "curl", "-s", "--max-time", "5", m3u8_url
        ], stderr=subprocess.DEVNULL).decode()
        
        match = re.search(r'BANDWIDTH=(\d+)', content)
        if match:
            return int(match.group(1)) // 1000
    except:
        pass
    return 128

def process_single_url(yt_url, name):
    """Process ONE URL with max retries"""
    print(f"📺 {name}")
    print(f"    🔍 URL: {yt_url[:60]}...")
    
    # RETRY LOGIC - 3 attempts
    for attempt in range(3):
        print(f"    🔄 Attempt {attempt + 1}/3")
        
        # Get stream URL
        stream_url = get_youtube_stream_url(yt_url)
        
        if stream_url:
            print(f"    📡 Stream: {stream_url[:60]}...")
            
            # Get best variant
            best_url = get_best_m3u8_variant(stream_url)
            
            # Verify URL works
            try:
                test = subprocess.check_output([
                    "curl", "-I", "--max-time", "5", best_url
                ], stderr=subprocess.DEVNULL)
                
                if b"200 OK" in test or b"302" in test:
                    bitrate = get_bitrate(best_url)
                    print(f"    ✅ SUCCESS: {bitrate}kbps")
                    return best_url, bitrate
            except:
                pass
        
        print(f"    ⏳ Retrying in 2s...")
        time.sleep(2)
    
    print(f"    ❌ FAILED after 3 attempts")
    return None, 0

# MAIN PROCESSING
print("🚀 Starting Tamil M3U8 Update")
print("=" * 50)

# Parse yt_links.txt
entries = []
with open("yt_links.txt", "r") as f:
    lines = f.readlines()

i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    
    parts = [p.strip() for p in line.split("|")]
    
    if len(parts) >= 3:
        name = parts[0]
        lang = parts[1] if len(parts) > 1 else "Tamil"
        favicon = parts[2] if len(parts) > 2 else ""
        
        # Get URL (handle multi-line)
        url = ""
        if len(parts) > 3:
            url = parts[3]
        elif i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith("http"):
                url = next_line
                i += 1
        
        if url:
            entries.append((name, lang, favicon, url))
    
    i += 1

print(f"✅ Found {len(entries)} streams to process")

# PROCESS ALL STREAMS
json_data = []
success_count = 0

for name, lang, favicon, url in entries:
    m3u8, bitrate = process_single_url(url, name)
    
    if m3u8:
        success_count += 1
        
        # Create JSON entry
        entry = {
            "changeuuid": str(uuid.uuid4()),
            "stationuuid": str(uuid.uuid4()),
            "serveruuid": str(uuid.uuid4()),
            "name": name,
            "url": m3u8,
            "url_resolved": m3u8,
            "homepage": "",
            "favicon": favicon,
            "tags": "News,Live" if "News" in name else "Music",
            "country": "India",
            "countrycode": "NEWS" if "News" in name else "ARTIST",
            "iso_3166_2": "",
            "state": "Tamil Nadu",
            "language": "tamil",
            "languagecodes": "ta",
            "votes": 0,
            "lastchangetime": get_current_time(),
            "lastchangetime_iso8601": get_current_time_iso(),
            "codec": "AAC",
            "bitrate": bitrate,
            "hls": 1,
            "lastcheckok": 1,
            "lastchecktime": get_current_time(),
            "lastchecktime_iso8601": get_current_time_iso(),
            "lastcheckoktime": get_current_time(),
            "lastcheckoktime_iso8601": get_current_time_iso(),
            "lastlocalchecktime": get_current_time(),
            "lastlocalchecktime_iso8601":
