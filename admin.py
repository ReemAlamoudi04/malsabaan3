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
    st.markdown('''<style>
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
    </style>''', unsafe_allow_html=True)
    st.markdown(f'''<header class="admin-brand">
      <img src="data:image/svg+xml;base64,{logo_data}" alt="Mohammed Al Sabaan law firm logo">
      <div class="admin-brand-name" lang="ar" dir="rtl">محمد منصور السبعان<span>للمحاماة والاستشارات القانونية والتوثيق</span></div>
    </header>
    <section class="admin-heading" aria-labelledby="admin-title">
      <h1 id="admin-title">Admin panel</h1>
      <p>Manage consultations, visitor insights and office settings.<br><span lang="ar" dir="rtl">إدارة الاستشارات وإحصاءات الزيارة وإعدادات المكتب</span></p>
    </section>''', unsafe_allow_html=True)
    st.warning('Demo storage: requests, visitor counts and settings may be erased by a Streamlit restart or redeployment. Use test data only.')
    st.link_button('← Return to website / العودة للموقع', '/')
    if not password or len(password) < 12:
        st.info('Set ADMIN_PASSWORD in Streamlit Secrets to a password of at least 12 characters. The dashboard stays locked until then.')
        return
    if time.time() - st.session_state.get('admin_seen', 0) > 1800:
        st.session_state.pop('admin_authenticated', None)
    if not st.session_state.get('admin_authenticated'):
        with st.form('admin_login'):
            entered = st.text_input('Admin password / كلمة مرور الإدارة', type='password')
            submit = st.form_submit_button('Sign in / تسجيل الدخول')
        if submit:
            if not store.login_allowed():
                st.error('Too many unsuccessful attempts. Please wait 15 minutes.')
            elif hmac.compare_digest(entered.encode(), password.encode()):
                store.login_succeeded()
                st.session_state.admin_authenticated = True
                st.session_state.admin_seen = time.time()
                st.rerun()
            else:
                store.login_failed()
                st.error('Incorrect password / كلمة المرور غير صحيحة')
        return
    st.session_state.admin_seen = time.time()
    a,b,c=st.columns([4,2,1])
    a.caption('Signed in · session locks after 30 minutes of inactivity')
    if c.button('Sign out / خروج'):
        st.session_state.pop('admin_authenticated', None)
        st.session_state.pop('admin_seen', None)
        st.rerun()
    if b.button('Refresh / تحديث'):
        st.rerun()
    metrics = store.metrics()
    cols = st.columns(3)
    for col,label,key in zip(cols,['Received requests / الطلبات المستلمة','Open / المفتوحة','Closed / المغلقة'],['total','open','closed']):
        col.metric(label,metrics[key])
    requests_tab,analytics_tab,settings_tab = st.tabs(['Consultations / الاستشارات','Visitors / الزيارات','Office settings / إعدادات المكتب'])
    with requests_tab:
        st.caption('Form submissions contain entered contact details. WhatsApp clicks record an enquiry handoff only; they do not confirm that a message was sent.')
        rows = store.requests()
        filter_col, search_col = st.columns([1,3])
        status = filter_col.selectbox('Status filter / الحالة', ['All','Open','Closed'])
        query = search_col.text_input('Search name, phone, service or subject / بحث', max_chars=100).strip().lower()
        shown = [r for r in rows if (status=='All' or r['status']==status.lower()) and (not query or query in ' '.join([r['name'],r['mobile'],r['service'],r['subject']]).lower())]
        if not shown:
            st.info('No matching requests yet / لا توجد طلبات مطابقة')
        else:
            table = pd.DataFrame(shown)[['id','created_at','name','mobile','service','source','status']]
            table['created_at'] = pd.to_datetime(table['created_at'], utc=True).dt.tz_convert('Asia/Riyadh').dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(table.rename(columns={'created_at':'Received (Riyadh)'}),hide_index=True,use_container_width=True)
            lookup = {r['id']:r for r in shown}
            selected = st.selectbox('Open a request', list(lookup), format_func=lambda ident: f"{lookup[ident]['name'] or 'WhatsApp enquiry'} · {lookup[ident]['service'] or 'General consultation'} · {ident[:8]}")
            row = lookup[selected]
            st.subheader(row['name'] or 'WhatsApp enquiry / استفسار واتساب')
            for label,key in [('Service','service'),('Subject','subject'),('Phone','mobile'),('Email','email'),('Language','language'),('Source','source')]:
                st.text(f"{label}: {row[key] or 'Not provided'}")
            st.text(row['details'] or 'No additional details provided.')
            for item in store.attachments(selected):
                st.download_button(f"Download / تنزيل: {item['filename']}",item['content'],file_name=item['filename'],mime='application/octet-stream',key='attachment_'+item['id'])
            with st.form('edit_'+selected):
                new_status = st.radio('Request status',['open','closed'],index=0 if row['status']=='open' else 1,horizontal=True)
                notes = st.text_area('Internal notes (admin only)',value=row['notes'],max_chars=5000)
                if st.form_submit_button('Save request / حفظ الطلب'):
                    store.update_request(selected,new_status,notes)
                    st.rerun()
    with analytics_tab:
        cols=st.columns(3)
        cols[0].metric('Unique browsers / متصفحات فريدة',metrics['visitors'])
        cols[1].metric('Visits / الزيارات',metrics['visits'])
        cols[2].metric('Visits today (Riyadh)',metrics['today'])
        st.caption('Only visitors who allow analytics are counted. Anonymous browser IDs; no IP addresses or browsing history are collected. A new tab counts as a visit. Clearing browser storage, private mode or another device can count the same person again. These are approximate visitor counts. Admin views are excluded.')
        if metrics['daily']:
            chart = pd.DataFrame(metrics['daily']).sort_values('day').set_index('day')
            st.bar_chart(chart,y='visits',color='#b68c66')
        else:
            st.info('Visitor statistics will appear after the website is opened.')
    with settings_tab:
        settings=store.settings(default_phone)
        st.caption('Saved changes apply to new website loads. Refresh an already-open website to see the latest settings.')
        with st.form('office_settings'):
            phone = st.text_input('WhatsApp and contact number',value=settings['whatsapp'],max_chars=25,help='Include country code, e.g. 966…')
            ar,en=st.columns(2)
            address_ar=ar.text_input('العنوان بالعربية',value=settings['address_ar'],max_chars=300)
            address_en=en.text_input('Address in English',value=settings['address_en'],max_chars=300)
            hours_ar=ar.text_input('ساعات العمل بالعربية',value=settings['hours_ar'],max_chars=300)
            hours_en=en.text_input('Working hours in English',value=settings['hours_en'],max_chars=300)
            lat=ar.number_input('Latitude',min_value=-90.0,max_value=90.0,value=float(settings['latitude']),format='%.7f')
            lng=en.number_input('Longitude',min_value=-180.0,max_value=180.0,value=float(settings['longitude']),format='%.7f')
            maps=st.text_input('Google Maps directions link',value=settings['maps_url'],max_chars=1000)
            if st.form_submit_button('Save office settings / حفظ الإعدادات'):
                try:
                    store.save_settings(dict(whatsapp=phone,address_ar=address_ar,address_en=address_en,hours_ar=hours_ar,hours_en=hours_en,latitude=lat,longitude=lng,maps_url=maps))
                    st.success('Office settings saved / تم حفظ الإعدادات')
                except (ValueError,TypeError):
                    st.error('Check the phone number, coordinates, text fields and HTTPS Google Maps link.')
