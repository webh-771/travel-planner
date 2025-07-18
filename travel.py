import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as ggi
from datetime import date
import matplotlib.pyplot as plt

load_dotenv()
api_key = os.getenv("API_KEY")

st.markdown("""
    <style>
        body {
            background-color: #f0f5f9;
            color: #333333;
        }
        .main {
            background-color: #000000;
            border-radius: 15px;
            padding: 10px;
        }
        h1 {
            color: #4CAF50;
            font-family: 'Helvetica', sans-serif;
        }
        h2, h3 {
            color: #1E90FF;
            font-family: 'Arial', sans-serif;
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 10px;
            font-size: 16px;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
        .card {
            background-color: #808080;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
        }
        .sidebar {
            background-color: #2F4F4F;
            color: white;
            padding: 20px;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

if not api_key:
    st.error("API key not found. Please ensure it is set correctly in the .env file.")
else:
    ggi.configure(api_key=api_key)
    model = ggi.GenerativeModel("gemini-pro")
    chat = model.start_chat()

    def budget_calculator():
        st.markdown("<h1 style='text-align: center;'>💰 Travel Budget Calculator</h1>", unsafe_allow_html=True)
        
        st.markdown("### Please provide your estimated expenses in the following categories:")

        transport_budget = st.number_input("Transport Budget (₹)", min_value=1000, max_value=100000, step=1000)
        food_budget = st.number_input("Food Budget (₹)", min_value=1000, max_value=50000, step=500)
        stay_budget = st.number_input("Accommodation Budget (₹)", min_value=1000, max_value=100000, step=1000)
        other_expenses = st.number_input("Miscellaneous Expenses (₹)", min_value=500, max_value=50000, step=500)
        
        total_budget = (lambda transport, food, stay, other: transport + food + stay + other)(transport_budget, food_budget, stay_budget, other_expenses)

        inflation_rate = st.slider("Inflation Rate (%)", 0, 20, 5)
        adjust_for_inflation = lambda budget, rate: budget * (1 + rate / 100)
        inflation_adjusted_budget = adjust_for_inflation(total_budget, inflation_rate)

        num_days = st.slider("Number of Travel Days", 1, 30, 7)
        cost_per_day = (lambda total, days: total / days)(total_budget, num_days)

        currency_conversion = st.checkbox("Need to convert to another currency?")
        conversion_rate = 1
        if currency_conversion:
            conversion_rate = st.number_input("Enter Conversion Rate (₹ to Foreign Currency)", min_value=0.01, value=1.0)
            converted_budget = lambda budget, rate: budget / rate
            foreign_currency_budget = converted_budget(inflation_adjusted_budget, conversion_rate)

        st.markdown(f"### Budget Breakdown:")
        st.write(f"**Total Budget (without inflation):** ₹{total_budget}")
        st.write(f"**Total Budget (with inflation adjustment):** ₹{inflation_adjusted_budget}")
        st.write(f"**Cost per day:** ₹{cost_per_day}")
        
        if currency_conversion:
            st.write(f"**Total Budget in Foreign Currency:** {foreign_currency_budget}")

        categories = ['Transport', 'Food', 'Accommodation', 'Miscellaneous']
        values = [transport_budget, food_budget, stay_budget, other_expenses]
        
        fig, ax = plt.subplots()
        ax.pie(values, labels=categories, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  
        st.pyplot(fig)


    def call_gemini_ai(prompt):
        try:
            response = chat.send_message(prompt, stream=True)
            generated_text = ''.join([word.text for word in response])
            return generated_text
        except Exception as e:
            st.error(f"Error: {e}")
            return ""

    if 'travel_planner_db' not in st.session_state:
        st.session_state['travel_planner_db'] = {}
    if 'budget_breakdown' not in st.session_state:
        st.session_state['budget_breakdown'] = ""

    def add_travel_plan(from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, plan):
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
        st.markdown("<h2>Set Operations</h2>", unsafe_allow_html=True)

        set1 = ('Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad')
        set2 = ('Pune', 'Delhi', 'Kolkata', 'Bengaluru')

        set_operations_dict = {
            'Union': set(set1).union(set(set2)),
            'Intersection': set(set1).intersection(set(set2)),
            'Difference (Set1 - Set2)': set(set1).difference(set(set2)),
            'Symmetric Difference': set(set1).symmetric_difference(set(set2))
        }

        for operation, result in set_operations_dict.items():
            st.write(f"**{operation}:** {result}")

    def get_travel_details():
        st.markdown("### Where do you want to go? 🌎")
        cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Surat', 'Pune', 'Jaipur', 'Gokarna', 'Palanpur']

        from_destination = st.selectbox("Where are you starting from?", cities)
        to_destination = st.selectbox("Where do you want to go?", cities)

        start_date = st.date_input("Start date", min_value=date.today())
        end_date = st.date_input("End date", min_value=start_date)

        if start_date > end_date:
            st.error("End date must be after the start date.")
            return from_destination, to_destination, start_date, end_date, None, None

        food_budget = st.slider("Food Budget (₹)", 1000, 50000, step=1000)
        stay_budget = st.slider("Stay Budget (₹)", 1000, 50000, step=1000)
        other_budget = st.slider("Other Expenses (₹)", 1000, 50000, step=1000)
        total_budget = food_budget + stay_budget + other_budget

        budget_breakdown = f"Food: ₹{food_budget}, Stay: ₹{stay_budget}, Other: ₹{other_budget}, Total: ₹{total_budget}"

        days = (end_date - start_date).days + 1
        query = f"Plan a trip from {from_destination} to {to_destination} for {days} days with a total budget of ₹{total_budget}, including {budget_breakdown}."
        return from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, query

    st.sidebar.markdown("<h2 class='sidebar'>📋 Menu</h2>", unsafe_allow_html=True)
    choice = st.sidebar.radio("Go to", ["Travel Plans", "Budget Calculator"])

    if choice == "Travel Plans":
        st.markdown("<h1 style='text-align: center;'>✈️ Travel Planner 🌍</h1>", unsafe_allow_html=True)

        from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, query = get_travel_details()

        if st.button("Generate Travel Plan"):
            if not all([from_destination, to_destination, start_date, end_date, total_budget]):
                st.error("Please provide all the details to generate the plan.")
            else:
                plan = call_gemini_ai(query)
                add_travel_plan(from_destination, to_destination, start_date, end_date, total_budget, budget_breakdown, plan)
                st.success("Travel plan generated successfully!")
                st.markdown(f"**From:** {from_destination}")
                st.markdown(f"**To:** {to_destination}")
                st.markdown(f"**Start Date:** {start_date}")
                st.markdown(f"**End Date:** {end_date}")
                st.markdown(f"**Budget Breakdown:** {budget_breakdown}")
                st.markdown(f"**Generated Plan:** {plan}")

        if st.button("Show Set Operations"):
            set_operations_popup()

    if choice == "Budget Calculator":
        budget_calculator()
