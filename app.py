import streamlit as st
import qrcode
import io
import uuid
from datetime import datetime
from PIL import Image
from supabase import create_client

st.set_page_config(
    page_title="SEVENTEEN AI Membership",
    page_icon="🪪",
    layout="centered"
)

# CONNECT TO SUPABASE
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

BUCKET = "members_photos"

st.title("SEVENTEEN AI")
st.subheader("Digital Membership System")

# QR VERIFICATION
params = st.query_params
verify_id = params.get("verify")

if verify_id:
    st.header("Membership Verification")

    result = supabase.table("members").select("*").eq(
        "member_id", verify_id
    ).execute()

    if result.data:
        member = result.data[0]
        st.success("✓ VERIFIED MEMBER")
        st.write("**Name:**", member["full_name"])
        st.write("**Membership ID:**", member["member_id"])
        st.write("**Role:**", member["role"])
        st.write("**Department:**", member["department"])
    else:
        st.error("Membership not found.")

    st.stop()


# ADMIN LOGIN
st.sidebar.title("Administration")

admin_password = st.secrets["ADMIN_PASSWORD"]
entered_password = st.sidebar.text_input(
    "Admin Password",
    type="password"
)

if entered_password != admin_password:
    st.info("Welcome to SEVENTEEN AI Digital Membership.")
    st.warning("Administrator login is required to register members.")
    st.stop()


# REGISTRATION
st.header("Register New Member")

with st.form("registration_form"):

    full_name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    role = st.text_input("Position / Role")
    department = st.text_input("Department")

    photo = st.file_uploader(
        "Upload Member Photograph",
        type=["jpg", "jpeg", "png"]
    )

    submitted = st.form_submit_button("Register Member")

    if submitted:

        if not full_name or not email or not role or not photo:
            st.error("Please complete all required fields.")

        else:
            try:
                year = datetime.now().year

                existing = supabase.table("members").select(
                    "member_id"
                ).like("member_id", f"SAI-{year}-%").execute()

                numbers = [
                    int(x["member_id"].split("-")[-1])
                    for x in existing.data
                ]

                next_number = max(numbers, default=0) + 1

                member_id = f"SAI-{year}-{next_number:03d}"

                extension = photo.name.split(".")[-1].lower()
                photo_path = f"{member_id}.{extension}"

                supabase.storage.from_(BUCKET).upload(
                    photo_path,
                    photo.getvalue(),
                    {"content-type": photo.type}
                )

                photo_url = supabase.storage.from_(
                    BUCKET
                ).get_public_url(photo_path)

                member_data = {
                    "member_id": member_id,
                    "full_name": full_name.strip(),
                    "email": email.strip().lower(),
                    "role": role.strip(),
                    "department": department.strip(),
                    "photo_path": photo_url
                }

                supabase.table("members").insert(
                    member_data
                ).execute()

                st.success("Member registered successfully!")
                st.write("Membership ID:", member_id)

            except Exception as e:
                st.error(f"Registration failed: {e}")


# MEMBER SEARCH
st.divider()
st.header("Find a Member")

search_id = st.text_input("Enter Membership ID")

if st.button("Search Member"):

    result = supabase.table("members").select("*").eq(
        "member_id", search_id.strip()
    ).execute()

    if result.data:
        member = result.data[0]

        st.success("Member found!")

        st.image(member["photo_path"], width=180)

        st.subheader(member["full_name"])
        st.write("Membership ID:", member["member_id"])
        st.write("Role:", member["role"])
        st.write("Department:", member["department"])

        st.write("Email:", member["email"])

        app_url = st.secrets["APP_URL"]

        verification_url = (
            f"{app_url}/?verify={member['member_id']}"
        )

        qr = qrcode.make(verification_url)

        qr_buffer = io.BytesIO()
        qr.save(qr_buffer, format="PNG")

        st.image(qr_buffer.getvalue(), width=180)

        st.download_button(
            "Download QR Code",
            data=qr_buffer.getvalue(),
            file_name=f"{member['member_id']}_QR.png",
            mime="image/png"
        )

    else:
        st.error("Member not found.")
