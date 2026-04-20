# support functions for eufy scales
# so timestamp and field names can be processed

from datetime import datetime
from utils import get_physique_rating
import pandas as pd

def convert_to_utc_datetime(date_str):
    clean_date = date_str.strip()
    dt_local = datetime.strptime(f"{clean_date}", "%Y-%m-%d %H:%M:%S")
    return dt_local

def process_row(row,gender):
    date = convert_to_utc_datetime(row['Time'])
    fat = float(row['BODY FAT %'])
    muscle_pct = float(row['MUSCLE MASS %'])

    data={
        'timestamp': date,
        'weight': int(float(row['WEIGHT (kg)']) * 100),
        'percent_fat': fat,
        'percent_hydration': float(row['WATER']),
        'visceral_fat_rating': int(float(row['VISCERAL FAT'])),
        'muscle_mass': float(row['MUSCLE MASS (kg)']),
        'bone_mass': float(row['BONE MASS (kg)']),
        'metabolic_age': int(float(row['BODY AGE'])) if row['BODY AGE'] else 0,
        'bmi': float(row['BMI'])
    }
    p_rating = row['BODY TYPE']
    if p_rating == '--' or pd.isna(p_rating):
        p_rating = get_physique_rating(fat, muscle_pct, gender)
    data['physique_rating'] = p_rating

    return data
