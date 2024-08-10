import piexif
from PIL import Image

def modify_exif_data(file_path, exif_modifications):
    # Load the existing EXIF data
    exif_dict = piexif.load(file_path)
    
    # Modify the specified EXIF tags
    for ifd_name in exif_modifications:
        ifd = exif_dict[ifd_name]
        for tag, value in exif_modifications[ifd_name].items():
            if isinstance(value, str):
                value = value.encode('utf-8')
            ifd[tag] = value

    # Save the modified EXIF data back to the file
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, file_path)

# Example usage
file_path = './Exercise2/example.jpg'
exif_modifications = {
    "Exif": {
        piexif.ExifIFD.DateTimeOriginal: "2024:05:29 15:00:00",
        piexif.ExifIFD.DateTimeDigitized: "2024:05:29 15:00:00"
    },
    "0th": {
        piexif.ImageIFD.Make: "New Camera Make",
        piexif.ImageIFD.Model: "New Camera Model"
    },
    "GPS": {
        piexif.GPSIFD.GPSLatitude: ((40, 1), (30, 1), (0, 1)),  # 40°30'0.0"N
        piexif.GPSIFD.GPSLatitudeRef: 'N',
        piexif.GPSIFD.GPSLongitude: ((74, 1), (0, 1), (0, 1)),  # 74°0'0.0"W
        piexif.GPSIFD.GPSLongitudeRef: 'W'
    }
}

modify_exif_data(file_path, exif_modifications)
print(f"EXIF data for {file_path} has been modified.")
