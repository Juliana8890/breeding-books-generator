import streamlit as st
import pandas as pd
import requests
import json


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

GLOBAL_REGION_CODES = {
    "India": "IN",
    "US": "US",
    "Mercosur": "MS"
}

HT_TYPE_CODES = {
    "Conventional": "CV"
}

MATERIAL_TYPE_CODES = {
    "Hybrid": "HY",
    "Varietal": "VY",
    "Parent Line": "PY",
    "B-line": "BL",
    "R-line": "RL",
    "Specialty": "ZZ"
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
# AI NORMALIZATION MAPS
# ============================================================

REGION_PAZ_MAP = {

    # -----------------------------
    # INDIA
    # -----------------------------

    "India Central": ("India", "CN"),
    "India North East": ("India", "NE"),
    "India North West": ("India", "NW"),
    "India Multi-zone": ("India", "MZ"),

    # -----------------------------
    # US
    # -----------------------------

    "US Southeast": ("US", "SE"),
    "US Multi-zone": ("US", "MZ"),

    # -----------------------------
    # MERCOSUR
    # -----------------------------

    "Southern Brazil & Uruguay": ("Mercosur", "SB"),
    "Mercosur Multi-zone": ("Mercosur", "MZ"),
}


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
# TOP-LEVEL BOOK TYPE
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
# FIELD BOOK NAME GENERATOR
# ============================================================

if book_type == "📍 Field Book Names":

    st.header("📍 Field Book Names Generator")

    st.write(
        "Upload your PAZ / Location / Stage CSV. "
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
        # REQUIRED COLUMNS
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


        # ----------------------------------------------------
        # VIEW INPUT
        # ----------------------------------------------------

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
        # FILTER LOCATIONS
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


        # ----------------------------------------------------
        # SHOW WHAT WILL BE GENERATED
        # ----------------------------------------------------

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
        # GENERATE FIELD BOOKS
        # ====================================================

        if st.button(
            "✨ Generate Field Book Names",
            type="primary",
            width="stretch"
        ):

            output_rows = []


            for _, row in paz_df.iterrows():

                paz = row["PAZ"]
                location = row["Location"]
                stage = row["Stage"]


                # --------------------------------------------
                # FIELD BOOK NAME
                # --------------------------------------------

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
                f"✓ Generated {len(output_df)} Field Book Names."
            )

            st.subheader(
                "Generated Field Book Names"
            )

            st.dataframe(
                output_df,
                width="stretch",
                hide_index=True
            )


            # ------------------------------------------------
            # DOWNLOAD
            # ------------------------------------------------

            csv = (
                output_df
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                label="⬇️ Download Field Book Names CSV",
                data=csv,
                file_name="Field_books_output.csv",
                mime="text/csv",
                width="stretch"
            )


# ============================================================
# ENTRY BOOK NAME GENERATOR
# ============================================================

else:

    st.header("🌾 Entry Book Names Generator")

    st.write(
        "Create standardized Entry Book Names either manually "
        "or by describing what you need in natural language."
    )


    # ========================================================
    # MANUAL / AI TABS
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

        st.subheader("📝 Manual Entry Book Creation")

        st.write(
            "Specify the naming components below. "
            "Book numbers are generated sequentially for "
            "data governance."
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
        # REGION / PAZ
        # ----------------------------------------------------

        st.subheader("Region")

        col1, col2 = st.columns(2)


        with col1:

            manual_region = st.selectbox(
                "Global Region",
                list(GLOBAL_REGION_CODES.keys()),
                key="manual_region"
            )


        with col2:

            if manual_region == "India":

                manual_paz_options = [
                    "CN",
                    "NE",
                    "NW",
                    "MZ"
                ]

            elif manual_region == "US":

                manual_paz_options = [
                    "SE",
                    "MZ"
                ]

            else:

                manual_paz_options = [
                    "SB",
                    "MZ"
                ]


            manual_paz = st.selectbox(
                "PAZ",
                manual_paz_options,
                key="manual_paz"
            )


        # ----------------------------------------------------
        # PRODUCT CONCEPT / HT / MATERIAL
        # ----------------------------------------------------

        st.subheader("Product / Material")

        col1, col2, col3 = st.columns(3)


        with col1:

            manual_product = st.selectbox(
                "Product Concept",
                list(PROGRAM_CODES.keys()),
                key="manual_product"
            )


        with col2:

            manual_ht = st.selectbox(
                "HT Type",
                list(HT_TYPE_CODES.keys()),
                key="manual_ht"
            )


        with col3:

            manual_material = st.selectbox(
                "Material Type",
                list(MATERIAL_TYPE_CODES.keys()),
                key="manual_material"
            )


        # ----------------------------------------------------
        # R&D PHASE
        # ----------------------------------------------------

        manual_phase = st.selectbox(
            "R&D Phase",
            list(RD_PHASE_CODES.keys()),
            key="manual_phase"
        )


        # ----------------------------------------------------
        # NUMBER OF BOOKS
        # ----------------------------------------------------

        manual_number = st.number_input(
            "Number of Books",
            min_value=1,
            max_value=99,
            value=20,
            step=1,
            key="manual_number"
        )


        # ----------------------------------------------------
        # STARTING BOOK NUMBER
        # ----------------------------------------------------

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
            "✨ Generate Entry Book Names",
            type="primary",
            width="stretch",
            key="manual_generate"
        ):

            output_rows = []


            for i in range(
                manual_number
            ):

                book_number = (
                    manual_start + i
                )


                if book_number > 99:

                    st.error(
                        "Book numbers cannot exceed 99 "
                        "because the naming convention uses "
                        "a two-digit index."
                    )

                    break


                book_name = (
                    f"{str(manual_year)[-2:]}"
                    f"{BOOK_TYPE_CODES[manual_book_type]}"
                    f"{SEASON_CODES[manual_season]}"
                    f"_"
                    f"{GLOBAL_REGION_CODES[manual_region]}"
                    f"{manual_paz}"
                    f"{PROGRAM_CODES[manual_product]}"
                    f"_"
                    f"{HT_TYPE_CODES[manual_ht]}"
                    f"_"
                    f"{MATERIAL_TYPE_CODES[manual_material]}"
                    f"{RD_PHASE_CODES[manual_phase]}"
                    f"{book_number:02d}"
                )


                output_rows.append({

                    "Book Number":
                        f"{book_number:02d}",

                    "Year":
                        manual_year,

                    "Book Type":
                        manual_book_type,

                    "Season":
                        manual_season,

                    "Global Region":
                        manual_region,

                    "PAZ":
                        manual_paz,

                    "Product Concept":
                        manual_product,

                    "HT Type":
                        manual_ht,

                    "Material Type":
                        manual_material,

                    "R&D Phase":
                        manual_phase,

                    "Entry Book Name":
                        book_name
                })


            output_df = pd.DataFrame(
                output_rows
            )


            if not output_df.empty:

                st.success(
                    f"✓ Generated {len(output_df)} "
                    "Entry Book Names."
                )

                st.subheader(
                    "Generated Entry Book Names"
                )

                st.dataframe(
                    output_df,
                    width="stretch",
                    hide_index=True
                )


                csv = (
                    output_df
                    .to_csv(index=False)
                    .encode("utf-8")
                )


                st.download_button(
                    label="⬇️ Download Entry Book Names CSV",
                    data=csv,
                    file_name="Entry_books_output.csv",
                    mime="text/csv",
                    width="stretch",
                    key="manual_download"
                )


    # ========================================================
    # AI-ASSISTED ENTRY
    # ========================================================

    with ai_tab:

        st.subheader(
            "✨ AI-Assisted Entry Book Creation"
        )

        st.write(
            "Describe the Entry Books you need in one sentence. "
            "AI will interpret the request and your controlled "
            "naming rules will generate the official names."
        )


        st.caption(
            "Example: Generate 20 Yield Entry Books for 2026 "
            "main season, India Central, Mid-Early, "
            "Conventional Hybrid, H0."
        )


        description = st.text_area(
            "Describe what you need",
            value=(
                "Generate 20 Yield Entry Books for 2026 "
                "main season, India Central, Mid-Early, "
                "Conventional Hybrid, H0."
            ),
            height=120,
            key="ai_description"
        )


        # ====================================================
        # AI FUNCTION
        # ====================================================

        def ask_ai(user_request):

            try:

                api_key = st.secrets[
                    "GROQ_API_KEY"
                ]

            except Exception:

                raise Exception(
                    "GROQ_API_KEY is not configured. "
                    "Add it under Streamlit Secrets."
                )


            system_prompt = """
You are the natural-language interpreter for a
breeding-book naming application.

Your job is ONLY to extract the user's request into
the exact structured fields required by the application.

DO NOT create the final book name.
DO NOT invent codes.
Return JSON only.

============================================================
BOOK TYPE
============================================================

Yield Entry Book = Yield
Nursery Entry Book = Nursery

============================================================
SEASON
============================================================

Main Season = Main Season
Main = Main Season

Off Season = Off Season
Off = Off Season

============================================================
GLOBAL REGION + PAZ
============================================================

INDIA:

India Central
=> global_region = India
=> paz = CN

India North East
=> global_region = India
=> paz = NE

India North West
=> global_region = India
=> paz = NW

India Multi-zone
=> global_region = India
=> paz = MZ


US:

US Southeast
=> global_region = US
=> paz = SE

US Multi-zone
=> global_region = US
=> paz = MZ


MERCOSUR:

Southern Brazil & Uruguay
=> global_region = Mercosur
=> paz = SB

Mercosur Multi-zone
=> global_region = Mercosur
=> paz = MZ


If the user explicitly gives a PAZ code,
preserve the PAZ code.

============================================================
PRODUCT CONCEPT
============================================================

Mid-Early = ME
Medium Maturity = MM
Long Grain = LG

============================================================
HT TYPE
============================================================

Only the following HT type is supported:

Conventional = CV
Conventional Hybrid = CV

Use only supported values.
Do not invent alternative HT types or codes.

============================================================
MATERIAL TYPE
============================================================

Hybrid = HY
Varietal = VY
Parent Line = PY
B-line = BL
R-line = RL
Specialty = ZZ

Use only supported values.
Do not invent alternative material types or codes.

============================================================
R&D PHASE
============================================================

Breeding Trial Stage 1 = 1
Stage 1 = 1

Breeding Trial Stage 2 = 2
Stage 2 = 2

Product Creation = 3
H0 = 3
Product Creation / H0 = 3

Product Advancement = 4
H1 = 4
H1+ = 4
Product Advancement / H1+ = 4

XP = 5
RFYT = 5
XP / RFYT = 5

PYT = 9

============================================================
IMPORTANT INTERPRETATION
============================================================

Example:

"India Central"

must become:

global_region = "India"
paz = "CN"

NOT:

global_region = "India Central"


Example:

"India Multi-zone"

must become:

global_region = "India"
paz = "MZ"


Example:

"Conventional Hybrid"

must become:

ht_type = "CV"
material_type = "HY"


Example:

"H0"

must become:

rd_phase = 3

============================================================
OUTPUT
============================================================

Return exactly these fields:

number_of_books
year
book_type
season
global_region
paz
product_concept
ht_type
material_type
rd_phase

Return JSON only.
"""


            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",

                headers={
                    "Authorization":
                        f"Bearer {api_key}",

                    "Content-Type":
                        "application/json"
                },

                json={

                    "model":
                        "openai/gpt-oss-20b",

                    "messages": [

                        {
                            "role":
                                "system",

                            "content":
                                system_prompt
                        },

                        {
                            "role":
                                "user",

                            "content":
                                user_request
                        }
                    ],

                    "temperature":
                        0,

                    "max_tokens":
                        400,

                    "response_format": {
                        "type":
                            "json_object"
                    }
                },

                timeout=60
            )


            if response.status_code != 200:

                raise Exception(
                    f"AI service returned HTTP "
                    f"{response.status_code}: "
                    f"{response.text}"
                )


            result = response.json()


            content = (
                result["choices"][0]["message"]["content"]
                .strip()
            )


            return json.loads(content)


        # ====================================================
        # AI GENERATE BUTTON
        # ====================================================

        if st.button(
            "✨ Generate from Description",
            type="primary",
            width="stretch",
            key="ai_generate"
        ):

            if not description.strip():

                st.warning(
                    "Please describe the Entry Books "
                    "you need."
                )

            else:

                try:

                    with st.spinner(
                        "✨ AI is interpreting your request..."
                    ):

                        ai_data = ask_ai(
                            description
                        )


                    # ----------------------------------------
                    # REQUIRED FIELDS
                    # ----------------------------------------

                    required_fields = [

                        "number_of_books",
                        "year",
                        "book_type",
                        "season",
                        "global_region",
                        "paz",
                        "product_concept",
                        "ht_type",
                        "material_type",
                        "rd_phase"
                    ]


                    missing = [

                        field

                        for field in required_fields

                        if field not in ai_data
                    ]


                    if missing:

                        raise Exception(
                            "AI response is missing: "
                            + ", ".join(missing)
                        )


                    # ----------------------------------------
                    # CONVERT VALUES
                    # ----------------------------------------

                    number_of_books = int(
                        ai_data["number_of_books"]
                    )

                    ai_year = int(
                        ai_data["year"]
                    )

                    book_type_value = str(
                        ai_data["book_type"]
                    ).strip()

                    season_value = str(
                        ai_data["season"]
                    ).strip()

                    region_value = str(
                        ai_data["global_region"]
                    ).strip()

                    paz_value = str(
                        ai_data["paz"]
                    ).strip().upper()

                    product_value = str(
                        ai_data["product_concept"]
                    ).strip()

                    ht_value = str(
                        ai_data["ht_type"]
                    ).strip()

                    material_value = str(
                        ai_data["material_type"]
                    ).strip()

                    rd_phase = int(
                        ai_data["rd_phase"]
                    )


                    # ----------------------------------------
                    # NORMALIZE BOOK TYPE
                    # ----------------------------------------

                    if book_type_value.lower() == "yield":

                        book_type_value = "Yield"

                    elif book_type_value.lower() == "nursery":

                        book_type_value = "Nursery"

                    else:

                        raise Exception(
                            f"Invalid book type: "
                            f"{book_type_value}"
                        )


                    # ----------------------------------------
                    # NORMALIZE SEASON
                    # ----------------------------------------

                    if season_value.lower() in [
                        "main",
                        "main season"
                    ]:

                        season_value = "Main Season"

                    elif season_value.lower() in [
                        "off",
                        "off season"
                    ]:

                        season_value = "Off Season"

                    else:

                        raise Exception(
                            f"Invalid season: "
                            f"{season_value}"
                        )


                    # ----------------------------------------
                    # NORMALIZE PRODUCT CONCEPT
                    # ----------------------------------------

                    product_lookup = {

                        "me":
                            "ME",

                        "mid-early":
                            "ME",

                        "mid early":
                            "ME",

                        "mm":
                            "MM",

                        "medium maturity":
                            "MM",

                        "lg":
                            "LG",

                        "long grain":
                            "LG"
                    }


                    product_key = (
                        product_value.lower()
                    )


                    if product_key in product_lookup:

                        product_code = (
                            product_lookup[
                                product_key
                            ]
                        )

                    else:

                        raise Exception(
                            f"Invalid product concept: "
                            f"{product_value}"
                        )


                    # ----------------------------------------
                    # NORMALIZE HT
                    # ----------------------------------------

                    ht_lookup = {

                        "cv":
                            "CV",

                        "conventional":
                            "CV",

                        "conventional hybrid":
                            "CV"
                    }


                    ht_key = (
                        ht_value.lower()
                    )


                    if ht_key in ht_lookup:

                        ht_code = ht_lookup[
                            ht_key
                        ]

                    else:

                        raise Exception(
                            f"Invalid HT type: "
                            f"{ht_value}"
                        )


                    # ----------------------------------------
                    # NORMALIZE MATERIAL
                    # ----------------------------------------

                    material_lookup = {

                        "hy":
                            "HY",

                        "hybrid":
                            "HY",

                        "vy":
                            "VY",

                        "varietal":
                            "VY",

                        "py":
                            "PY",

                        "parent":
                            "PY",

                        "parent line":
                            "PY",

                        "bl":
                            "BL",

                        "b-line":
                            "BL",

                        "b line":
                            "BL",

                        "rl":
                            "RL",

                        "r-line":
                            "RL",

                        "r line":
                            "RL",

                        "zz":
                            "ZZ",

                        "specialty":
                            "ZZ"
                    }


                    material_key = (
                        material_value.lower()
                    )


                    if material_key in material_lookup:

                        material_code = (
                            material_lookup[
                                material_key
                            ]
                        )

                    else:

                        raise Exception(
                            f"Invalid material type: "
                            f"{material_value}"
                        )


                    # ----------------------------------------
                    # NORMALIZE R&D PHASE
                    # ----------------------------------------

                    if rd_phase not in [
                        1,
                        2,
                        3,
                        4,
                        5,
                        9
                    ]:

                        raise Exception(
                            f"Invalid R&D phase: "
                            f"{rd_phase}"
                        )


                    # ----------------------------------------
                    # GLOBAL REGION
                    # ----------------------------------------

                    region_lookup = {

                        "india":
                            "IN",

                        "us":
                            "US",

                        "mercosur":
                            "MS"
                    }


                    region_key = (
                        region_value.lower()
                    )


                    if region_key not in region_lookup:

                        raise Exception(
                            f"Invalid global region: "
                            f"{region_value}"
                        )


                    region_code = region_lookup[
                        region_key
                    ]


                    # ----------------------------------------
                    # VALID PAZ
                    # ----------------------------------------

                    valid_paz = {

                        "India": [
                            "CN",
                            "NE",
                            "NW",
                            "MZ"
                        ],

                        "US": [
                            "SE",
                            "MZ"
                        ],

                        "Mercosur": [
                            "SB",
                            "MZ"
                        ]
                    }


                    canonical_region = (

                        {
                            "IN":
                                "India",

                            "US":
                                "US",

                            "MS":
                                "Mercosur"
                        }[
                            region_code
                        ]
                    )


                    if paz_value not in valid_paz[
                        canonical_region
                    ]:

                        raise Exception(
                            f"Invalid PAZ '{paz_value}' "
                            f"for {canonical_region}."
                        )


                    # ----------------------------------------
                    # YEAR VALIDATION
                    # ----------------------------------------

                    if ai_year < 2000 or ai_year > 2099:

                        raise Exception(
                            "Year must be between 2000 and 2099."
                        )


                    # ----------------------------------------
                    # NUMBER VALIDATION
                    # ----------------------------------------

                    if number_of_books < 1:

                        raise Exception(
                            "Number of books must be "
                            "at least 1."
                        )


                    if number_of_books > 99:

                        raise Exception(
                            "The two-digit book index "
                            "allows a maximum of 99 books "
                            "per generated sequence."
                        )


                    # =================================================
                    # AI INTERPRETATION
                    # =================================================

                    st.success(
                        "✓ AI successfully interpreted "
                        "your request."
                    )


                    st.subheader(
                        "🤖 AI Interpretation"
                    )


                    interpretation_df = pd.DataFrame([

                        {
                            "Field":
                                "Number of Books",

                            "Value":
                                number_of_books
                        },

                        {
                            "Field":
                                "Year",

                            "Value":
                                ai_year
                        },

                        {
                            "Field":
                                "Book Type",

                            "Value":
                                book_type_value
                        },

                        {
                            "Field":
                                "Season",

                            "Value":
                                season_value
                        },

                        {
                            "Field":
                                "Global Region",

                            "Value":
                                canonical_region
                        },

                        {
                            "Field":
                                "PAZ",

                            "Value":
                                paz_value
                        },

                        {
                            "Field":
                                "Product Concept",

                            "Value":
                                product_code
                        },

                        {
                            "Field":
                                "HT Type",

                            "Value":
                                ht_code
                        },

                        {
                            "Field":
                                "Material Type",

                            "Value":
                                material_code
                        },

                        {
                            "Field":
                                "R&D Phase",

                            "Value":
                                rd_phase
                        }
                    ])


                    st.dataframe(
                        interpretation_df,
                        width="stretch",
                        hide_index=True
                    )


                    # =================================================
                    # GENERATE ENTRY BOOK NAMES
                    # =================================================

                    output_rows = []


                    for i in range(
                        number_of_books
                    ):

                        book_number = i + 1


                        book_name = (

                            f"{str(ai_year)[-2:]}"

                            f"{BOOK_TYPE_CODES[book_type_value]}"

                            f"{SEASON_CODES[season_value]}"

                            f"_"

                            f"{region_code}"

                            f"{paz_value}"

                            f"{product_code}"

                            f"_"

                            f"{ht_code}"

                            f"_"

                            f"{material_code}"

                            f"{rd_phase}"

                            f"{book_number:02d}"
                        )


                        output_rows.append({

                            "Book Number":
                                f"{book_number:02d}",

                            "Entry Book Name":
                                book_name
                        })


                    output_df = pd.DataFrame(
                        output_rows
                    )


                    st.success(
                        f"✓ Generated "
                        f"{len(output_df)} "
                        f"Entry Book Names."
                    )


                    st.subheader(
                        "Generated Entry Book Names"
                    )


                    st.dataframe(
                        output_df,
                        width="stretch",
                        hide_index=True
                    )


                    # --------------------------------------------
                    # DOWNLOAD
                    # --------------------------------------------

                    csv = (
                        output_df
                        .to_csv(index=False)
                        .encode("utf-8")
                    )


                    st.download_button(
                        label=(
                            "⬇️ Download AI-Generated "
                            "Entry Books CSV"
                        ),

                        data=csv,

                        file_name=(
                            "AI_Entry_books_output.csv"
                        ),

                        mime="text/csv",

                        width="stretch",

                        key="ai_download"
                    )


                    # --------------------------------------------
                    # SHOW AI JSON
                    # --------------------------------------------

                    with st.expander(
                        "🔍 View AI response"
                    ):

                        st.json(ai_data)


                except Exception as e:

                    st.error(
                        "AI response could not be processed: "
                        + str(e)
                    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Breeding Books Generator — AI-assisted prototype"
)
