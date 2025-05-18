import pandas as pd
import requests

def get_scryfall_image_url(scryfall_id, language='en'):
    """
    Fetch the correct image URL from Scryfall based on card ID and language
    """
    if pd.isna(scryfall_id):
        return None

    # Language-specific endpoint
    lang_url = f"https://api.scryfall.com/cards/{scryfall_id}/{language.lower()}"
    fallback_url = f"https://api.scryfall.com/cards/{scryfall_id}"

    try:
        response = requests.get(lang_url)
        if response.status_code == 200:
            return response.json().get("image_uris", {}).get("normal")

        # Try fallback if language version isn't available
        response = requests.get(fallback_url)
        if response.status_code == 200:
            return response.json().get("image_uris", {}).get("normal")

    except Exception as e:
        print(f"Error fetching {scryfall_id} ({language}): {e}")

    return None

# 🔄 Load your spreadsheet (replace filename as needed)
input_file = "Singles.xlsx"
df = pd.read_excel(input_file)

# 🌐 Add/Update the image column
df["scryfall image url"] = df.apply(
    lambda row: get_scryfall_image_url(row["Scryfall ID"], row["Language"]), axis=1
)

# 💾 Save the output
output_file = "Singles_For_Sale_Updated_With_Images.xlsx"
df.to_excel(output_file, index=False)
print(f"✅ Done! Image links saved to: {output_file}")