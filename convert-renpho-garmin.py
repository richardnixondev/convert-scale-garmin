import pandas as pd
from datetime import datetime, timezone
import os.path
import sys
from garmin_fit_sdk import Encoder, Profile

if len(sys.argv) < 3: 
    print("Error: two arguments are expected, with an optional third (default male)")
    print("Usage: ", sys.argv[0], "<input_file.csv> <output_file.fit> [male/female]")
    sys.exit(1)

if len(sys.argv) == 4: # gender espeficied 
    if sys.argv[3] == 'male':
        gender='male'
    else:
        gender='female'
else:
    gender='male'
    
input_file = sys.argv[1]
output_file = sys.argv[2]

if not os.path.isfile(input_file):
    print(f"Error: file {input_file} not found!")
    exit(1)
    
if os.path.isfile(output_file):
    print(f"file {output_file} exists and will be overwritten!")

# Not very scientific logic for 'Physique Rating'.
# The thresholds can be adjusted for male/female 
# but these are not in the CSV file and need to come
# from the command line invocation
def get_physique_rating(fat, muscle_pct, gender):
    if gender.lower() == 'female':
        low_fat, high_fat = 21, 32
        low_muscle, high_muscle = 30, 40
    else:
        low_fat, high_fat = 12, 22
        low_muscle, high_muscle = 40, 50

    if fat > high_fat:
        return 1 if muscle_pct < low_muscle else 2 if muscle_pct < high_muscle else 3
    elif fat > low_fat:
        return 4 if muscle_pct < low_muscle else 5 if muscle_pct < high_muscle else 6
    else:
        return 7 if muscle_pct < low_muscle else 8 if muscle_pct < high_muscle else 9

def convert_to_utc_datetime(date_str, time_str):
    clean_date = date_str.strip().replace('-', '/')
    dt_local = datetime.strptime(f"{clean_date} {time_str.strip()}", "%d/%m/%Y %H:%M:%S")
    return dt_local

# Load data
df = pd.read_csv(input_file, skipinitialspace=True)
df.columns = [c.strip() for c in df.columns]

# Initialize FIT Encoder
encoder = Encoder()
# FIT File header info
encoder.write_mesg({
    'mesg_num': Profile['mesg_num']['FILE_ID'],
    'type': 'weight',
    'manufacturer': 'development',
    'product': 1,
    'serial_number': 12345678,
    'time_created': datetime.now(timezone.utc)
})

# Process CSV lines
for _, row in df.iterrows():
    try:
        dt = convert_to_utc_datetime(row['Date'], row['Time'])
        fat = float(row['Body Fat(%)'])
        muscle_pct = float(row['Skeletal Muscle(%)'])
        
        # Physique Rating Logic
        p_rating = row['Body Type']
        if p_rating == '--' or pd.isna(p_rating):
            p_rating = get_physique_rating(fat, muscle_pct, gender)

        encoder.write_mesg({
            'mesg_num': Profile['mesg_num']['WEIGHT_SCALE'],
            'timestamp': dt,
            'weight': int(float(row['Weight(kg)']) * 100),
            'percent_fat': fat,
            'percent_hydration': float(row['Body Water(%)']),
            'visceral_fat_rating': int(float(row['Visceral Fat'])),
            'muscle_mass': float(row['Muscle Mass(kg)']),
            'bone_mass': float(row['Bone Mass(kg)']),
            'metabolic_age': int(float(row['Metabolic Age'])),
            'bmi': float(row['BMI']),
            'physique_rating': int(p_rating)
        })
        
    except Exception as e:
        print(f"Error processing line: {e}")

# Close encoder and save file
uint8_array = encoder.close()
with open(output_file, 'wb') as f:
    f.write(uint8_array)

print(f"FIT file written as '{output_file}'")
