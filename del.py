data = ["Body_Build_Type", "Body_Complexion_Type", "Habits", "Speech", "Forehead", "Face_Type",
        "Cheek", "Chin", "Lips", "Nose", "Teeth", "Beard", "Moustaches", "Eyes_Type", "Blind",
        "Eyes_Color", "Using_Specs", "Specs_Type", "Eye_Brow_Thickness", "Eye_Brow_Shape", 
        "Blinking", "Squint", "Ears_Missing", "Ears_Deformed", "Deaf_Dumb", "Arms", "Finger_Extra",
        "Finger_Missing", "Hunch_Stooping_Back", "Goitre", "Legs", "Toe_Extra", "Toe_Missing",
        "Limping", "Bow_Leg", "Knock_Knee", "Ear_Lobes", "Hair_Type", "Using_Wig", "Hair_Length",
        "Hair_Straightness", "Hair_Color", "Hair_Dye", "Hair_Cut", "Hair_Style", "Outer_Top",
        "Outer_Bottom", "Inner_Top", "Inner_Bottom", "Seasonal_Accessories_Top", "Seasonal_Accessories_Bottom",
        "Footwear", "Moles_Small", "Black_Marks_Large", "Scar_Marks", "Burn_Marks", "Leucoderma_White_Patches",
        "Tattoo_Marks", "Blood_Group"]
    
data_dict = {}
for i in data:
    data_dict[i] = f"{{form.{i}}}"

print(data_dict)