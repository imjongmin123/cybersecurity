import os
import argparse
import exifread
import struct
import datetime

VALID_IMAGE_EXTENSIONS = ['.png', '.jpeg', '.jpg', '.bmp', '.gif']

def get_file_metadata(file_path):
    metadata = {}
    file_stats = os.stat(file_path)
    metadata['File Name'] = os.path.basename(file_path)
    metadata['File Size'] = file_stats.st_size
    metadata['File Modification Date/Time'] = datetime.datetime.fromtimestamp(file_stats.st_mtime)
    metadata['File Access Date/Time'] = datetime.datetime.fromtimestamp(file_stats.st_atime)
    metadata['File Creation Date/Time'] = datetime.datetime.fromtimestamp(file_stats.st_ctime)
    return metadata

def parse_bmp_metadata(filename):
    with open(filename, 'rb') as f:
        header = f.read(14)
        dib_header_size, = struct.unpack('<I', f.read(4))
        
        if dib_header_size not in [40, 68, 108, 124]:
            print(f"Unsupported BMP version with DIB header size: {dib_header_size}")
            return
        
        dib_header = f.read(dib_header_size - 4)
        metadata = {
            "BMPVersion": dib_header_size,
            "ImageWidth": struct.unpack('<I', dib_header[0:4])[0],
            "ImageHeight": struct.unpack('<I', dib_header[4:8])[0],
            "Planes": struct.unpack('<H', dib_header[8:10])[0],
            "BitDepth": struct.unpack('<H', dib_header[10:12])[0],
            "Compression": struct.unpack('<I', dib_header[12:16])[0],
            "ImageLength": struct.unpack('<I', dib_header[16:20])[0],
            "PixelsPerMeterX": struct.unpack('<I', dib_header[20:24])[0],
            "PixelsPerMeterY": struct.unpack('<I', dib_header[24:28])[0],
            "NumColors": struct.unpack('<I', dib_header[28:32])[0],
            "NumImportantColors": struct.unpack('<I', dib_header[32:36])[0],
        }
        if dib_header_size >= 108:
            metadata.update({
                "RedMask": struct.unpack('<I', dib_header[36:40])[0],
                "GreenMask": struct.unpack('<I', dib_header[40:44])[0],
                "BlueMask": struct.unpack('<I', dib_header[44:48])[0],
                "AlphaMask": struct.unpack('<I', dib_header[48:52])[0],
                "ColorSpace": struct.unpack('<I', dib_header[52:56])[0],
                "GammaRed": struct.unpack('<I', dib_header[92:96])[0],
                "GammaGreen": struct.unpack('<I', dib_header[96:100])[0],
                "GammaBlue": struct.unpack('<I', dib_header[100:104])[0],
                "RenderingIntent": struct.unpack('<I', dib_header[104:108])[0],
                "ProfileDataOffset": struct.unpack('<I', dib_header[108:112])[0],
                "ProfileSize": struct.unpack('<I', dib_header[112:116])[0],
            })
    return metadata

def parse_gif_metadata(filename):
    with open(filename, 'rb') as f:
        header_lever = f.read(6)

        metadata = {
            "File type": "GIF",
            "GIF Version": header_lever[3:].decode('ascii'),
        }

        logical_screen_descriptor = f.read(7)
        width, height, packed, bg_color, aspect_ratio = struct.unpack('<HHBBB', logical_screen_descriptor)
        metadata.update({
            "Image Width": width,
            "Image Height": height,
            "Color Map": packed,
            "Has Color Map": (packed & 0b10000000) >> 7,
            "Color Resolution Depth": ((packed & 0b01110000) >> 4) + 1,
            "Bits Per Pixel": (packed & 0b00000111) + 1,
            "Background Color": bg_color,
            "Pixel Aspect Ratio": aspect_ratio,
        })
        return metadata

def parse_png_metadata(filename):
    with open(filename, 'rb') as f:
        signature = f.read(8)
        
        metadata = {}
        while True:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                break
            chunk_length, chunk_type = struct.unpack('>I4s', chunk_header)
            chunk_data = f.read(chunk_length)
            f.read(4)  # CRC

            if chunk_type == b'IHDR':  # Image header
                width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack('>IIBBBBB', chunk_data[:13])
                metadata.update({
                    "ImageWidth": width,
                    "ImageHeight": height,
                    "BitDepth": bit_depth,
                    "ColorType": color_type,
                    "CompressionMethod": compression,
                    "FilterMethod": filter_method,
                    "InterlaceMethod": interlace,
                })
        return metadata

def parse_exif_data(filename):
    with open(filename, 'rb') as f:
        tags = exifread.process_file(f)
    
    metadata = {}
    for tag in tags.keys():
        metadata[tag] = str(tags[tag])
    
    if not metadata:
        print(f"No EXIF tags found in {filename}")
    return metadata

def check_file_format(filename):
    with open(filename, 'rb') as f:
        header = f.read(10)

        if header[:2] == b'BM': #bmp
            metadata = parse_bmp_metadata(filename)
        elif header[:2] == b'\xFF\xD8': #jpeg, jpg
            metadata = parse_exif_data(filename)
        elif header[:8] == b'\x89PNG\r\n\x1a\n': #png
            metadata = parse_png_metadata(filename)
        elif header[:6] in (b'GIF87a', b'GIF89a'): #gif
            metadata = parse_gif_metadata(filename)
        else:
            print(f"{filename} is an unsupported file format")
            return "unsupported"
    file_metadata = get_file_metadata(filename)
    if isinstance(metadata, dict):
        metadata.update(file_metadata)
    return metadata

def print_metadata(metadata):
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            print(f"{key}: {value}")
    else:
        print(metadata)

def valid_file_type(filename):
    valid_extensions = ['.jpeg', '.jpg', '.bmp', '.gif', ".png"]
    ext = os.path.splitext(filename)[1].lower()
    if ext in valid_extensions:
        return filename
    else:
        raise argparse.ArgumentTypeError(f"Unsupported file type: {filename}")

def main():
    parser = argparse.ArgumentParser(description='Parse EXIF data from image files')
    parser.add_argument('filenames', nargs='+', type=valid_file_type)

    args = parser.parse_args()

    for filename in args.filenames:
        print(f"*********************",filename,"*********************")
        exif_data = check_file_format(filename)
        print_metadata(exif_data)

if __name__ == "__main__":
    main()
