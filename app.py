
'''import streamlit as st
import qrcode
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from supabase import create_client


# FONT FUNCTION
def get_font(size):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            size
        )
    except OSError:
        return ImageFont.load_default()


# PAGE SETTINGS
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

        if member.get("photo_path"):
            st.image(member["photo_path"], width=180)

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
    st.warning(
        "Administrator login is required to register members."
    )
    st.stop()

# MEMBER MANAGEMENT
st.divider()
st.header("Member Management")

try:
    all_members = supabase.table("members").select(
        "member_id, full_name, email, role, department"
    ).execute()

    member_list = all_members.data or []

    if member_list:
        member_options = {
            f"{m['member_id']} - {m['full_name']}": m["member_id"]
            for m in member_list
        }

        selected_member = st.selectbox(
            "Select a member",
            list(member_options.keys())
        )

        selected_id = member_options[selected_member]

        result = supabase.table("members").select("*").eq(
            "member_id", selected_id
        ).execute()

        member = result.data[0]

        with st.form("edit_member_form"):
            st.subheader("Edit Member Details")

            new_name = st.text_input(
                "Full Name", value=member["full_name"]
            )

            new_email = st.text_input(
                "Email", value=member["email"]
            )

            new_role = st.text_input(
                "Role", value=member["role"]
            )

            new_department = st.text_input(
                "Department", value=member.get("department") or ""
            )

            confirm_delete = st.checkbox(
    f"I understand that {member['full_name']} will be permanently deleted."
            )

            save_button = st.form_submit_button("Save Changes")
            delete_button = st.form_submit_button("Delete Member")

                        if save_button:
                supabase.table("members").update({
                    "full_name": new_name,
                    "email": new_email,
                    "role": new_role,
                    "department": new_department
                }).eq("member_id", selected_id).execute()

                st.success("Member details updated successfully!")
                st.rerun()

            if delete_button:
                if confirm_delete:
                    supabase.table("members").delete().eq(
                        "member_id", selected_id
                    ).execute()

                    st.success("Member deleted successfully!")
                    st.rerun()
                else:
                    st.warning(
                        "Please tick the confirmation box before deleting."
                    )

    else:
        st.info("No members available to manage.")

except Exception as e:
    st.error(f"Member management error: {e}")
except Exception as e:
    st.error(f"Member management error: {e}")
# REGISTER NEW MEMBER

# ADMIN DASHBOARD
st.divider()
st.header("SEVENTEEN AI Admin Dashboard")

try:
    dashboard_data = supabase.table("members").select(
        "member_id, full_name, role, department, email"
    ).execute()

    members = dashboard_data.data or []

    total_members = len(members)

    departments = set(
        m["department"]
        for m in members
        if m.get("department")
    )

    roles = set(
        m["role"]
        for m in members
        if m.get("role")
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Members", total_members)
    col2.metric("Departments", len(departments))
    col3.metric("Different Roles", len(roles))

    st.subheader("Registered Members")

    if members:
        st.dataframe(
            members,
            use_container_width=True
        )
    else:
        st.info("No members registered yet.")

except Exception as e:
    st.error(f"Dashboard error: {e}")

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
                ).like(
                    "member_id", f"SAI-{year}-%"
                ).execute()

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
                    photo.getv
'''
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

