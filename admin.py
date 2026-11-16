"""Server-side password gate and admin-only dashboard."""
from pathlib import Path
import base64
import hmac
import time
import pandas as pd
import streamlit as st


def show_admin(store, password, default_phone):
    logo = Path(__file__).resolve().parent / 'website/assets/logo.svg'
    logo_data = base64.b64encode(logo.read_bytes()).decode('ascii')
    language = st.query_params.get('admin_lang', 'ar')
    if language not in ('ar', 'en'):
        language = 'ar'
    def tr(en, ar):
        return ar if language == 'ar' else en
    st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
    :root{--admin-ink:#183756;--admin-deep:#10263d;--admin-bronze:#b68c66;--admin-paper:#f7f8fa;--admin-muted:#526577;--admin-rule:#c7d0d8}
    .stApp{background:var(--admin-paper);color:var(--admin-ink)}
    [data-testid="stHeader"]{background:var(--admin-paper)}
    [data-testid="stMainBlockContainer"]{max-width:1360px;padding:3rem clamp(1rem,4vw,4rem) 4rem}
    [data-testid="stMain"]{overflow-y:auto!important;overflow-x:hidden!important}
    .admin-brand{display:flex;align-items:center;justify-content:space-between;gap:32px;padding:24px 0 30px;border-bottom:1px solid var(--admin-bronze);margin-bottom:28px}
    .admin-brand img{display:block;width:154px;max-width:35%;height:auto}
    .admin-brand-name{text-align:right;line-height:1.8;color:var(--admin-ink);font-size:18px;font-weight:500}
    .admin-brand-name span{display:block;color:var(--admin-muted);font-size:13px;font-weight:400}
    .admin-heading{background:var(--admin-deep);padding:32px 36px;margin-bottom:20px;border-bottom:2px solid var(--admin-bronze)}
    .admin-heading h1{color:var(--admin-paper);font-size:clamp(30px,4vw,44px);font-weight:500;letter-spacing:-.025em;margin:0;padding:0;line-height:1.3}
    .admin-heading p{color:#bfccd8;font-size:15px;line-height:1.8;margin:12px 0 0}
    h1,h2,h3{color:var(--admin-ink);font-weight:500;letter-spacing:-.025em}
    [data-testid="stMetric"]{background:white;color:var(--admin-ink);padding:24px;border:1px solid var(--admin-rule);border-radius:0}
    [data-testid="stMetricLabel"]{color:var(--admin-muted)}
    [data-testid="stMetricValue"]{color:var(--admin-ink);font-variant-numeric:tabular-nums;font-weight:500}
    [data-testid="stForm"]{padding:24px;border:1px solid var(--admin-rule);border-radius:0;background:white}
    [data-baseweb="tab-list"]{gap:24px;border-bottom:1px solid var(--admin-rule)}
    [data-baseweb="tab"]{min-height:52px;color:var(--admin-muted);padding-inline:4px}
    [data-baseweb="tab"][aria-selected="true"]{color:var(--admin-ink);font-weight:600}
    [data-baseweb="tab-highlight"]{background:var(--admin-bronze)}
    [data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{background:white;border-radius:0;border-color:var(--admin-rule)}
    .stButton button,.stLinkButton a,.stDownloadButton button,.stFormSubmitButton button{border-radius:0;min-height:44px;border-color:var(--admin-rule);color:var(--admin-ink)}
    button[kind="primary"],.stFormSubmitButton button{background:var(--admin-ink);color:var(--admin-paper);border-color:var(--admin-ink)}
    [data-testid="stAlert"]{border-radius:0}
    button:focus-visible,a:focus-visible{outline:2px solid var(--admin-bronze);outline-offset:3px}
    @media(max-width:600px){[data-testid="stMainBlockContainer"]{padding-top:2rem}.admin-brand{gap:16px;padding-block:16px}.admin-brand img{width:118px}.admin-brand-name{font-size:14px}.admin-brand-name span{font-size:12px}.admin-heading{padding:24px}.admin-heading h1{font-size:30px}[data-testid="stForm"]{padding:16px}[data-baseweb="tab-list"]{gap:12px}}
    .admin-logo{display:block;width:max-content;max-width:100%;padding:10px 0}
    .admin-logo img{height:128px;width:auto;max-width:100%;object-fit:contain}
    .admin-header-rule{height:1px;background:var(--admin-ink);margin:0 0 36px}
    .admin-heading{background:transparent;border:0;padding:12px 0 24px;margin:0}
    .admin-heading h1{color:var(--admin-ink);font-size:42px}
    .admin-heading p{color:var(--admin-muted);margin-top:12px}
    .login-heading{padding:0 0 22px}
    .login-heading h1{font-size:36px;line-height:1.5;margin:0 0 12px;padding:0}
    .login-heading p{color:var(--admin-muted);margin:0;font-size:16px}
    [data-testid="stForm"]:has(.login-heading){padding:36px;margin:16px 0 20px}
    [data-testid="stForm"]:has(.login-heading) input{min-height:48px}
    [data-baseweb="tab-list"]{gap:0;background:#edf1f5;padding:6px;border:1px solid var(--admin-rule);margin-block:24px}
    [data-baseweb="tab"]{flex:1;min-height:52px;padding:12px 20px;white-space:normal}
    [data-baseweb="tab"][aria-selected="true"]{background:var(--admin-ink);color:var(--admin-paper)}
    [data-baseweb="tab-highlight"]{display:none}
    ::selection{background:#dce4eb;color:var(--admin-ink)}
    @media(max-width:700px){.admin-logo img{height:90px}[data-testid="stForm"]:has(.login-heading){padding:24px}[data-testid="stHorizontalBlock"]:has(.login-heading){flex-wrap:wrap}[data-testid="stHorizontalBlock"]:has(.login-heading)>[data-testid="stColumn"]{min-width:100%;flex:1 1 100%}[data-baseweb="tab"]{font-size:14px;padding:10px 8px}.admin-heading h1{font-size:32px}}
    </style>''', unsafe_allow_html=True)
    body_font = 'IBM Plex Sans Arabic' if language == 'ar' else 'IBM Plex Sans'
    display_font = 'IBM Plex Sans Arabic' if language == 'ar' else 'Fraunces'
    direction = 'rtl' if language == 'ar' else 'ltr'
    st.markdown(f'''<style>
    .stApp,.stApp input,.stApp textarea,.stApp button,.stApp select,.stApp p,.stApp label{{font-family:"{body_font}",sans-serif}}
    [data-testid="stMainBlockContainer"]{{direction:{direction}}}
    .admin-heading h1,h1,h2,h3{{font-family:"{display_font}",serif}}
    </style>''', unsafe_allow_html=True)
    brand, actions = st.columns([4,2], vertical_alignment='center')
    with brand:
        st.markdown(f'<a class="admin-logo" href="/" target="_self"><img src="data:image/svg+xml;base64,{logo_data}" alt="Mohammed Al Sabaan — محمد منصور السبعان"></a>', unsafe_allow_html=True)
    with actions:
        selected = st.selectbox('اللغة / Language', ['ar','en'], index=0 if language == 'ar' else 1, format_func=lambda value: 'العربية' if value == 'ar' else 'English', key='admin_language_picker')
        if selected != language:
            st.query_params['admin_lang'] = selected
            st.rerun()
        st.link_button(tr('Return to website', 'العودة للموقع'), '/')
    st.markdown('<div class="admin-header-rule"></div>', unsafe_allow_html=True)
    if not password or len(password) < 12:
        st.info(tr('Set ADMIN_PASSWORD in Streamlit Secrets to a password of at least 12 characters. The dashboard stays locked until then.', 'أضف ADMIN_PASSWORD في إعدادات Streamlit Secrets بكلمة مرور لا تقل عن 12 حرفًا لتفعيل لوحة الإدارة.'))
        return
    if time.time() - st.session_state.get('admin_seen', 0) > 1800:
        st.session_state.pop('admin_authenticated', None)
    if not st.session_state.get('admin_authenticated'):
        _, login, _ = st.columns([1,1.4,1])
        with login:
            with st.form('admin_login'):
                st.markdown(f'<div class="login-heading"><h1>{tr("Welcome back", "مرحبًا بعودتك")}</h1><p>{tr("Sign in to your Admin panel", "سجّل الدخول إلى لوحة الإدارة")}</p></div>', unsafe_allow_html=True)
                entered = st.text_input(tr('Admin password', 'كلمة مرور الإدارة'), type='password')
                submit = st.form_submit_button(tr('Sign in', 'تسجيل الدخول'), use_container_width=True, type='primary')
                st.caption(tr('Your session locks after 30 minutes of inactivity.', 'تُقفل جلستك بعد 30 دقيقة من عدم النشاط.'))
        st.caption(tr('Password help: contact the website administrator to reset your access.', 'للمساعدة في كلمة المرور، تواصل مع مسؤول الموقع لإعادة تعيينها.'))
        if submit:
            if not store.login_allowed():
                st.error(tr('Too many unsuccessful attempts. Please wait 15 minutes.', 'محاولات غير ناجحة كثيرة. يرجى الانتظار 15 دقيقة.'))
            elif hmac.compare_digest(entered.encode(), password.encode()):
                store.login_succeeded()
                st.session_state.admin_authenticated = True
                st.session_state.admin_seen = time.time()
                st.rerun()
            else:
                store.login_failed()
                st.error(tr('Incorrect password', 'كلمة المرور غير صحيحة'))
        return
    st.session_state.admin_seen = time.time()
    st.markdown(f'<section class="admin-heading"><h1>{tr("Admin panel", "لوحة الإدارة")}</h1><p>{tr("Consultations, visitor insights and office settings", "الاستشارات وإحصاءات الزيارة وإعدادات المكتب")}</p></section>', unsafe_allow_html=True)
    with st.expander(tr('Storage information', 'معلومات التخزين')):
        st.warning(tr('Demo storage may reset after a restart or redeployment. Use test data only.', 'قد تُحذف البيانات التجريبية عند إعادة التشغيل أو النشر. استخدم بيانات اختبار فقط.'))
    a,b,c=st.columns([4,2,1])
    a.caption(tr('Signed in · session locks after 30 minutes of inactivity', 'تم تسجيل الدخول · تُقفل الجلسة بعد 30 دقيقة من عدم النشاط'))
    if c.button(tr('Sign out', 'تسجيل الخروج')):
        st.session_state.pop('admin_authenticated', None)
        st.session_state.pop('admin_seen', None)
        st.rerun()
    if b.button(tr('Refresh', 'تحديث')):
        st.rerun()
    metrics = store.metrics()
    cols = st.columns(3)
    for col,label,key in zip(cols,[tr('Received requests', 'الطلبات المستلمة'),tr('Open', 'المفتوحة'),tr('Closed', 'المغلقة')],['total','open','closed']):
        col.metric(label,metrics[key])
    requests_tab,analytics_tab,settings_tab = st.tabs([tr('Consultations', 'الاستشارات'),tr('Visitors', 'إحصاءات الزيارة'),tr('Office settings', 'إعدادات المكتب')])
    with requests_tab:
        st.caption(tr('Form submissions contain entered contact details. WhatsApp clicks record an enquiry handoff only; they do not confirm that a message was sent.', 'تحتوي طلبات الاستشارة على بيانات التواصل المُدخلة. تسجّل نقرات واتساب الانتقال للمحادثة فقط، ولا تؤكد إرسال رسالة.'))
        rows = store.requests()
        filter_col, search_col = st.columns([1,3])
        status = filter_col.selectbox(tr('Status filter', 'الحالة'), ['All','Open','Closed'], format_func=lambda v: tr(v, {'All':'الكل','Open':'مفتوحة','Closed':'مغلقة'}[v]))
        query = search_col.text_input(tr('Search name, phone, service or subject', 'ابحث بالاسم أو الجوال أو الخدمة أو الموضوع'), max_chars=100).strip().lower()
        shown = [r for r in rows if (status=='All' or r['status']==status.lower()) and (not query or query in ' '.join([r['name'],r['mobile'],r['service'],r['subject']]).lower())]
        if not shown:
            st.info(tr('No matching requests yet', 'لا توجد طلبات مطابقة'))
        else:
            table = pd.DataFrame(shown)[['id','created_at','name','mobile','service','source','status']]
            table['created_at'] = pd.to_datetime(table['created_at'], utc=True).dt.tz_convert('Asia/Riyadh').dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(table.rename(columns={'id':tr('ID','الرقم'),'created_at':tr('Received (Riyadh)','تاريخ الاستلام (الرياض)'),'name':tr('Name','الاسم'),'mobile':tr('Phone','الجوال'),'service':tr('Service','الخدمة'),'source':tr('Source','المصدر'),'status':tr('Status','الحالة')}),hide_index=True,use_container_width=True)
            lookup = {r['id']:r for r in shown}
            selected = st.selectbox(tr('Open a request', 'عرض الطلب'), list(lookup), format_func=lambda ident: f"{lookup[ident]['name'] or tr('WhatsApp enquiry','استفسار واتساب')} · {lookup[ident]['service'] or tr('General consultation','استشارة عامة')} · {ident[:8]}")
            row = lookup[selected]
            st.subheader(row['name'] or tr('WhatsApp enquiry', 'استفسار واتساب'))
            for label,key in [(tr('Service','الخدمة'),'service'),(tr('Subject','الموضوع'),'subject'),(tr('Phone','الجوال'),'mobile'),(tr('Email','البريد الإلكتروني'),'email'),(tr('Language','اللغة'),'language'),(tr('Source','المصدر'),'source')]:
                st.text(f"{label}: {row[key] or tr('Not provided', 'غير متوفر')}")
            st.text(row['details'] or tr('No additional details provided.', 'لا توجد تفاصيل إضافية.'))
            for item in store.attachments(selected):
                st.download_button(f"{tr('Download','تنزيل')}: {item['filename']}",item['content'],file_name=item['filename'],mime='application/octet-stream',key='attachment_'+item['id'])
            with st.form('edit_'+selected):
                new_status = st.radio(tr('Request status', 'حالة الطلب'),['open','closed'],index=0 if row['status']=='open' else 1,horizontal=True, format_func=lambda v: tr(v.title(), 'مفتوح' if v == 'open' else 'مغلق'))
                notes = st.text_area(tr('Internal notes (admin only)', 'ملاحظات داخلية للإدارة فقط'),value=row['notes'],max_chars=5000)
                if st.form_submit_button(tr('Save request', 'حفظ الطلب')):
                    store.update_request(selected,new_status,notes)
                    st.rerun()
    with analytics_tab:
        cols=st.columns(3)
        cols[0].metric(tr('Unique browsers', 'متصفحات فريدة'),metrics['visitors'])
        cols[1].metric(tr('Visits', 'الزيارات'),metrics['visits'])
        cols[2].metric(tr('Visits today (Riyadh)', 'زيارات اليوم (الرياض)'),metrics['today'])
        st.caption(tr('Only visitors who allow analytics are counted. Anonymous browser IDs; no IP addresses or browsing history are collected. A new tab counts as a visit. Clearing browser storage, private mode or another device can count the same person again. These are approximate visitor counts. Admin views are excluded.', 'تُحتسب زيارات الموافقين على الإحصاءات فقط، بمعرّفات متصفح مجهولة دون عناوين IP أو سجل تصفح. تُحتسب كل علامة تبويب جديدة زيارة، وقد يتكرر احتساب الشخص بعد مسح التخزين أو استخدام جهاز آخر. الأعداد تقريبية وتستثني زيارات الإدارة.'))
        if metrics['daily']:
            chart = pd.DataFrame(metrics['daily']).sort_values('day').set_index('day')
            st.bar_chart(chart,y='visits',color='#b68c66')
        else:
            st.info(tr('Visitor statistics will appear after the website is opened.', 'ستظهر الإحصاءات بعد زيارة الموقع والموافقة على الإحصاءات.'))
    with settings_tab:
        settings=store.settings(default_phone)
        st.caption(tr('Saved changes apply to new website loads. Refresh an already-open website to see the latest settings.', 'تُطبق التغييرات المحفوظة عند إعادة تحميل الموقع.'))
        with st.form('office_settings'):
            phone = st.text_input(tr('WhatsApp and contact number', 'رقم واتساب والتواصل'),value=settings['whatsapp'],max_chars=25,help=tr('Include country code, e.g. 966…', 'أدخل رمز الدولة مثل 966…'))
            ar,en=st.columns(2)
            address_ar=ar.text_input(tr('Address in Arabic','العنوان بالعربية'),value=settings['address_ar'],max_chars=300)
            address_en=en.text_input(tr('Address in English', 'العنوان بالإنجليزية'),value=settings['address_en'],max_chars=300)
            hours_ar=ar.text_input(tr('Working hours in Arabic','ساعات العمل بالعربية'),value=settings['hours_ar'],max_chars=300)
            hours_en=en.text_input(tr('Working hours in English', 'ساعات العمل بالإنجليزية'),value=settings['hours_en'],max_chars=300)
            lat=ar.number_input(tr('Latitude', 'خط العرض'),min_value=-90.0,max_value=90.0,value=float(settings['latitude']),format='%.7f')
            lng=en.number_input(tr('Longitude', 'خط الطول'),min_value=-180.0,max_value=180.0,value=float(settings['longitude']),format='%.7f')
            maps=st.text_input(tr('Google Maps directions link', 'رابط الاتجاهات في خرائط Google'),value=settings['maps_url'],max_chars=1000)
            if st.form_submit_button(tr('Save office settings', 'حفظ إعدادات المكتب')):
                try:
                    store.save_settings(dict(whatsapp=phone,address_ar=address_ar,address_en=address_en,hours_ar=hours_ar,hours_en=hours_en,latitude=lat,longitude=lng,maps_url=maps))
                    st.success(tr('Office settings saved', 'تم حفظ إعدادات المكتب'))
                except (ValueError,TypeError):
                    st.error(tr('Check the phone number, coordinates, text fields and HTTPS Google Maps link.', 'تحقق من رقم التواصل والإحداثيات والنصوص ورابط خرائط Google الآمن.'))
