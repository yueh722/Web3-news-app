import streamlit as st
from datetime import datetime
from news_service import NewsService
from utils import inject_custom_css, inject_swipe_detection, inject_pwa_html, inject_pwa_detection, is_pwa, log_to_console, inject_visibility_auto_fetch

# ====== 配置與設定 ======
st.set_page_config(page_title="Web3 News", page_icon="📰", layout="centered")

# 注入 PWA 支援（清單與 Service Worker）
inject_pwa_html()
inject_pwa_detection()

inject_custom_css()
inject_swipe_detection()

# 初始化服務
if "news_service" not in st.session_state:
    st.session_state.news_service = NewsService()

# ====== Session State 初始化 ======
if "today_rows" not in st.session_state:
    st.session_state.today_rows = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.today().date()
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today().date()
if "auto_fetched" not in st.session_state:
    st.session_state.auto_fetched = False
if "status_message" not in st.session_state:
    st.session_state.status_message = None
if "status_type" not in st.session_state:
    st.session_state.status_type = None
if "comment_success_msg" not in st.session_state:
    st.session_state.comment_success_msg = None
if "comment_error_msg" not in st.session_state:
    st.session_state.comment_error_msg = None

# ====== 輔助函式 ======
def rerun():
    """相容的重新執行函式。"""
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# 快取相容性墊片 (Shim)
if hasattr(st, "cache_data"):
    cache_decorator = st.cache_data(ttl=1800, show_spinner=False)
elif hasattr(st, "experimental_memo"):
    cache_decorator = st.experimental_memo(ttl=1800, show_spinner=False)
else:
    # 針對非常舊版本的備案（雖然參數可能略有不同）
    cache_decorator = st.cache(ttl=1800, show_spinner=False, suppress_st_warning=True)

@cache_decorator
def get_cached_news(date_str):
    """包裝新聞資料快取以避免重複呼叫 Webhook。"""
    # 在此實例化服務以確保它是乾淨的，且不依賴傳遞 session_state
    service = NewsService()
    return service.fetch_news(date_str)

def handle_update(force_refresh=False):
    """從 n8n 獲取新聞。"""
    date_str = st.session_state.selected_date.strftime("%Y/%m/%d")
    
    # 如果請求強制重新整理（手動點擊），清除此函式的快取
    if force_refresh:
        get_cached_news.clear()
    
    # 使用快取包裝器獲取新聞
    result = get_cached_news(date_str)
    
    # 獲取今日日期進行比較
    today = datetime.today().date()
    selected = st.session_state.selected_date
        
    if result["status"] == "success":
        if "data" in result:
            st.session_state.today_rows = result["data"]
            st.session_state.current_index = 0
            st.session_state.current_date = date_str
            
            # 檢查資料是否為空並設定適當訊息
            if not st.session_state.today_rows:
                if selected <= today:
                    # 過去或今天無資料
                    st.session_state.status_message = "📭 本日無新聞資料 [0則]"
                    st.session_state.status_type = "warning"
                else:
                    # 未來日期
                    st.session_state.status_message = "📅 無此日期資料請重選日期"
                    st.session_state.status_type = "warning"
            else:
                # 如果資料存在，清除狀態訊息
                st.session_state.status_message = None
                st.session_state.status_type = None
        else:
            st.success(result.get("message", "操作成功"))
    else:
        # 警告或錯誤時清除資料
        st.session_state.today_rows = []
        
        if result["status"] == "warning":
            st.session_state.status_message = result["message"]
            st.session_state.status_type = "warning"
        elif result["status"] in ["future_date", "no_news"]:
             # 如果 fetch_news 返回特定狀態，則處理這些狀態
            if result["status"] == "future_date":
                st.session_state.status_message = "📅 無此日期資料請重選日期"
                st.session_state.status_type = "warning"
            elif result["status"] == "no_news":
                st.session_state.status_message = "📭 本日無新聞資料 [0則]"
                st.session_state.status_type = "warning"
        else:
             st.session_state.status_message = result["message"]
             st.session_state.status_type = "error"
    
    return result

def handle_comment(row, comment_key):
    """發送評論至 n8n（Callback 形式）。"""
    # 從 Session State 取得最新的評論輸入值
    comment = st.session_state.get(comment_key, "")
    sheet_name = st.session_state.selected_date.strftime("%Y/%m/%d")
    
    with st.spinner("送出評論中..."):
        result = st.session_state.news_service.post_comment(sheet_name, row["列號"], comment)
    
    if result["status"] == "success":
        # 儲存成功訊息到 session state
        st.session_state.comment_success_msg = result["message"]
        st.session_state.comment_error_msg = None # 清除先前的錯誤
        
        # 更新本地狀態
        for r in st.session_state.today_rows:
            if r["列號"] == row["列號"]:
                r["評論"] = comment
                break
        # Callback 結束後，Streamlit 會自動執行一次 Rerun
    else:
        st.session_state.comment_error_msg = result["message"]
        st.session_state.comment_success_msg = None


# ====== UI 函式 ======

def show_web_ui():
    """顯示 Web 使用者介面（適用於瀏覽器模式）。"""
    # 定義佈局容器
    header_container = st.container()
    controls_container = st.container()
    status_container = st.container()
    content_container = st.container()
    
    # 1. 標題
    with header_container:
        st.markdown('<h1 class="custom-title">✨ Web3 精選新聞 ✨</h1>', unsafe_allow_html=True)
    
    # 智慧自動更新邏輯：
    # 當 auto_fetched 為 False 時，顯示一個隱藏按鈕 "StartAutoFetch"
    # 並注入 JS 來偵測可見度，只有當頁面可見時，JS 才會點擊該按鈕觸發更新。
    if not st.session_state.auto_fetched:
        # 1. 產生一個隱藏按鈕 (CSS/JS 會把它藏起來)
        # 用 key 確保唯一性
        if st.button("StartAutoFetch", key="btn_trigger_auto_fetch"):
            # 當被點擊時 (表示前端 JS 偵測到可見了)
            try:
                log_to_console(f"� [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Visibility detected - Triggering auto-fetch")
            except:
                pass
            
            with status_container:
                status_placeholder = st.empty()
                status_placeholder.markdown(
                    f'<div class="status-area" style="background-color: #e69138; color: white;">正在自動更新 {st.session_state.selected_date.strftime("%Y/%m/%d")} 的新聞...</div>', 
                    unsafe_allow_html=True
                )
                
                # 設定旗標防止重複
                st.session_state.auto_fetched = True
                
                result = handle_update()
                
                if result["status"] == "success" or st.session_state.status_message:
                    status_placeholder.empty()
                    rerun()
                else:
                    status_placeholder.error(result.get("message", "Unknown error"))
        
        # 2. 注入 JS 偵測邏輯
        inject_visibility_auto_fetch()
    
    # 2. 控制面板（日期與更新）
    with controls_container:
        col_date, col_btn = st.columns([2, 1])
        with col_date:
            st.session_state.selected_date = st.date_input(
                "選擇日期",
                value=st.session_state.selected_date
            )
        with col_btn:
            # 加入間隔以對齊按鈕與輸入框（因為標籤高度將其下推）
            # 增加至 38px 以配合較大的標籤字體大小
            st.markdown('<div style="height: 38px;"></div>', unsafe_allow_html=True)
            if st.button("🔄 更新", key="btn_update_news"):
                # 在狀態容器中使用佔位符顯示更新訊息
                with status_container:
                    status_placeholder = st.empty()
                    status_placeholder.markdown(
                        f'<div class="status-area" style="background-color: #e69138; color: white;">正在更新 {st.session_state.selected_date.strftime("%Y/%m/%d")} 的新聞...</div>', 
                        unsafe_allow_html=True
                    )
                    
                    # 執行更新
                    result = handle_update(force_refresh=True)
                    
                    # 重新執行以更新 UI（資料或狀態訊息）
                    if result["status"] == "success" or st.session_state.status_message:
                        status_placeholder.empty()
                        rerun()
                    else:
                        status_placeholder.error(result.get("message", "Unknown error"))
    
    # 3. 狀態列（控制項下方）
    with status_container:
        # 如果有設定狀態訊息則顯示
        if st.session_state.status_message:
            if st.session_state.status_type == "warning":
                # 橘色警告框
                st.markdown(
                    f'<div class="status-area" style="background-color: #e69138; color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;">{st.session_state.status_message}</div>',
                    unsafe_allow_html=True
                )
            elif st.session_state.status_type == "error":
                 st.markdown(
                    f'<div class="status-area" style="background-color: #dc3545; color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;">{st.session_state.status_message}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="status-area">{st.session_state.status_message}</div>',
                    unsafe_allow_html=True
                )
        elif not st.session_state.today_rows:
            # 如果無資料且無狀態訊息的預設訊息
            st.markdown('<div class="status-area">', unsafe_allow_html=True)
            st.markdown(
                '<div style="color: #FFFFFF; font-weight: bold; font-size: 1.2rem;">請點擊「更新」以取得內容</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. 內容區域
    with content_container:
        if st.session_state.today_rows:
            total = len(st.session_state.today_rows)
            idx = st.session_state.current_index
            row = st.session_state.today_rows[idx]
            
            # 卡片容器
            with st.container():
                st.markdown(f"""
                <div class="news-card">
                    <div style="margin-bottom: 0.5rem;">
                        <span style="color: #4facfe; font-weight: bold; font-size: 1.5rem;">📅 {st.session_state.current_date}</span>
                        <span style="color: #999; font-weight: normal; font-size: 0.95rem;">   [ 共 {total} 則 ]</span><br>
                        <span style="color: #4facfe; font-weight: bold; font-size: 1.5rem;">No.  {idx + 1}</span>
                    </div>
                    <h3>{row.get('標題', '無標題')}</h3>
                    <p style="color: #ccc; font-size: 1em;">
                        <a href="{row.get('url', '')}" target="_blank" style="color: #4facfe; text-decoration: none;">
                            {row.get('url', '')}
                        </a>
                    </p>
                    <hr style="border-color: #004080;">
                    <p><strong>💡 AI 評選原因:</strong><br>{row.get('ai評選原因', '')}</p>
                    <p><strong>🎯 分數:</strong> {row.get('分數', '')} | <strong>🏷️ 主題:</strong> {row.get('主題', '')}</p>
                </div>
                """, unsafe_allow_html=True)

                # 導航按鈕（已恢復）
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("⬅️ 上一則", key="btn_prev", disabled=(st.session_state.current_index == 0)):
                        st.session_state.current_index -= 1
                        rerun()
                with c2:
                    if st.button("➡️ 下一則", key="btn_next", disabled=(st.session_state.current_index == len(st.session_state.today_rows) - 1)):
                        st.session_state.current_index += 1
                        rerun()

                # 評論區塊
                st.markdown("---")
                comment_key = f"comment_{row.get('sno')}_{st.session_state.current_date}"
                current_comment = row.get("評論", "")
                
                new_comment = st.text_area("📝 留下評論", value=current_comment, key=comment_key)
                
                st.button("送出評論", key=f"btn_comment_{row.get('sno')}", on_click=handle_comment, args=(row, comment_key))
                
                # 顯示評論成功訊息（如果在重新執行後有設定）
                if st.session_state.comment_success_msg:
                    st.success(st.session_state.comment_success_msg)
                    # 顯示後清除，避免下次重新整理還出現
                    st.session_state.comment_success_msg = None
                
                # 顯示評論錯誤訊息
                if st.session_state.comment_error_msg:
                    st.error(st.session_state.comment_error_msg)
                    st.session_state.comment_error_msg = None

def show_app_ui():
    """顯示 App 使用者介面（適用於 PWA/獨立模式）。"""
    # 目前 App 介面與 Web 介面相同
    # 您可以稍後自訂此處以獲得更像 App 的體驗
    show_web_ui()


# ====== 主要 App 路由 ======

# 檢查是否在 PWA 模式下執行並路由至適當的 UI
if is_pwa():
    show_app_ui()
else:
    show_web_ui()
