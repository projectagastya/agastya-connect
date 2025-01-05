import json
import os
import streamlit as st

from utils import switch_page

async def load_add_student_page():
    if st.button("Back to Choice Page", icon=":material/arrow_back:", type="primary"):
        switch_page("choice")
        
    st.title("Add a New Student")
    name = st.text_input("Name")
    age = st.number_input("Age", step=1)
    sex = st.radio("Gender", ["Male", "Female"])
    region = st.text_input("Region")
    uploaded_image = st.file_uploader("Upload Student Image", type=["png", "jpg", "jpeg"])

    if st.button("Submit"):
        if not name or not region or not uploaded_image:
            st.error(body="All fields must be filled, and an image must be uploaded!")
        elif age < 5 or age > 30:
            st.error("Age must be between 5 and 30.")
        else:
            image_path = f"information/{name.lower().replace(' ', '-')}.png"
            os.makedirs("information", exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(uploaded_image.read())

            new_student = {
                "name": name,
                "age": age,
                "sex": sex,
                "region": region,
                "image": image_path
            }
            try:
                with open("students.json", "r+") as file:
                    students = json.load(file)
                    students.append(new_student)
                    file.seek(0)
                    json.dump(students, file, indent=4)
                st.success("Student added successfully!")
            except FileNotFoundError:
                st.error("Students data file not found.")


