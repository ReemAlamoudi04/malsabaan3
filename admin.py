"""Server-side password gate and admin-only dashboard."""
import hmac
import time
import pandas as pd
import streamlit as st


def show_admin(store, password, default_phone):
    st.markdown('''<style>
    .stApp{background:#f7f8fa;color:#183756}
    [data-testid="stHeader"]{background:#f7f8fa}
    [data-testid="stMainBlockContainer"]{max-width:1250px;padding-top:5rem}
    [data-testid="stMetric"]{background:#edf1f5;color:#183756;padding:24px;border:1px solid #d5dee7;border-top:3px solid #b68c66}
    [data-testid="stMetricLabel"]{color:#526577}
    h1,h2,h3{color:#183756}
    [data-testid="stMain"]{overflow-y:auto!important;overflow-x:hidden!important}
    [data-testid="stForm"]{border-color:#d5dee7}
    [data-testid="stTabs"] button[aria-selected="true"]{color:#183756}
    button[kind="primary"]{background:#b68c66;color:#183756;border-color:#b68c66}
    </style>''', unsafe_allow_html=True)
    st.caption('MOHAMMED AL SABAAN · OFFICE ADMINISTRATION')
    st.title('Office dashboard | لوحة الإدارة')
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
    a,b=st.columns([5,1])
    a.caption('Signed in · session locks after 30 minutes of inactivity')
    if b.button('Sign out'):
        st.session_state.pop('admin_authenticated', None)
        st.session_state.pop('admin_seen', None)
        st.rerun()
    if st.button('Refresh dashboard / تحديث'):
        st.rerun()
    metrics = store.metrics()
    cols = st.columns(3)
    for col,label,key in zip(cols,['Received requests / الطلبات المستلمة','Open / المفتوحة','Closed / المغلقة'],['total','open','closed']):
        col.metric(label,metrics[key])
    requests_tab,analytics_tab,settings_tab = st.tabs(['Consultations / الاستشارات','Visitors / الزيارات','Office settings / إعدادات المكتب'])
    with requests_tab:
        st.caption('Form submissions contain entered contact details. WhatsApp clicks record an enquiry handoff only; they do not confirm that a message was sent.')
        rows = store.requests()
        status = st.selectbox('Status filter', ['All','Open','Closed'])
        query = st.text_input('Search name, phone or service', max_chars=100).strip().lower()
        shown = [r for r in rows if (status=='All' or r['status']==status.lower()) and (not query or query in ' '.join([r['name'],r['mobile'],r['service']]).lower())]
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
            for label,key in [('Service','service'),('Phone','mobile'),('Email','email'),('Language','language'),('Source','source')]:
                st.text(f"{label}: {row[key] or 'Not provided'}")
            st.text(row['details'] or 'No additional details provided.')
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
        st.caption('Anonymous browser IDs; no IP addresses or browsing history are collected. A new tab counts as a visit. Clearing browser storage, private mode or another device can count the same person again. These are approximate visitor counts. Admin views are excluded.')
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
