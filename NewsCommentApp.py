import streamlit as st
from datetime import datetime
from news_service import NewsService
from utils import inject_custom_css, inject_swipe_detection, inject_pwa_html, inject_pwa_detection, is_pwa

# ====== Configuration & Setup ======
st.set_page_config(page_title="Web3 News", page_icon="📰", layout="centered")

# Inject PWA support (manifest and service worker)
inject_pwa_html()
inject_pwa_detection()

inject_custom_css()
inject_swipe_detection()

# Initialize Service
if "news_service" not in st.session_state:
    st.session_state.news_service = NewsService()

# ====== Session State Initialization ======
if "today_rows" not in st.session_state:
    st.session_state.today_rows = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.today().date()
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today().date()

# ====== Helper Functions ======
def rerun():
    """Compatible rerun."""
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

def handle_update():
    """Fetch news from n8n."""
    date_str = st.session_state.selected_date.strftime("%Y/%m/%d")
    
    # Fetch news directly (loading message handled in UI)
    result = st.session_state.news_service.fetch_news(date_str)
        
    if result["status"] == "success":
        if "data" in result:
            st.session_state.today_rows = result["data"]
            st.session_state.current_index = 0
            st.session_state.current_date = date_str
        else:
            st.success(result.get("message", "操作成功"))
    elif result["status"] == "warning":
        st.warning(result["message"])
    
    return result

def handle_comment(row, comment):
    """Send comment to n8n."""
    sheet_name = st.session_state.selected_date.strftime("%Y/%m/%d")
    
    with st.spinner("送出評論中..."):
        result = st.session_state.news_service.post_comment(sheet_name, row["列號"], comment)
    
    if result["status"] == "success":
        st.success(result["message"])
        # Update local state
        for r in st.session_state.today_rows:
            if r["列號"] == row["列號"]:
                r["評論"] = comment
                break
        rerun()
    else:
        st.error(result["message"])


# ====== UI Functions ======

def show_web_ui():
    """Display Web UI (for browser mode)."""
    # Define Layout Containers
    header_container = st.container()
    controls_container = st.container()
    status_container = st.container()
    content_container = st.container()
    
    # 1. Title
    with header_container:
        st.markdown('<h1 class="custom-title">✨ Web3 精選新聞 ✨</h1>', unsafe_allow_html=True)
    
    # 2. Control Panel (Date & Update)
    with controls_container:
        col_date, col_btn = st.columns([2, 1])
        with col_date:
            st.session_state.selected_date = st.date_input(
                "選擇日期",
                value=st.session_state.selected_date
            )
        with col_btn:
            # Add spacer to align button with input box (pushing it down by label height)
            # Increased to 38px to account for larger label font size
            st.markdown('<div style="height: 38px;"></div>', unsafe_allow_html=True)
            if st.button("🔄 更新", key="btn_update_news"):
                # Show updating message in status container using a placeholder
                with status_container:
                    status_placeholder = st.empty()
                    status_placeholder.markdown(
                        f'<div class="status-area" style="background-color: #e69138; color: white;">正在更新 {st.session_state.selected_date.strftime("%Y/%m/%d")} 的新聞...</div>', 
                        unsafe_allow_html=True
                    )
                    
                    # Perform update
                    result = handle_update()
                    
                    if result["status"] == "success":
                        # Clear message and rerun to show content
                        status_placeholder.empty()
                        rerun()
                    elif result["status"] == "future_date":
                        # Future date - show orange warning
                        status_placeholder.markdown(
                            '<div class="status-area" style="background-color: #ff9800; color: white;">📅 無此日期資料請重選日期</div>',
                            unsafe_allow_html=True
                        )
                    elif result["status"] == "no_news":
                        # No news but valid date - show orange warning
                        status_placeholder.markdown(
                            '<div class="status-area" style="background-color: #ff9800; color: white;">📭 本日無新聞資料 [0則]</div>',
                            unsafe_allow_html=True
                        )
                    elif result["status"] == "warning":
                        status_placeholder.warning(result["message"])
                    else:
                        status_placeholder.error(result["message"])
    
    # 3. Status Bar (Below Controls)
    with status_container:
        # Only show message if no data
        if not st.session_state.today_rows:
            st.markdown('<div class="status-area">', unsafe_allow_html=True)
            st.markdown(
                '<div style="color: #FFFFFF; font-weight: bold; font-size: 1.2rem;">請點擊「更新」以取得內容</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. Content Area
    with content_container:
        if st.session_state.today_rows:
            total = len(st.session_state.today_rows)
            idx = st.session_state.current_index
            row = st.session_state.today_rows[idx]
            
            # Card Container
            with st.container():
                st.markdown(f"""
                <div class="news-card">
                    <div style="margin-bottom: 0.5rem;">
                        <span style="color: #4facfe; font-weight: bold; font-size: 1.5rem;">📅 {st.session_state.current_date}</span>
                        <span style="color: #999; font-weight: normal; font-size: 0.95rem;">   [ 共 {total} 則 ]</span><br>
                        <span style="color: #4facfe; font-weight: bold; font-size: 1.5rem;">No.  {idx + 1}</span>
                    </div>
                    <h3>{row.get('標題', '無標題')}</h3>
                    <p style="color: #ccc; font-size: 0.9em;">{row.get('url', '')}</p>
                    <hr style="border-color: #004080;">
                    <p><strong>💡 AI 評選原因:</strong><br>{row.get('ai評選原因', '')}</p>
                    <p><strong>🎯 分數:</strong> {row.get('分數', '')} | <strong>🏷️ 主題:</strong> {row.get('主題', '')}</p>
                </div>
                """, unsafe_allow_html=True)

                # Navigation Buttons (Restored)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("⬅️ 上一則", key="btn_prev", disabled=(st.session_state.current_index == 0)):
                        st.session_state.current_index -= 1
                        rerun()
                with c2:
                    if st.button("➡️ 下一則", key="btn_next", disabled=(st.session_state.current_index == len(st.session_state.today_rows) - 1)):
                        st.session_state.current_index += 1
                        rerun()

                # Comment Section
                st.markdown("---")
                comment_key = f"comment_{row.get('sno')}_{st.session_state.current_date}"
                current_comment = row.get("評論", "")
                
                new_comment = st.text_area("📝 留下評論", value=current_comment, key=comment_key)
                
                if st.button("送出評論", key=f"btn_comment_{row.get('sno')}"):
                    handle_comment(row, new_comment)

def show_app_ui():
    """Display App UI (for PWA/standalone mode)."""
    # For now, App UI is the same as Web UI
    # You can customize this later for a more app-like experience
    show_web_ui()


# ====== Main App Routing ======

# Check if running in PWA mode and route to appropriate UI
if is_pwa():
    show_app_ui()
else:
    show_web_ui()
