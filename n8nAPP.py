import streamlit as st
import requests
from datetime import datetime
import traceback

# ====== n8n Webhook URL ======

N8N_WEBHOOK_read = "https://n8n.defintek.io/webhook/read_news"
N8N_WEBHOOK_update = "https://n8n.defintek.io/webhook/update_news"

# ====== Streamlit 標題 ======
st.title("✨ Web3 精選新聞 ✨")

# ====== 初始化 Session State ======
if "today_rows" not in st.session_state:
    st.session_state.today_rows = []
if "comment_values" not in st.session_state:
    st.session_state.comment_values = {}
if "star_container" not in st.session_state:
    st.session_state.star_container = st.empty()
if "status_container" not in st.session_state:
    st.session_state.status_container = st.empty()
if "controls_container" not in st.session_state:
    st.session_state.controls_container = st.empty()
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# ====== 顯示狀態 ======
def update_status(current_index):
    if st.session_state.today_rows:
        st.session_state.status_container.info(
            f"已取得今日新聞 len: {len(st.session_state.today_rows)} | index: {current_index}"
        )
    else:
        st.session_state.status_container.warning("請先按 🔄 更新，取得今日新聞。")

# ====== 顯示新聞 ======
def show_current_star(data, index):
    if not data:
        st.session_state.star_container.empty()
        return

    row = data[index]    

    with st.session_state.star_container.container():
        st.write(f"                   {row['日期']}")
        st.subheader(f"NO.{row['sno']}  {row['標題']}")
        st.write(f"url: {row['url']}")
        st.write(f"ai評選原因: {row['ai評選原因']}")
        st.write(f"分數: {row['分數']}")
        st.write(f"主題: {row['主題']}")
        #st.write(f"備註: {row['備註']}")
        #st.write(f"評論: {row['評論']}")

        comment_key = f"comment_{row.get('sno')}_{row.get('日期')}"
        comment = st.text_area(
            "留下評論：",
            value=str(row.get("評論", "")),
            key=comment_key
        )

        button_key = f"send_comment_{row.get('列號')}_{row.get('日期')}"
        if st.button("送出評論", key=button_key):
            try:
                #sheet_name = datetime.today().strftime("%Y/%m/%d")
                sheet_name = row.get('日期')
                payload = {
                    "sheetName": sheet_name, 
                    "rowIndex": row["列號"],   
                    "comment": comment
                }

                #st.json(payload)
                #st.write("即將送出的 payload：", payload)


                response = requests.post(N8N_WEBHOOK_update, json=payload)
                if response.status_code == 200:
                    st.success("評論已送出！")

                    for r in st.session_state.today_rows:
                        if r["列號"] == row["列號"]:
                            r["評論"] = comment
                            break

                else:
                    st.error(f"n8n 回應錯誤: {response.text}")
            except Exception as e:
                st.error(f"無法連線到 n8n 評論: {e}")


# ====== 顯示目前新聞和狀態 ======
update_status(st.session_state.current_index)
show_current_star(st.session_state.today_rows, st.session_state.current_index)

# ====== 按鈕 ======
with st.session_state.controls_container.container():
    col1, col2, col3 = st.columns([1,1,1])

    with col1:
        #disabled_prev = (st.session_state.current_index <= 0)
        #if st.button("⬅ 上一則新聞", disabled=disabled_prev):
        if st.button("⬅ 上一則"):
            if(st.session_state.current_index > 0):
                st.session_state.current_index -= 1
                show_current_star(st.session_state.today_rows, st.session_state.current_index)
                update_status(st.session_state.current_index)

    with col2:
        if st.button("🔄 更新"):
            today_str = datetime.today().strftime("%Y/%m/%d")
            try:
                response = requests.get(N8N_WEBHOOK_read, params={"date": today_str})
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        if len(data) == 1 and "message" in data[0]:
                            st.success(data[0]["message"])  
                        else:    
                            st.session_state.today_rows = [item.get("json", item) for item in data]
                            st.session_state.current_index = 0
                            show_current_star(st.session_state.today_rows, st.session_state.current_index)
                            update_status(st.session_state.current_index)
                    else:
                        st.warning("n8n 回傳資料為空")
                else:
                    st.error(f"n8n 回應錯誤: {response.text}")
            except Exception as e:
                st.error(f"無法連線到 n8n 更新 : {e}")
                st.text(traceback.format_exc())

    with col3:
        #disabled_next = (st.session_state.current_index >= len(st.session_state.today_rows)-1)
        #if st.button("➡ 下一則新聞", disabled=disabled_next):
        if st.button("➡ 下一則"):
            if(st.session_state.current_index < (len(st.session_state.today_rows)-1)):    
                st.session_state.current_index += 1
                show_current_star(st.session_state.today_rows, st.session_state.current_index)
                update_status(st.session_state.current_index)
