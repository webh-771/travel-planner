import streamlit as st
import google.generativeai as ggi
from datetime import date, timedelta
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        body {
            background-color: #f0f5f9;
            color: #333333;
        }
        .main {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 20px;
        }
        h1 {
            color: #1E90FF; /* DodgerBlue */
            font-family: 'Helvetica', sans-serif;
            text-align: center;
        }
        h2, h3 {
            color: #2F4F4F; /* DarkSlateGray */
            font-family: 'Arial', sans-serif;
        }
        .stButton > button {
            background-color: #1E90FF;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
            font-size: 16px;
            font-weight: bold;
            width: 100%;
        }
        .stButton > button:hover {
            background-color: #1C86EE; /* A slightly darker blue */
        }
        .card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.1);
            border: 1px solid #e6e6e6;
        }
        .st-emotion-cache-16txtl3 {
             padding: 2rem 1rem; /* Reduce sidebar padding */
        }
        .sidebar .sidebar-content {
            background-color: #F8F9FA;
        }
    </style>
""", unsafe_allow_html=True)


# --- Sidebar for API Key and Navigation ---
st.sidebar.markdown("<h2 style='color: #1E90FF;'>📋 Menu</h2>", unsafe_allow_html=True)
api_key = st.sidebar.text_input("Enter your Google AI API Key", type="password", help="Get your key from Google AI Studio.")

# --- Main Application Logic ---
# The app will only run if an API key is provided.
if api_key:
    try:
        ggi.configure(api_key=api_key)
        model = ggi.GenerativeModel("gemini-pro")
        chat = model.start_chat()
    except Exception as e:
        st.error(f"Failed to configure Google AI: {e}")
        st.stop() # Stop execution if API key is invalid

    # --- Function Definitions ---
    def budget_calculator():
        """Displays the budget calculation interface."""
        st.markdown("<h1>💰 Travel Budget Calculator</h1>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<h3>Please provide your estimated expenses in the following categories:</h3>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                transport_budget = st.number_input("Transport Budget (₹)", min_value=0, max_value=100000, step=1000, value=1000)
                food_budget = st.number_input("Food Budget (₹)", min_value=0, max_value=50000, step=500, value=1000)
            with col2:
                stay_budget = st.number_input("Accommodation Budget (₹)", min_value=0, max_value=100000, step=1000, value=1000)
                other_expenses = st.number_input("Miscellaneous Expenses (₹)", min_value=0, max_value=50000, step=500, value=500)
            
            total_budget = transport_budget + food_budget + stay_budget + other_expenses

            st.markdown("---")
            st.markdown("<h3>Adjustments & Analysis</h3>", unsafe_allow_html=True)
            
            col3, col4 = st.columns(2)
            with col3:
                inflation_rate = st.slider("Inflation Rate (%)", 0, 20, 5)
                inflation_adjusted_budget = total_budget * (1 + inflation_rate / 100)
                num_days = st.slider("Number of Travel Days", 1, 30, 7)
                cost_per_day = total_budget / num_days if num_days > 0 else 0
            
            with col4:
                currency_conversion = st.checkbox("Need to convert to another currency?")
                foreign_currency_budget = None
                if currency_conversion:
                    conversion_rate = st.number_input("Enter Conversion Rate (₹ to Foreign Currency)", min_value=0.01, value=1.0, step=0.01)
                    foreign_currency_budget = inflation_adjusted_budget / conversion_rate if conversion_rate > 0 else 0


            st.markdown("---")
            st.markdown("<h3>Budget Summary</h3>", unsafe_allow_html=True)
            
            summary_col1, summary_col2 = st.columns(2)
            with summary_col1:
                st.metric(label="Total Budget (pre-inflation)", value=f"₹{total_budget:,.2f}")
                st.metric(label="Cost Per Day", value=f"₹{cost_per_day:,.2f}")
                st.metric(label="Total Budget (post-inflation)", value=f"₹{inflation_adjusted_budget:,.2f}", delta=f"{inflation_rate}% inflation")
                if foreign_currency_budget is not None:
                    st.metric(label="Budget in Foreign Currency", value=f"{foreign_currency_budget:,.2f}")

            # --- Pie Chart for Budget Breakdown ---
            with summary_col2:
                st.markdown("<h5>Budget Distribution</h5>", unsafe_allow_html=True)
                if total_budget > 0:
                    categories = ['Transport', 'Food', 'Accommodation', 'Miscellaneous']
                    values = [transport_budget, food_budget, stay_budget, other_expenses]
                    
                    fig, ax = plt.subplots()
                    ax.pie(values, labels=categories, autopct='%1.1f%%', startangle=90,
                           colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                    st.pyplot(fig)
                else:
                    st.info("Enter budget values to see the distribution chart.")

    def call_gemini_ai(prompt):
        """Sends a prompt to the Gemini model and returns the response."""
        try:
            with st.spinner("Generating your personalized travel plan..."):
                response = chat.send_message(prompt, stream=True)
                generated_text = ''.join([word.text for word in response])
            return generated_text
        except Exception as e:
            st.error(f"Error communicating with Gemini: {e}")
            return ""

    # Initialize session state for storing travel plans
    if 'travel_planner_db' not in st.session_state:
        st.session_state['travel_planner_db'] = {}

    def add_travel_plan(from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, plan):
        """Adds a new travel plan to the session state."""
        plan_id = len(st.session_state['travel_planner_db']) + 1
        st.session_state['travel_planner_db'][plan_id] = {
            "from_destination": from_destination,
            "to_destination": to_destination,
            "start_date": start_date,
            "end_date": end_date,
            "total_budget": total_budget,
            "budget_breakdown": budget_breakdown,
            "plan": plan
        }

    def set_operations_popup():
        """Displays a popup with set operations on sample city data."""
        with st.expander("Show Set Operations Example"):
            st.markdown("<h2>Set Operations on Cities</h2>", unsafe_allow_html=True)
            set1 = {'Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad'}
            set2 = {'Pune', 'Delhi', 'Kolkata', 'Bengaluru'}
            
            st.write(f"**Set 1 (Major Hubs):** `{set1}`")
            st.write(f"**Set 2 (Other Metros):** `{set2}`")
            st.markdown("---")

            set_operations_dict = {
                'Union (All unique cities)': set1.union(set2),
                'Intersection (Cities in both sets)': set1.intersection(set2),
                'Difference (Hubs not in Metros)': set1.difference(set2),
                'Symmetric Difference (Cities in one set but not both)': set1.symmetric_difference(set2)
            }

            for operation, result in set_operations_dict.items():
                st.write(f"**{operation}:** `{result}`")

    def get_travel_details():
        """Gathers travel details from the user via input widgets."""
        st.markdown("<h3>Where do you want to go? 🌎</h3>", unsafe_allow_html=True)
        cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Surat', 'Pune', 'Jaipur', 'Gokarna', 'Palanpur', 'Goa', 'Manali']

        col1, col2 = st.columns(2)
        with col1:
            from_destination = st.selectbox("Where are you starting from?", cities, index=0)
            start_date = st.date_input("Start date", min_value=date.today())
        with col2:
            to_destination = st.selectbox("Where do you want to go?", cities, index=1)
            end_date = st.date_input("End date", min_value=start_date, value=start_date + timedelta(days=6))

        if start_date > end_date:
            st.error("End date must be on or after the start date.")
            st.stop()
        
        st.markdown("<h3>What's your budget? 💰</h3>", unsafe_allow_html=True)
        col3, col4, col5 = st.columns(3)
        with col3:
            food_budget = st.slider("Food Budget (₹)", 1000, 50000, 5000, step=1000)
        with col4:
            stay_budget = st.slider("Stay Budget (₹)", 1000, 100000, 10000, step=1000)
        with col5:
            other_budget = st.slider("Other Expenses (₹)", 1000, 50000, 3000, step=1000)
        
        total_budget = food_budget + stay_budget + other_budget
        budget_breakdown = f"Food: ₹{food_budget}, Stay: ₹{stay_budget}, Other: ₹{other_budget}, Total: ₹{total_budget}"
        days = (end_date - start_date).days + 1
        
        query = f"Plan a detailed, day-by-day trip from {from_destination} to {to_destination} for {days} days with a total budget of ₹{total_budget}. The budget breakdown is as follows: {budget_breakdown}. Provide recommendations for travel, accommodation, and activities that fit this budget. Make it sound exciting and personal."
        
        return from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, query

    # --- Page Navigation ---
    choice = st.sidebar.radio("Go to", ["Travel Planner", "Budget Calculator", "View Saved Plans"])

    if choice == "Travel Planner":
        st.markdown("<h1>✈️ AI Travel Planner 🌍</h1>", unsafe_allow_html=True)
        
        with st.form(key="travel_form"):
            from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, query = get_travel_details()
            submit_button = st.form_submit_button(label='Generate Travel Plan')

        if submit_button:
            if not all([from_destination, to_destination, start_date, end_date, total_budget]):
                st.error("Please provide all the details to generate the plan.")
            else:
                plan = call_gemini_ai(query)
                if plan:
                    add_travel_plan(from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, plan)
                    st.success("Travel plan generated successfully!")
                    st.balloons()
                    
                    st.markdown("---")
                    st.markdown("## Your Generated Itinerary")
                    
                    # Display the newly generated plan
                    st.markdown(f"**Trip:** {from_destination} to {to_destination}")
                    st.markdown(f"**Dates:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
                    st.markdown(f"**Budget Breakdown:** {budget_breakdown}")
                    st.markdown("---")
                    st.markdown(plan)

        set_operations_popup()

    elif choice == "Budget Calculator":
        budget_calculator()

    elif choice == "View Saved Plans":
        st.markdown("<h1>📚 Your Saved Travel Plans</h1>", unsafe_allow_html=True)
        if not st.session_state['travel_planner_db']:
            st.info("You haven't generated any travel plans yet. Go to the 'Travel Planner' to create one!")
        else:
            for plan_id, plan_details in st.session_state['travel_planner_db'].items():
                with st.expander(f"Plan #{plan_id}: {plan_details['from_destination']} to {plan_details['to_destination']}"):
                    st.markdown(f"**From:** {plan_details['from_destination']}")
                    st.markdown(f"**To:** {plan_details['to_destination']}")
                    st.markdown(f"**Start Date:** {plan_details['start_date']}")
                    st.markdown(f"**End Date:** {plan_details['end_date']}")
                    st.markdown(f"**Budget Breakdown:** {plan_details['budget_breakdown']}")
                    st.markdown("---")
                    st.markdown("**Generated Plan:**")
                    st.markdown(plan_details['plan'])

else:
    # --- Instructions for users without an API key ---
    st.markdown("<h1>✈️ Welcome to the AI Travel Planner</h1>", unsafe_allow_html=True)
    st.warning("Please enter your Google AI API key in the sidebar to begin.")
    st.info(
        "This application uses Google's Gemini model to generate personalized travel plans. "
        "You can get your own free API key from [Google AI Studio](https://aistudio.google.com/)."
    )
