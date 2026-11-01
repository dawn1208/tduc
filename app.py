import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

app = FastAPI(title="EcoMind AI All-in-One", version="1.0.0")

# Strict Guardrail & Roles
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

class ChatRequest(BaseModel):
    message: str
    role: str = "clean_energy"

class CarbonRequest(BaseModel):
    electricity_kwh: float
    gasoline_liters: float
    waste_kg: float

@app.post("/api/chat")
async def chat_stream(req: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Thiếu GEMINI_API_KEY trong biến môi trường.")

    system_prompt = ROLES_PROMPTS.get(req.role, ROLES_PROMPTS["clean_energy"]) + STRICT_GUARDRAIL
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, streaming=True, temperature=0.3)
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=req.message)]

    async def event_generator():
        async for chunk in llm.astream(messages):
            yield chunk.content

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/api/carbon-calculator")
async def calculate_carbon(req: CarbonRequest):
    elec_co2 = req.electricity_kwh * 0.72
    gas_co2 = req.gasoline_liters * 2.3
    waste_co2 = req.waste_kg * 1.5
    total_co2 = elec_co2 + gas_co2 + waste_co2
    
    suggestions = []
    if elec_co2 > 100: suggestions.append("Chuyển đổi sang thiết bị tiết kiệm điện hoặc lắp năng lượng mặt trời áp mái.")
    if gas_co2 > 50: suggestions.append("Tăng cường sử dụng phương tiện công cộng hoặc xe điện.")
    if waste_co2 > 30: suggestions.append("Thực hiện phân loại rác tại nguồn và ủ phân hữu cơ.")

    return {
        "monthly_co2_kg": round(total_co2, 2),
        "suggestions": suggestions
    }

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>EcoMind AI - Trợ lý Môi trường</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-emerald-950 text-slate-100 min-h-screen flex flex-col font-sans">
        <header class="border-b border-emerald-800 bg-emerald-900/60 p-4 sticky top-0 z-50">
            <div class="max-w-4xl mx-auto flex justify-between items-center">
                <h1 class="text-xl font-bold text-emerald-300">🌿 EcoMind AI Agent</h1>
                <div class="space-x-2">
                    <button onclick="switchTab('chat')" id="btn-chat" class="px-4 py-2 rounded-lg bg-emerald-600 text-sm font-medium">Chat Agent</button>
                    <button onclick="switchTab('calc')" id="btn-calc" class="px-4 py-2 rounded-lg bg-emerald-900 text-sm font-medium">Carbon Calculator</button>
                </div>
            </div>
        </header>

        <main class="max-w-4xl w-full mx-auto p-4 flex-1 flex flex-col">
            <!-- Chat View -->
            <div id="view-chat" class="flex-1 flex flex-col bg-emerald-900/30 border border-emerald-800 rounded-xl overflow-hidden h-[75vh]">
                <div class="p-3 bg-emerald-950/60 border-b border-emerald-800 flex justify-between items-center text-xs">
                    <span class="text-amber-400">⚡ Strict Mode: Chỉ trả lời về Môi trường & Khí hậu</span>
                    <select id="role-select" class="bg-emerald-900 border border-emerald-700 text-white p-1.5 rounded">
                        <option value="clean_energy">Kỹ sư Năng lượng Sạch</option>
                        <option value="waste_recycling">Chuyên gia Tái chế</option>
                        <option value="climate_ecologist">Nhà Sinh thái học Khí hậu</option>
                    </select>
                </div>
                <div id="chat-box" class="flex-1 overflow-y-auto p-4 space-y-3 text-sm">
                    <div class="bg-emerald-900/80 p-3 rounded-lg max-w-[80%]">Xin chào! Tôi là EcoMind AI. Tôi có thể hỗ trợ gì cho bạn về bảo vệ môi trường và năng lượng sạch?</div>
                </div>
                <div class="p-3 bg-emerald-950 border-t border-emerald-800 flex gap-2">
                    <input type="text" id="user-input" placeholder="Nhập câu hỏi về môi trường..." class="flex-1 bg-emerald-900 border border-emerald-700 rounded-lg px-4 py-2 text-sm focus:outline-none">
                    <button onclick="sendMessage()" class="bg-emerald-500 text-emerald-950 font-semibold px-4 rounded-lg">Gửi</button>
                </div>
            </div>

            <!-- Calculator View -->
            <div id="view-calc" class="hidden bg-emerald-900/30 border border-emerald-800 rounded-xl p-6 space-y-4">
                <h2 class="text-lg font-bold text-emerald-300">Tính toán Dấu chân Carbon</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div><label class="text-xs">Điện (kWh/tháng):</label><input type="number" id="elec" value="150" class="w-full bg-emerald-950 border border-emerald-700 p-2 rounded mt-1"></div>
                    <div><label class="text-xs">Xăng (Lít/tháng):</label><input type="number" id="gas" value="30" class="w-full bg-emerald-950 border border-emerald-700 p-2 rounded mt-1"></div>
                    <div><label class="text-xs">Rác (kg/tháng):</label><input type="number" id="waste" value="20" class="w-full bg-emerald-950 border border-emerald-700 p-2 rounded mt-1"></div>
                </div>
                <button onclick="calculateCarbon()" class="bg-emerald-500 text-emerald-950 font-semibold px-6 py-2 rounded-lg">Tính toán</button>
                <div id="calc-result" class="mt-4 p-4 bg-emerald-950 rounded-lg border border-emerald-800 hidden"></div>
            </div>
        </main>

        <script>
            function switchTab(tab) {
                if(tab === 'chat') {
                    document.getElementById('view-chat').classList.remove('hidden');
                    document.getElementById('view-calc').classList.add('hidden');
                    document.getElementById('btn-chat').className = 'px-4 py-2 rounded-lg bg-emerald-600 text-sm font-medium';
                    document.getElementById('btn-calc').className = 'px-4 py-2 rounded-lg bg-emerald-900 text-sm font-medium';
                } else {
                    document.getElementById('view-chat').classList.add('hidden');
                    document.getElementById('view-calc').classList.remove('hidden');
                    document.getElementById('btn-calc').className = 'px-4 py-2 rounded-lg bg-emerald-600 text-sm font-medium';
                    document.getElementById('btn-chat').className = 'px-4 py-2 rounded-lg bg-emerald-900 text-sm font-medium';
                }
            }

            async function sendMessage() {
                const input = document.getElementById('user-input');
                const role = document.getElementById('role-select').value;
                const chatBox = document.getElementById('chat-box');
                if(!input.value.trim()) return;

                const query = input.value;
                input.value = '';
                chatBox.innerHTML += `<div class="bg-emerald-600 text-white p-3 rounded-lg max-w-[80%] ml-auto">${query}</div>`;
                
                const aiMsgId = 'ai-' + Date.now();
                chatBox.innerHTML += `<div id="${aiMsgId}" class="bg-emerald-900/80 p-3 rounded-lg max-w-[80%]">Đang phân tích...</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const res = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: query, role: role})
                    });
                    const reader = res.body.getReader();
                    const decoder = new TextDecoder();
                    document.getElementById(aiMsgId).innerText = '';

                    while(true) {
                        const {done, value} = await reader.read();
                        if(done) break;
                        document.getElementById(aiMsgId).innerText += decoder.decode(value);
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }
                } catch(e) {
                    document.getElementById(aiMsgId).innerText = 'Lỗi kết nối server.';
                }
            }

            async function calculateCarbon() {
                const res = await fetch('/api/carbon-calculator', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        electricity_kwh: Number(document.getElementById('elec').value),
                        gasoline_liters: Number(document.getElementById('gas').value),
                        waste_kg: Number(document.getElementById('waste').value)
                    })
                });
                const data = await res.json();
                const box = document.getElementById('calc-result');
                box.classList.remove('hidden');
                box.innerHTML = `<h3 class='font-bold text-emerald-300'>Tổng lượng CO2: ${data.monthly_co2_kg} kg/tháng</h3><ul class='mt-2 space-y-1 text-xs'>` + data.suggestions.map(s => `<li>🌱 ${s}</li>`).join('') + `</ul>`;
            }
        </script>
    </body>
    </html>
    """