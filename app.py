import streamlit as st
import pandas as pd
import requests
import json
import re

# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Breeding Books Generator",
    page_icon="🌾",
    layout="wide"
)

# ============================================================
# CONTROLLED VOCABULARIES
# ============================================================

PROGRAM_CODES = {
    "Mid-Early": "ME",
    "Medium Maturity": "MM",
    "Long Grain": "LG"
}

SEASON_CODES = {
    "Main Season": "1",
    "Off Season": "2"
}

BOOK_TYPE_CODES = {
    "Yield": "Y",
    "Nursery": "N"
}

HT_CODES = {
    "Conventional": "CV",
    "FullPage": "FP",
    "MaxAce": "MA"
}

MATERIAL_CODES = {
    "Hybrid": "HY",
    "Varietal": "VY",
    "Parent Line": "PY",
    "B-line Stage 1": "BL1",
    "R-line Stage 1": "RL1",
    "S-line Stage 1": "SL1",
    "Specialty Trial": "ZZ"
}

RD_PHASE_CODES = {
    "Breeding Trial Stage 1": "1",
    "Breeding Trial Stage 2": "2",
    "Product Creation / H0": "3",
    "Product Advancement / H1+": "4",
    "XP / RFYT": "5",
    "PYT": "9"
}

# ============================================================
# REGION / PAZ MAPPING
# ============================================================
#
# IMPORTANT:
# Add or modify zone names here as your company vocabulary grows.
#
# Examples:
# India Central       -> IN + CN
# India Multi-zone    -> IN + MZ
#
# ============================================================

REGION_PAZ_MAP = {

    # ---------------- INDIA ----------------
    "India Central": ("IN", "CN"),
    "India North": ("IN", "NN"),
    "India Northeast": ("IN", "NE"),
    "India Northwest": ("IN", "NW"),
    "India South": ("IN", "SO"),
    "India East": ("IN", "EA"),
    "India West": ("IN", "WE"),
    "India Multi-zone": ("IN", "MZ"),

    # ---------------- US ----------------
    "US Southeast": ("US", "SE"),
    "US South": ("US", "SO"),
    "US Mid-South": ("US", "MS"),
    "US Southwest": ("US", "SW"),
    "US Mid-Atlantic": ("US", "MA"),
    "US Multi-zone": ("US", "MZ"),

    # ---------------- MERCOSUR ----------------
    "Mercosur Southern Brazil & Uruguay": ("MS", "SB"),
    "Mercosur Northern Brazil": ("MS", "NB"),
    "Mercosur Multi-zone": ("MS", "MZ"),
}

# ============================================================
# AI SETTINGS
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"


# ============================================================
# HEADER
# ============================================================

st.title("🌾 Breeding Books Generator")

st.markdown(
    "Generate standardized **Field Book Names and Entry Book Names** "
    "with UBS-compliant naming conventions."
)

st.divider()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """Clean a text value."""
    if value is None:
        return ""
    return str(value).strip()


def get_region_codes(global_region):
    """
    Convert a human-readable global region / PAZ description
    into the two-character global region and two-character PAZ.
    """

    if global_region in REGION_PAZ_MAP:
        return REGION_PAZ_MAP[global_region]

    # Try to handle Multi-zone automatically
    if "Multi-zone" in global_region:
        if global_region.startswith("India"):
            return "IN", "MZ"
        elif global_region.startswith("US"):
            return "US", "MZ"
        elif global_region.startswith("Mercosur"):
            return "MS", "MZ"

    return None, None


def generate_entry_book_names(
    year,
    book_type,
    season,
    global_region,
    product_concept,
    ht_type,
    material_type,
    rd_phase,
    number_of_books,
    starting_number=1
):
    """
    Generate sequential Entry Book names.

    Convention:

    YY + Book Type + Season
    _
    Global Region + PAZ + Product Concept
    _
    HT Type
    _
    Material Type + R&D Phase + sequential book number

    Example:

    26Y1_INCNME_CV_HY301
    """

    region_code, paz_code = get_region_codes(global_region)

    if region_code is None:
        raise ValueError(
            f"Global region / PAZ '{global_region}' is not configured."
        )

    program_code = PROGRAM_CODES[product_concept]
    season_code = SEASON_CODES[season]
    book_code = BOOK_TYPE_CODES[book_type]
    ht_code = HT_CODES[ht_type]
    material_code = MATERIAL_CODES[material_type]
    rd_code = RD_PHASE_CODES[rd_phase]

    year_code = str(year)[-2:]

    rows = []

    for i in range(number_of_books):

        sequence_number = starting_number + i

        book_number = f"{sequence_number:02d}"

        # R&D phase + sequential two-digit index
        suffix = f"{rd_code}{book_number}"

        book_name = (
            f"{year_code}"
            f"{book_code}"
            f"{season_code}"
            f"_{region_code}{paz_code}{program_code}"
            f"_{ht_code}"
            f"_{material_code}{suffix}"
        )

        rows.append({
            "Book Number": sequence_number,
            "Year": year,
            "Book Type": book_type,
            "Season": season,
            "Global Region": global_region,
            "Global Region Code": region_code,
            "PAZ": paz_code,
            "Product Concept": product_concept,
            "HT Type": ht_type,
            "Material Type": material_type,
            "R&D Phase": rd_phase,
            "Entry Book Name": book_name
        })

    return pd.DataFrame(rows)


def call_local_ai(user_request):
    """
    Send the user's natural-language request to Ollama.

    The AI ONLY interprets the request.
    Actual book-name generation is done deterministically
    by Python so the naming convention remains controlled.
    """

    system_prompt = """
You are an assistant for a corporate agricultural breeding
book naming application.

Your ONLY job is to interpret the user's request and return
valid JSON.

Do NOT invent codes.

Use these rules:

BOOK TYPES:
Yield = Y
Nursery = N

SEASONS:
Main Season = 1
Off Season = 2

PRODUCT CONCEPTS:
Mid-Early = ME
Medium Maturity = MM
Long Grain = LG

HT TYPES:
Conventional = CV
FullPage = FP
MaxAce = MA

MATERIAL TYPES:
Hybrid = HY
Varietal = VY
Parent Line = PY
B-line Stage 1 = BL1
R-line Stage 1 = RL1
S-line Stage 1 = SL1
Specialty Trial = ZZ

R&D PHASES:
Breeding Trial Stage 1 = 1
Breeding Trial Stage 2 = 2
Product Creation / H0 = 3
Product Advancement / H1+ = 4
XP / RFYT = 5
PYT = 9

REGION / PAZ INTERPRETATION:

India Central = global_region India, PAZ CN
India North = global_region India, PAZ NN
India Northeast = global_region India, PAZ NE
India Northwest = global_region India, PAZ NW
India South = global_region India, PAZ SO
India East = global_region India, PAZ EA
India West = global_region India, PAZ WE
India Multi-zone = global_region India, PAZ MZ

US Southeast = global_region US, PAZ SE
US South = global_region US, PAZ SO
US Mid-South = global_region US, PAZ MS
US Southwest = global_region US, PAZ SW
US Mid-Atlantic = global_region US, PAZ MA
US Multi-zone = global_region US, PAZ MZ

Mercosur Southern Brazil & Uruguay =
global_region Mercosur, PAZ SB

Mercosur Northern Brazil =
global_region Mercosur, PAZ NB

Mercosur Multi-zone =
global_region Mercosur, PAZ MZ

IMPORTANT:

If the user says:

"Conventional Hybrid"

interpret this as:
HT Type = Conventional
Material Type = Hybrid

If the user says:
"H0"
interpret this as:
R&D Phase = Product Creation / H0

If the user says:
"H1"
or
"H1+"
interpret this as:
R&D Phase = Product Advancement / H1+

Return ONLY this JSON structure:

{
    "number_of_books": 20,
    "year": 2026,
    "book_type": "Yield",
    "season": "Main Season",
    "global_region": "India Central",
    "product_concept": "Mid-Early",
    "ht_type": "Conventional",
    "material_type": "Hybrid",
    "rd_phase": "Product Creation / H0"
}

Do not include markdown.
Do not include explanations.
"""


    payload = {
        "model": OLLAMA_MODEL,
        "prompt": system_prompt + "\n\nUSER REQUEST:\n" + user_request,
        "stream": False,
        "format": "json"
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        ai_text = result.get("response", "").strip()

        return json.loads(ai_text)

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        )

    except Exception as e:

        raise RuntimeError(
            f"AI interpretation failed: {e}"
        )


def validate_ai_request(data):

    required = [
        "number_of_books",
        "year",
        "book_type",
        "season",
        "global_region",
        "product_concept",
        "ht_type",
        "material_type",
        "rd_phase"
    ]

    missing = [
        x for x in required
        if x not in data
    ]

    if missing:
        raise ValueError(
            "AI response is missing: "
            + ", ".join(missing)
        )

    if data["book_type"] not in BOOK_TYPE_CODES:
        raise ValueError("Invalid book type.")

    if data["season"] not in SEASON_CODES:
        raise ValueError("Invalid season.")

    if data["product_concept"] not in PROGRAM_CODES:
        raise ValueError("Invalid product concept.")

    if data["ht_type"] not in HT_CODES:
        raise ValueError("Invalid HT type.")

    if data["material_type"] not in MATERIAL_CODES:
        raise ValueError("Invalid material type.")

    if data["rd_phase"] not in RD_PHASE_CODES:
        raise ValueError("Invalid R&D phase.")

    if get_region_codes(data["global_region"])[0] is None:
        raise ValueError(
            f"Unknown global region / PAZ: "
            f"{data['global_region']}"
        )

    return True


# ============================================================
# BOOK TYPE
# ============================================================

book_type = st.radio(
    "What do you want to generate?",
    [
        "📍 Field Book Names",
        "🌾 Entry Book Names"
    ],
    horizontal=True
)


# ============================================================
# FIELD BOOK GENERATOR
# ============================================================

if book_type == "📍 Field Book Names":

    st.header("📍 Field Book Names Generator")

    st.write(
        "Upload your location file. "
        "The PAZ, Location and Stage information will be taken "
        "directly from the file."
    )

    # --------------------------------------------------------
    # FILE UPLOAD
    # --------------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload Field_books_input.csv",
        type=["csv"]
    )

    if uploaded_file is not None:

        try:

            df = pd.read_csv(uploaded_file)

        except Exception as e:

            st.error(
                f"Could not read the CSV file: {e}"
            )
            st.stop()

        # ----------------------------------------------------
        # CHECK REQUIRED COLUMNS
        # ----------------------------------------------------

        required_columns = {
            "PAZ",
            "Location",
            "Stage"
        }

        missing_columns = (
            required_columns -
            set(df.columns)
        )

        if missing_columns:

            st.error(
                "Your CSV is missing these required columns: "
                + ", ".join(sorted(missing_columns))
            )

            st.info(
                "Required format: PAZ, Location, Stage"
            )

            st.stop()

        # ----------------------------------------------------
        # CLEAN DATA
        # ----------------------------------------------------

        df = df[
            ["PAZ", "Location", "Stage"]
        ].copy()

        df["PAZ"] = (
            df["PAZ"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df["Location"] = (
            df["Location"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df["Stage"] = (
            df["Stage"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df = df[
            (df["PAZ"] != "") &
            (df["Location"] != "") &
            (df["Stage"] != "")
        ]

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        st.success(
            f"✓ Successfully loaded {len(df)} "
            f"location/stage records."
        )

        with st.expander(
            "📄 View uploaded PAZ / Location / Stage file"
        ):

            st.dataframe(
                df,
                width="stretch",
                hide_index=True
            )

        st.divider()

        # ====================================================
        # TRIAL INFORMATION
        # ====================================================

        st.subheader("Trial Information")

        col1, col2, col3 = st.columns(3)

        with col1:

            year = st.number_input(
                "Year",
                min_value=2000,
                max_value=2099,
                value=2026,
                step=1
            )

        with col2:

            season = st.selectbox(
                "Season",
                list(SEASON_CODES.keys())
            )

        with col3:

            program = st.selectbox(
                "Program",
                list(PROGRAM_CODES.keys())
            )

        # ----------------------------------------------------
        # PAZ
        # ----------------------------------------------------

        available_paz = sorted(
            df["PAZ"]
            .dropna()
            .unique()
            .tolist()
        )

        paz_options = [
            "ALL ZONES"
        ] + available_paz

        st.subheader("PAZ")

        selected_paz = st.selectbox(
            "Select PAZ",
            paz_options
        )

        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        if selected_paz == "ALL ZONES":

            paz_df = df.copy()

        else:

            paz_df = df[
                df["PAZ"] == selected_paz
            ].copy()

        st.info(
            f"📍 {len(paz_df)} locations found for "
            f"{selected_paz}. "
            "All stages in the uploaded file will be used."
        )

        with st.expander(
            f"View {selected_paz} locations and stages"
        ):

            st.dataframe(
                paz_df,
                width="stretch",
                hide_index=True
            )

        st.divider()

        # ====================================================
        # GENERATE
        # ====================================================

        if st.button(
            "✨ Generate Field Books",
            type="primary",
            width="stretch"
        ):

            output_rows = []

            for _, row in paz_df.iterrows():

                paz = row["PAZ"]
                location = row["Location"]
                stage = row["Stage"]

                book_name = (
                    f"{str(year)[-2:]}"
                    f"Y{SEASON_CODES[season]}"
                    f"_{location}"
                    f"_{PROGRAM_CODES[program]}"
                    f"_{stage}"
                    f"_{paz}"
                )

                output_rows.append({
                    "PAZ": paz,
                    "Location": location,
                    "Stage": stage,
                    "Program": PROGRAM_CODES[program],
                    "Field Book Name": book_name
                })

            output_df = pd.DataFrame(
                output_rows
            )

            st.success(
                f"✓ Generated {len(output_df)} Field Books."
            )

            st.subheader(
                "Generated Field Books"
            )

            st.dataframe(
                output_df,
                width="stretch",
                hide_index=True
            )

            csv = output_df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="⬇️ Download Field Books CSV",
                data=csv,
                file_name="Field_books_output.csv",
                mime="text/csv",
                width="stretch"
            )


# ============================================================
# ENTRY BOOK GENERATOR
# ============================================================

else:

    st.header("🌾 Entry Book Names Generator")

    st.write(
        "Create standardized Entry Book Names either manually "
        "or by describing what you need in natural language."
    )

    # ========================================================
    # TABS
    # ========================================================

    manual_tab, ai_tab = st.tabs(
        [
            "📝 Manual Entry",
            "✨ AI-Assisted Entry"
        ]
    )


    # ========================================================
    # MANUAL ENTRY
    # ========================================================

    with manual_tab:

        st.subheader("Manual Entry Book Creation")

        st.caption(
            "Select the required trial characteristics. "
            "Book numbers are generated sequentially."
        )

        # ----------------------------------------------------
        # BASIC INFORMATION
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            manual_year = st.number_input(
                "Year",
                min_value=2000,
                max_value=2099,
                value=2026,
                step=1,
                key="manual_year"
            )

        with col2:

            manual_book_type = st.selectbox(
                "Book Type",
                list(BOOK_TYPE_CODES.keys()),
                key="manual_book_type"
            )

        with col3:

            manual_season = st.selectbox(
                "Season",
                list(SEASON_CODES.keys()),
                key="manual_season"
            )

        # ----------------------------------------------------
        # REGION
        # ----------------------------------------------------

        manual_region = st.selectbox(
            "Global Region / PAZ",
            list(REGION_PAZ_MAP.keys()),
            key="manual_region"
        )

        region_code, paz_code = get_region_codes(
            manual_region
        )

        st.info(
            f"Selected region will be coded as "
            f"**{region_code}{paz_code}**"
        )

        # ----------------------------------------------------
        # PRODUCT / HT / MATERIAL
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            manual_program = st.selectbox(
                "Product Concept",
                list(PROGRAM_CODES.keys()),
                key="manual_program"
            )

        with col2:

            manual_ht = st.selectbox(
                "HT Type",
                list(HT_CODES.keys()),
                key="manual_ht"
            )

        with col3:

            manual_material = st.selectbox(
                "Material Type",
                list(MATERIAL_CODES.keys()),
                key="manual_material"
            )

        # ----------------------------------------------------
        # R&D PHASE
        # ----------------------------------------------------

        manual_rd = st.selectbox(
            "R&D Phase",
            list(RD_PHASE_CODES.keys()),
            key="manual_rd"
        )

        # ----------------------------------------------------
        # BOOK NUMBERING
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            manual_number = st.number_input(
                "Number of Books",
                min_value=1,
                max_value=999,
                value=20,
                step=1,
                key="manual_number"
            )

        with col2:

            manual_start = st.number_input(
                "Starting Book Number",
                min_value=1,
                max_value=99,
                value=1,
                step=1,
                key="manual_start"
            )

        # ----------------------------------------------------
        # GENERATE
        # ----------------------------------------------------

        if st.button(
            "✨ Generate Entry Books",
            type="primary",
            width="stretch",
            key="manual_generate"
        ):

            try:

                output_df = generate_entry_book_names(
                    year=manual_year,
                    book_type=manual_book_type,
                    season=manual_season,
                    global_region=manual_region,
                    product_concept=manual_program,
                    ht_type=manual_ht,
                    material_type=manual_material,
                    rd_phase=manual_rd,
                    number_of_books=manual_number,
                    starting_number=manual_start
                )

                st.success(
                    f"✓ Generated {len(output_df)} Entry Books."
                )

                st.dataframe(
                    output_df,
                    width="stretch",
                    hide_index=True
                )

                csv = output_df.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    label="⬇️ Download Entry Books CSV",
                    data=csv,
                    file_name="Entry_books_output.csv",
                    mime="text/csv",
                    width="stretch",
                    key="manual_download"
                )

            except Exception as e:

                st.error(
                    f"Could not generate Entry Books: {e}"
                )


    # ========================================================
    # AI ENTRY
    # ========================================================

    with ai_tab:

        st.subheader("✨ AI-Assisted Entry Book Creation")

        st.write(
            "Describe the Entry Books you need in one sentence."
        )

        st.caption(
            "Example: Generate 20 Yield Entry Books for "
            "2026 main season, India Central, Mid-Early, "
            "Conventional Hybrid, H0."
        )

        ai_request = st.text_area(
            "Describe what you need",
            height=120,
            placeholder=(
                "Generate 20 Yield Entry Books for 2026 "
                "main season, India Central, Mid-Early, "
                "Conventional Hybrid, H0."
            ),
            key="ai_request"
        )

        if st.button(
            "✨ Generate from Description",
            type="primary",
            width="stretch",
            key="ai_generate"
        ):

            if not ai_request.strip():

                st.warning(
                    "Please describe the Entry Books you need."
                )

            else:

                with st.spinner(
                    "🤖 AI is interpreting your request..."
                ):

                    try:

                        ai_data = call_local_ai(
                            ai_request
                        )

                        # ------------------------------------
                        # SHOW AI INTERPRETATION
                        # ------------------------------------

                        with st.expander(
                            "🔎 View AI interpretation",
                            expanded=True
                        ):

                            st.json(ai_data)

                        # ------------------------------------
                        # VALIDATE
                        # ------------------------------------

                        validate_ai_request(
                            ai_data
                        )

                        # ------------------------------------
                        # GENERATE
                        # ------------------------------------

                        output_df = generate_entry_book_names(
                            year=int(
                                ai_data["year"]
                            ),
                            book_type=ai_data["book_type"],
                            season=ai_data["season"],
                            global_region=ai_data["global_region"],
                            product_concept=ai_data[
                                "product_concept"
                            ],
                            ht_type=ai_data["ht_type"],
                            material_type=ai_data[
                                "material_type"
                            ],
                            rd_phase=ai_data["rd_phase"],
                            number_of_books=int(
                                ai_data["number_of_books"]
                            ),
                            starting_number=1
                        )

                        # ------------------------------------
                        # SUCCESS
                        # ------------------------------------

                        st.success(
                            f"✓ AI interpreted your request "
                            f"and generated "
                            f"{len(output_df)} Entry Books."
                        )

                        # ------------------------------------
                        # SUMMARY
                        # ------------------------------------

                        region_code, paz_code = get_region_codes(
                            ai_data["global_region"]
                        )

                        st.info(
                            f"**Naming interpretation:** "
                            f"{ai_data['global_region']} → "
                            f"**{region_code}{paz_code}** | "
                            f"{ai_data['product_concept']} → "
                            f"**{PROGRAM_CODES[ai_data['product_concept']]}** | "
                            f"{ai_data['ht_type']} → "
                            f"**{HT_CODES[ai_data['ht_type']]}** | "
                            f"{ai_data['material_type']} → "
                            f"**{MATERIAL_CODES[ai_data['material_type']]}** | "
                            f"{ai_data['rd_phase']} → "
                            f"**{RD_PHASE_CODES[ai_data['rd_phase']]}**"
                        )

                        # ------------------------------------
                        # RESULT
                        # ------------------------------------

                        st.subheader(
                            "Generated Entry Books"
                        )

                        st.dataframe(
                            output_df,
                            width="stretch",
                            hide_index=True
                        )

                        # ------------------------------------
                        # DOWNLOAD
                        # ------------------------------------

                        csv = output_df.to_csv(
                            index=False
                        ).encode("utf-8")

                        st.download_button(
                            label="⬇️ Download Entry Books CSV",
                            data=csv,
                            file_name="AI_Entry_books_output.csv",
                            mime="text/csv",
                            width="stretch",
                            key="ai_download"
                        )

                    except Exception as e:

                        st.error(
                            f"AI response could not be validated: {e}"
                        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Breeding Books Generator — AI-assisted prototype"
)