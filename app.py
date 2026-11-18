import streamlit as st
import qrcode
import io
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
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

        # CREATE PROFESSIONAL ID CARD
        card = Image.new("RGB", (1200, 750), "#101B35")
        draw = ImageDraw.Draw(card)

        white = "#FFFFFF"
        silver = "#B8C5D8"
        blue = "#263D65"

        # Header
        draw.rounded_rectangle(
            (35, 35, 1165, 715),
            radius=35,
            outline=silver,
            width=5
        )

        draw.text(
            (85, 75),
            "SEVENTEEN AI",
            fill=white,
            font=ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                58
            )
        )

        draw.text(
            (85, 155),
            "INTELLIGENCE  |  INNOVATION  |  IMPACT",
            fill=silver
        )

        draw.line((80, 215, 1120, 215), fill=silver, width=3)

        # Member photograph
        response = requests.get(
            member["photo_path"], timeout=20
        )
        response.raise_for_status()

        photo = Image.open(
            io.BytesIO(response.content)
        ).convert("RGB")

        photo = ImageOps.fit(photo, (330, 390))

        card.paste(photo, (85, 265))

        # Member details
        draw.text(
            (465, 280),
            member["full_name"],
            fill=white,
            font=ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                38
            )
        )

        draw.text((465, 365), "POSITION / ROLE", fill=silver)
        draw.text((465, 405), member["role"], fill=white)

        draw.text((465, 465), "DEPARTMENT", fill=silver)
        draw.text(
            (465, 505),
            member["department"] or "Not specified",
            fill=white
        )

        draw.text((465, 565), "MEMBERSHIP ID", fill=silver)
        draw.text(
            (465, 605),
            member["member_id"],
            fill=white,
            font=ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                32
            )
        )

        # QR code
        qr_image = qr.convert("RGB").resize((190, 190))
        card.paste(qr_image, (900, 465))

        draw.text(
            (895, 665),
            "SCAN TO VERIFY",
            fill=silver
        )

        st.divider()
        st.subheader("SEVENTEEN AI Digital ID Card")

        st.image(card, use_container_width=True)

        # Download PNG
        png_buffer = io.BytesIO()
        card.save(png_buffer, format="PNG")

        st.download_button(
            "Download ID Card (PNG)",
            data=png_buffer.getvalue(),
            file_name=f"{member['member_id']}_ID.png",
            mime="image/png"
        )

        # Download PDF
        pdf_buffer = io.BytesIO()
        card.save(pdf_buffer, format="PDF", resolution=150)

        st.download_button(
            "Download ID Card (PDF)",
            data=pdf_buffer.getvalue(),
            file_name=f"{member['member_id']}_ID.pdf",
            mime="application/pdf"
        )

    else:
        st.error("Member not found.")
        
 
