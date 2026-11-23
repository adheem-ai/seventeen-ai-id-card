import io
from datetime import datetime

import qrcode
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
from supabase import create_client


# --------------------------------------------------
# FONT FUNCTION
# --------------------------------------------------
def get_font(size):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            size
        )
    except OSError:
        return ImageFont.load_default()


# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------
st.set_page_config(
    page_title="SEVENTEEN AI Membership",
    page_icon="🪪",
    layout="centered"
)


# --------------------------------------------------
# CONNECT TO SUPABASE
# --------------------------------------------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

BUCKET = "members_photos"

st.title("SEVENTEEN AI")
st.subheader("Digital Membership System")


# --------------------------------------------------
# PUBLIC QR VERIFICATION
# --------------------------------------------------
params = st.query_params
verify_id = params.get("verify")

if verify_id:
    st.header("Membership Verification")

    try:
        result = (
            supabase.table("members")
            .select("*")
            .eq("member_id", verify_id)
            .execute()
        )

        if result.data:
            member = result.data[0]

            st.success("✓ VERIFIED MEMBER")
            st.write("**Name:**", member.get("full_name", ""))
            st.write("**Membership ID:**", member.get("member_id", ""))
            st.write("**Role:**", member.get("role", ""))
            st.write(
                "**Department:**",
                member.get("department") or "Not specified"
            )

            if member.get("photo_path"):
                st.image(member["photo_path"], width=180)
        else:
            st.error("Membership not found.")

    except Exception as e:
        st.error(f"Verification error: {e}")

    st.stop()


# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------
st.sidebar.title("Administration")

admin_password = st.secrets["ADMIN_PASSWORD"]

entered_password = st.sidebar.text_input(
    "Admin Password",
    type="password"
)

if entered_password != admin_password:
    st.info("Welcome to SEVENTEEN AI Digital Membership.")
    st.warning(
        "Administrator login is required to register and manage members."
    )
    st.stop()


# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------
st.divider()
st.header("SEVENTEEN AI Admin Dashboard")

try:
    dashboard_data = (
        supabase.table("members")
        .select("member_id, full_name, role, department, email")
        .execute()
    )

    members = dashboard_data.data or []

    total_members = len(members)

    departments = {
        member.get("department")
        for member in members
        if member.get("department")
    }

    roles = {
        member.get("role")
        for member in members
        if member.get("role")
    }

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Members", total_members)
    col2.metric("Departments", len(departments))
    col3.metric("Different Roles", len(roles))

    st.subheader("Registered Members")

    if members:
        st.dataframe(members, use_container_width=True)
    else:
        st.info("No members registered yet.")

except Exception as e:
    st.error(f"Dashboard error: {e}")


# --------------------------------------------------
# MEMBER MANAGEMENT
# --------------------------------------------------
st.divider()
st.header("Member Management")

try:
    all_members = (
        supabase.table("members")
        .select("member_id, full_name, email, role, department")
        .execute()
    )

    member_list = all_members.data or []

    if member_list:
        member_options = {
            f"{member['member_id']} - {member['full_name']}":
                member["member_id"]
            for member in member_list
        }

        selected_member = st.selectbox(
            "Select a member",
            list(member_options.keys())
        )

        selected_id = member_options[selected_member]

        selected_result = (
            supabase.table("members")
            .select("*")
            .eq("member_id", selected_id)
            .execute()
        )

        if selected_result.data:
            member = selected_result.data[0]

            with st.form("edit_member_form"):
                st.subheader("Edit Member Details")

                new_name = st.text_input(
                    "Full Name",
                    value=member.get("full_name", "")
                )

                new_email = st.text_input(
                    "Email",
                    value=member.get("email", "")
                )

                new_role = st.text_input(
                    "Role",
                    value=member.get("role", "")
                )

                new_department = st.text_input(
                    "Department",
                    value=member.get("department") or ""
                )
                new_status = st.selectbox(
                    "Membership Status",
                    ["Active", "Inactive"]
                )

                confirm_delete = st.checkbox(
                    f"I understand that {member.get('full_name', 'this member')} "
                    "will be permanently deleted."
                )

                save_button = st.form_submit_button("Save Changes")
                delete_button = st.form_submit_button("Delete Member")

            if save_button:
                if not new_name.strip() or not new_email.strip() or not new_role.strip():
                    st.error("Name, email, and role cannot be empty.")
                else:
                    try:
                        (
                            supabase.table("members")
                            .update({
                                "full_name": new_name.strip(),
                                "email": new_email.strip().lower(),
                                "role": new_role.strip(),
                                "department": new_department.strip(),
                                "status": new_status
                            })
                            .eq("member_id", selected_id)
                            .execute()
                        )

                        st.success("Member details updated successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Could not update member: {e}")

            if delete_button:
                if confirm_delete:
                    try:
                        (
                            supabase.table("members")
                            .delete()
                            .eq("member_id", selected_id)
                            .execute()
                        )

                        st.success("Member deleted successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Could not delete member: {e}")
                else:
                    st.warning(
                        "Please tick the confirmation box before deleting."
                    )
        else:
            st.warning("The selected member could not be found.")

    else:
        st.info("No members available to manage.")

except Exception as e:
    st.error(f"Member management error: {e}")


# --------------------------------------------------
# REGISTER NEW MEMBER
# --------------------------------------------------
st.divider()
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
    if not full_name.strip() or not email.strip() or not role.strip() or photo is None:
        st.error("Please complete all required fields and upload a photograph.")
    else:
        try:
            year = datetime.now().year

            existing = (
                supabase.table("members")
                .select("member_id")
                .like("member_id", f"SAI-{year}-%")
                .execute()
            )

            numbers = []
            for item in existing.data or []:
                try:
                    numbers.append(int(item["member_id"].split("-")[-1]))
                except (ValueError, IndexError, KeyError):
                    continue

            next_number = max(numbers, default=0) + 1
            member_id = f"SAI-{year}-{next_number:03d}"

            extension = photo.name.rsplit(".", 1)[-1].lower()
            photo_path = f"{member_id}.{extension}"

            supabase.storage.from_(BUCKET).upload(
                photo_path,
                photo.getvalue(),
                {"content-type": photo.type}
            )

            photo_url = supabase.storage.from_(BUCKET).get_public_url(
                photo_path
            )

            member_data = {
                "member_id": member_id,
                "full_name": full_name.strip(),
                "email": email.strip().lower(),
                "role": role.strip(),
                "department": department.strip(),
                "photo_path": photo_url
            }

            (
                supabase.table("members")
                .insert(member_data)
                .execute()
            )

            st.success("Member registered successfully!")
            st.write("Membership ID:", member_id)

        except Exception as e:
            st.error(f"Registration failed: {e}")


# --------------------------------------------------
# MEMBER SEARCH
# --------------------------------------------------
st.divider()
st.header("Find a Member")

search_id = st.text_input("Enter Membership ID")

if st.button("Search Member"):
    try:
        result = (
            supabase.table("members")
            .select("*")
            .eq("member_id", search_id.strip())
            .execute()
        )

        if result.data:
            member = result.data[0]

            st.success("Member found!")

            if member.get("photo_path"):
                st.image(member["photo_path"], width=180)

            st.subheader(member.get("full_name", ""))
            st.write("Membership ID:", member.get("member_id", ""))
            st.write("Role:", member.get("role", ""))
            st.write(
                "Department:",
                member.get("department") or "Not specified"
            )
            st.write("Email:", member.get("email", ""))

            # --------------------------------------------------
            # VERIFICATION QR CODE
            # --------------------------------------------------
            app_url = st.secrets["APP_URL"].rstrip("/")
            verification_url = (
                f"{app_url}/?verify={member['member_id']}"
            )

            qr = qrcode.make(verification_url)

            # --------------------------------------------------
            # CREATE ID CARD
            # --------------------------------------------------
            card = Image.new(
                "RGB",
                (1200, 750),
                "#101B35"
            )

            draw = ImageDraw.Draw(card)

            white = "#FFFFFF"
            silver = "#B8C5D8"

            # CARD BORDER
            draw.rounded_rectangle(
                (35, 35, 1165, 715),
                radius=35,
                outline=silver,
                width=5
            )

            # LOGO AND HEADER
            try:
                logo = Image.open("logo.jpg").convert("RGBA")
                logo.thumbnail((100, 100))
                card.paste(logo, (85, 65), logo)

            except Exception as e:
                st.error(f"Logo could not be loaded: {e}")
                st.stop()

            draw.text(
                (210, 80),
                "SEVENTEEN AI",
                fill=white,
                font=get_font(58)
            )

            draw.text(
                (210, 155),
                "INTELLIGENCE  |  INNOVATION  |  IMPACT",
                fill=silver,
                font=get_font(20)
            )

            draw.line(
                (80, 215, 1120, 215),
                fill=silver,
                width=3
            )

            # MEMBER PHOTOGRAPH
            try:
                response = requests.get(
                    member["photo_path"],
                    timeout=20
                )
                response.raise_for_status()

                photo_image = Image.open(
                    io.BytesIO(response.content)
                ).convert("RGB")

                photo_image = ImageOps.fit(
                    photo_image,
                    (330, 390)
                )

                card.paste(photo_image, (85, 265))

            except Exception as e:
                st.error(f"Could not load member photograph: {e}")
                st.stop()

            # MEMBER DETAILS
            draw.text(
                (465, 280),
                member.get("full_name", ""),
                fill=white,
                font=get_font(38)
            )

            draw.text(
                (465, 365),
                "POSITION / ROLE",
                fill=silver,
                font=get_font(22)
            )

            draw.text(
                (465, 405),
                member.get("role", ""),
                fill=white,
                font=get_font(28)
            )

            draw.text(
                (465, 465),
                "DEPARTMENT",
                fill=silver,
                font=get_font(22)
            )

            draw.text(
                (465, 505),
                member.get("department") or "Not specified",
                fill=white,
                font=get_font(28)
            )

            draw.text(
                (465, 565),
                "MEMBERSHIP ID",
                fill=silver,
                font=get_font(22)
            )

            draw.text(
                (465, 605),
                member.get("member_id", ""),
                fill=white,
                font=get_font(32)
            )

            # QR CODE ON CARD
            qr_image = qr.convert("RGB").resize((190, 190))
            card.paste(qr_image, (900, 465))

            draw.text(
                (895, 665),
                "SCAN TO VERIFY",
                fill=silver,
                font=get_font(20)
            )

            # DISPLAY DIGITAL ID CARD
            st.divider()
            st.subheader("SEVENTEEN AI Digital ID Card")

            st.image(
                card,
                use_container_width=True
            )

            # DOWNLOAD PNG
            png_buffer = io.BytesIO()
            card.save(png_buffer, format="PNG")

            st.download_button(
                "Download ID Card (PNG)",
                data=png_buffer.getvalue(),
                file_name=f"{member['member_id']}_ID.png",
                mime="image/png"
            )

            # DOWNLOAD PDF
            pdf_buffer = io.BytesIO()
            card.save(
                pdf_buffer,
                format="PDF",
                resolution=150
            )

            st.download_button(
                "Download ID Card (PDF)",
                data=pdf_buffer.getvalue(),
                file_name=f"{member['member_id']}_ID.pdf",
                mime="application/pdf"
            )

        else:
            st.error("Member not found.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

