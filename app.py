import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="EcoMind AI", page_icon="🌿", layout="centered")

# CSS tùy chỉnh giao diện xanh tối giản, mượt mà
st.markdown("""
    <style>
    .stApp { background-color: #022c22; color: #f1f5f9; }
    .stTextInput input { background-color: #064e3b; color: white; border: 1px solid #059669; }
    .stSelectbox select { background-color: #064e3b; color: white; border: 1px solid #059669; }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 EcoMind AI - Trợ lý Môi trường")
st.markdown("Trợ lý AI chuyên biệt về năng lượng sạch, tái chế và biến đổi khí hậu.")

# Kiểm tra API Key từ biến môi trường hoặc sidebar
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Nhập Gemini API Key của bạn:", type="password")
    if not api_key:
        st.warning("⚠️ Vui lòng nhập Gemini API Key để tiếp tục sử dụng AI.")
        st.stop()

# Chọn tab chức năng
tab1, tab2 = st.tabs(["💬 Chat với Eco Agent", "📊 Công cụ tính Carbon"])

ROLES_PROMPTS = {
    "clean_energy": "Bạn là Kỹ sư Năng lượng Sạch. Bạn CHỈ trả lời các chủ đề về năng lượng tái tạo, pin mặt trời, điện gió và giảm phát thải.\n",
    "waste_recycling": "Bạn là Chuyên gia Tái chế Rác thải. Bạn CHỈ trả lời các vấn đề về phân loại rác, kinh tế tuần hoàn và giảm rác thải sinh hoạt.\n",
    "climate_ecologist": "Bạn là Nhà Sinh thái học Khí hậu. Bạn CHỈ trả lời các vấn đề về biến đổi khí hậu, bảo tồn hệ sinh thái và đa dạng sinh học.\n"
}

STRICT_GUARDRAIL = """
QUY TẮC RÀNG BUỘC TUYỆT ĐỐI:
1. Bạn là EcoMind AI - AI Agent CHỈ CHUYÊN BIỆT về môi trường và khí hậu.
2. Nếu câu hỏi KHÔNG liên quan đến môi trường/khí hậu/năng lượng/rác thải: Hãy từ chối lịch sự và lái câu chuyện về bảo vệ môi trường.
"""

with tab1:
    role_choice = st.selectbox("Chọn chuyên gia AI:", [
        ("clean_energy", "Kỹ sư Năng lượng Sạch"),
        ("waste_recycling", "Chuyên gia Tái chế Rác thải"),
        ("climate_ecologist", "Nhà Sinh thái học Khí hậu")
    ], format_func=lambda x: x[1])

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Xin chào! Tôi có thể giúp gì cho bạn về môi trường và năng lượng sạch?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Nhập câu hỏi về môi trường..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, streaming=True, temperature=0.3)
                system_prompt = ROLES_PROMPTS[role_choice[0]] + STRICT_GUARDRAIL
                messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
                
                response_container = st.empty()
                full_response = ""
                for chunk in llm.stream(messages):
                    full_response += chunk.content
                    response_container.markdown(full_response + "▌")
                response_container.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {e}")

with tab2:
    st.subheader("Tính toán Dấu chân Carbon")
    elec = st.number_input("Điện năng tiêu thụ (kWh/tháng):", value=150.0)
    gas = st.number_input("Tiêu thụ Xăng/Dầu (Lít/tháng):", value=30.0)
    waste = st.number_input("Rác thải sinh hoạt (kg/tháng):", value=20.0)

    if st.button("Tính toán và Phân tích"):
        elec_co2 = elec * 0.72
        gas_co2 = gas * 2.3
        waste_co2 = waste * 1.5
        total_co2 = elec_co2 + gas_co2 + waste_co2
        
        st.success(f"🌍 Tổng lượng CO2 ước tính: **{round(total_co2, 2)} kg/tháng**")
        st.markdown("### Gợi ý cắt giảm từ chuyên gia:")
        if elec_co2 > 100: st.markdown("- 🌱 Chuyển sang thiết bị tiết kiệm điện hoặc lắp năng lượng mặt trời áp mái.")
        if gas_co2 > 50: st.markdown("- 🌱 Tăng cường sử dụng phương tiện công cộng hoặc xe điện.")
        if waste_co2 > 30: st.markdown("- 🌱 Thực hiện phân loại rác tại nguồn và ủ phân hữu cơ.")