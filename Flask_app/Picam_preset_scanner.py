import os
import time
import glob
import piexif
import importlib 
from PIL import Image
from pathlib import Path
from datetime import datetime
from picamera2 import Picamera2, Preview
from libcamera import Transform, controls

awb_modes = {
    "off": 0,
    "auto": 1,
    "sunlight": 2,
    "cloudy": 3,
    "shade": 4,
    "tungsten": 5,
    "fluorescent": 6,
    "incandescent": 7,
    "flash": 8,
    "horizon": 9,
}
exposure_modes = {
    "normal": 0,
    "sport": 1,
    "long": 2
}

ae_metering_modes = {
    "centre-weighted": 0,
    "spot": 1,
    "matrix": 2
}
Local         = Path.home() / "Pictures" / "RT360_Capture"


# === Postavke koje se smiju mjenjati ===
SAVE_JPG = True                    # True = JPG,   snima JPG
SAVE_DNG = False                   # False = DNG,  snima DNG, ako su oboje false onda je JPG
C_res         = (4056, 3040)       # (4056, 3040) najveca rezolucija
C_rotation    = 90                 # 0, 90, 180, 270 rotira sliku  preview u browseru i pise u EXIF ali samo za jpg
C_hflip       = False              # True / False        
C_vflip       = False              # True / False
C_AwbEnable   = True               # True = auto...., False = off
C_AwbMode     = "incandescent"     # auto, incandescent, fluorescent, daylight, cloudy
C_Exp_Mode    = "normal"           # normal, short, long
C_Meter       = "centre-weighted"  # centre-weighted, spot, matrix
C_Gain        = 1.0                # 1.0 = ISO 100
C_Shutter     = 0                  # 0 = auto; ili npr. 20000 = 1/50s
C_Brightness  = 0                  # -1.0 to 1.0
C_Contrast    = 1                  # 0.0 to 32.0
C_Saturation  = 1.0                # 0.0 to 32.0
C_Sharpness   = 1.0                # 0.0 to 16.0
C_format      = "RGB888"           # RGB888, BGR888 ,YUV420, YUV420_SP, XBGR8888, XRGB8888, MJPEG, YUYV, RGB565, GRAY8
# === Postavke koje se smiju mjenjati kraj===


if C_rotation not in [0, 90, 180, 270]:
    raise ValueError("Rotacija mora biti 0, 90, 180 ili 270")

# === Inicijalizacija viviše kamera ===
cams = [Picamera2(0), Picamera2(1)] #,Picamera2(2), Picamera2(3)]

def get_camera(index):
    return cams[index]
    
def write_exif_metadata(filename, rotation, metadata):
    orientation_map = {
        0: 1,
        90: 6,
        180: 3,
        270: 8
    }
    orientation = orientation_map.get(rotation, 1)
    dt_str = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    exposure_us = metadata.get("ExposureTime", 0)               # mikrosekunde
    iso_val = int(metadata.get("AnalogueGain", 1.0) * 100)      # okvirno pretvaranje gain -> ISO
    focal_len = 3.6                                             # primjer za V3 kameru (fiksni objektiv)

    exif_dict = {
        "0th": {
            piexif.ImageIFD.Orientation: orientation,
            piexif.ImageIFD.Make: "DI360",
            piexif.ImageIFD.Model: "Raspberry pi 5B - Camera Module V3",
            piexif.ImageIFD.Software: "RT360",
            piexif.ImageIFD.Artist: "",
            piexif.ImageIFD.Copyright: "2025 DI360",
            piexif.ImageIFD.ImageDescription: "Fotogrametrija",
            piexif.ImageIFD.DateTime: dt_str,
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: dt_str,
            piexif.ExifIFD.ExposureTime: (exposure_us, 1_000_000) if exposure_us else None,
            piexif.ExifIFD.ISOSpeedRatings: iso_val if iso_val else None,
            piexif.ExifIFD.FocalLength: (int(focal_len * 100), 100),
        }
    }
    for ifd in exif_dict:
        keys_to_del = [k for k,v in exif_dict[ifd].items() if v is None]
        for k in keys_to_del:
            del exif_dict[ifd][k]
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filename)
    
def apply_camera_settings(cam):
    transform = Transform(hflip=int(C_hflip), vflip=int(C_vflip))
    config = cam.create_still_configuration(
        main={"size": C_res, "format": C_format},
        transform=transform
    )
    cam.configure(config)
    controls = {
        "AwbEnable":      C_AwbEnable,
        "AwbMode":        awb_modes[C_AwbMode],
        "AeExposureMode": exposure_modes[C_Exp_Mode],
        "AeMeteringMode": ae_metering_modes[C_Meter],
        "AnalogueGain":   C_Gain,
        "ExposureTime":   C_Shutter,
        "Brightness":     C_Brightness,
        "Contrast":       C_Contrast,
        "Saturation":     C_Saturation,
        "Sharpness":      C_Sharpness,
    }
    cam.set_controls(controls)

# === Generiranje imena slike ===
def pic_name(idx, current_folder_path):
    folder = current_folder_path
    folder.mkdir(parents=True, exist_ok=True)
    if SAVE_JPG:
        ext = "jpg"
    elif SAVE_DNG:
        ext = "dng"
    else:
        ext = "jpg"  # fallback
    list_of_files = sorted(folder.glob(f"IMG_cam{idx}*.{ext}"))
    max_num = 0
    for f in list_of_files:
        try:
            num = int(f.stem.rsplit("-", 1)[1])
            if num > max_num:
                max_num = num
        except:
            continue
    next_num = max_num + 1
    return str(folder / f"IMG_cam{idx}-{next_num:05d}")

# === Snimanje slike ===
def take_picture():
    for idx, cam in enumerate(cams):
        apply_camera_settings(cam)
        cam.start()
        time.sleep(1)
        metadata = cam.capture_metadata()
        path = pic_name(idx)
        cam.capture_file(path)
        cam.stop()

        write_exif_metadata(path, C_rotation, metadata)
        print(f"Camera {idx} picture saved: {path} with EXIF rotation {C_rotation}")

# === Snimanje slika u oba formata ===     
def capture_both_formats(current_folder_path):
    for idx, cam in enumerate(cams):
        print(f"\n[Picam {idx}] Capture starting...")
        apply_camera_settings(cam)
        capture_config = cam.create_still_configuration(raw={}, display=None, buffer_count=2)
        cam.start()
        time.sleep(1)
        request = cam.capture_request()
        path_base = pic_name(idx, current_folder_path)
        jpg_path = f"{path_base}.jpg"
        dng_path = f"{path_base}.dng"
        if SAVE_JPG:
            request.save("main", jpg_path)
            print(f"DONE: camera {idx} -> {jpg_path}")
        if SAVE_DNG:
            request.save_dng(dng_path)
            print(f"DONE: camera {idx} -> {dng_path}")
        metadata = request.get_metadata()
        request.release()
        cam.stop()
        if SAVE_JPG:
            write_exif_metadata(jpg_path, C_rotation, metadata)
        
# === Test ===

if __name__ == "__main__":
    capture_both_formats()
    
