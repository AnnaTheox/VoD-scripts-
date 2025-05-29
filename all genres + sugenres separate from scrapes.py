import json
import pandas as pd

file_paths = [
    # directories of VoD scrapes in JSON here 
]

genres = set()
subgenres = set()

for path in file_paths:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        continue

    if not isinstance(data, list):
        print(f"Warning: Data in {path} is not a list. Skipping.")
        continue

    for item in data:
        platform = None

        # Channel 5
        if 'primary_vod_genre' in item and 'genre' in item:
            platform = '5'
            genre = item.get('primary_vod_genre')
            subgenre = item.get('genre')
            if genre:
                genres.add((platform, genre.strip()))
            if subgenre:
                subgenres.add((platform, subgenre.strip()))

        # iPlayer
        elif 'iplayer_main_genre' in item or 'iplayer_subgenres' in item:
            platform = 'iPlayer'
            genre = item.get('iplayer_main_genre')
            subgenre_list = item.get('iplayer_subgenres', [])
            if genre:
                genres.add((platform, genre.strip()))
            if isinstance(subgenre_list, list):
                for sg in subgenre_list:
                    if isinstance(sg, str):
                        subgenres.add((platform, sg.strip()))

        # ITVX
        elif 'itv_genre' in item:
            platform = 'ITVX'
            genre = item.get('itv_genre')
            if genre:
                genres.add((platform, genre.strip()))
            # no subgenre for ITVX

        # Channel 4
        elif 'subGenres' in item:
            platform = 'channel4'
            genre = item.get('genre')
            subgenre_list = item.get('subGenres', [])
            if genre:
                genres.add((platform, genre.strip()))
            if isinstance(subgenre_list, list):
                for sg in subgenre_list:
                    if isinstance(sg, str):
                        subgenres.add((platform, sg.strip()))

# Convert to DataFrames
genre_df = pd.DataFrame(sorted(genres), columns=['Platform', 'Genre'])
subgenre_df = pd.DataFrame(sorted(subgenres), columns=['Platform', 'Subgenre'])

# Write to Excel
output_path = r'C:\Users\kdpk341\PycharmProjects\Evidence for PSM\INT_genres_and_subgenres_by_platform.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    genre_df.to_excel(writer, index=False, sheet_name='Genres')
    subgenre_df.to_excel(writer, index=False, sheet_name='Subgenres')

print(f"Excel file saved to: {output_path}")
